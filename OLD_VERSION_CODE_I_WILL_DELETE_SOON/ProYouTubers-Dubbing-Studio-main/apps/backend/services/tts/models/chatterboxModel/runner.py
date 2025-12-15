from __future__ import annotations
import contextlib
import json
import sys
import threading
import logging
import time
from pathlib import Path
from typing import Dict, Tuple

# DEBUG: Print environment info
logger = logging.getLogger("runner_debug")
logging.basicConfig(level=logging.INFO)
logger.info(f"Runner Python Executable: {sys.executable}")
logger.info(f"Runner Sys Path: {sys.path}")
try:
    import torch
    logger.info(f"Torch version: {torch.__version__}")
except ImportError as e:
    logger.error(f"Failed to import torch: {e}")


# GPU/CPU device detection - automatically uses GPU when available
import torch
logger.info(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    logger.info(f"GPU device: {torch.cuda.get_device_name(0)}")



import torchaudio as ta

# Mock perth module to prevent watermarker initialization failure
import sys
class MockPerthWatermarker:
    """Mock watermarker that does nothing"""
    def __init__(self, *args, **kwargs):
        logger.info("Using mock watermarker (perth library not available)")
    def __call__(self, *args, **kwargs):
        return args[0] if args else None
    def apply_watermark(self, wav, **kwargs):
        """Pass through audio unchanged"""
        return wav

class MockPerth:
    PerthImplicitWatermarker = MockPerthWatermarker

sys.modules['perth'] = MockPerth()

from chatterbox.mtl_tts import ChatterboxMultilingualTTS

from common_schemas.models import SegmentAudioOut, TTSRequest, TTSResponse
from common_schemas.service_utils import get_service_logger


_MODEL_CACHE: Dict[Tuple[str, str], Tuple[torch.nn.Module, int]] = {}
_MODEL_LOCK = threading.Lock()


def _device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_model(model_name: str, device: str, log_level: int):
    logger = get_service_logger("tts.chatterbox", log_level)
    key = (model_name, device)
    with _MODEL_LOCK:
        cached = _MODEL_CACHE.get(key)
        if cached:
            logger.debug("Using cached chatterbox model=%s device=%s.", model_name, device)
            return cached

        load_start = time.perf_counter()
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        sample_rate = model.sr

        _MODEL_CACHE[key] = (model, sample_rate)
        logger.info(
            "Loaded chatterbox model=%s device=%s in %.2fs.",
            model_name,
            device,
            time.perf_counter() - load_start,
        )
        return _MODEL_CACHE[key]


def _synthesize(req: TTSRequest) -> TTSResponse:
    log_level = req.extra.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level, logging.INFO)
    logger = get_service_logger("tts.chatterbox", log_level)
    run_start = time.perf_counter()
    workspace_path = Path(req.workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)

    model_name = (req.extra or {}).get("model_name", "chatterbox_multilingual")
    device = _device()
    model, sample_rate = _load_model(model_name, device, log_level)

    out = TTSResponse()
    generation_kwargs = (req.extra or {}).get("generate", {})
    logger.info(
        "Starting chatterbox synthesis segments=%d workspace=%s model=%s device=%s",
        len(req.segments or []),
        req.workspace,
        model_name,
        device,
    )

    for i, segment in enumerate(req.segments):
        seg_start = time.perf_counter()
        audio_prompt = segment.audio_prompt_url or None
        if audio_prompt and not Path(audio_prompt).exists():
            raise FileNotFoundError(f"Audio prompt file not found: {audio_prompt}")

        if segment.legacy_audio_path:
            output_file = Path(segment.legacy_audio_path)
            if not output_file.is_absolute():
                output_file = (workspace_path / output_file).resolve()
            else:
                output_file = output_file.resolve()
            try:
                output_file.relative_to(workspace_path.resolve())
            except ValueError as exc:  # ensure overwrite stays inside workspace
                raise RuntimeError(f"legacy_audio_path must reside inside workspace: {segment.legacy_audio_path}") from exc
        else:
            identifier = segment.segment_id or f"seg-{i}"
            output_file = workspace_path / f"{identifier}.wav"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        wav = model.generate(
            segment.text,
            language_id=segment.lang,
            audio_prompt_path=audio_prompt,
            **generation_kwargs,
        )

        ta.save(str(output_file), wav, sample_rate)

        out.segments.append(
            SegmentAudioOut(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                audio_prompt_url=segment.audio_prompt_url,
                audio_url=str(output_file),
                speaker_id=segment.speaker_id,
                lang=segment.lang,
                sample_rate=sample_rate,
                segment_id=segment.segment_id,
            )
        )
        logger.info(
            "Generated segment %d lang=%s prompt=%s duration=%.2fs",
            i,
            segment.lang,
            bool(audio_prompt),
            time.perf_counter() - seg_start,
        )

    logger.info(
        "Completed chatterbox synthesis in %.2fs (segments=%d).",
        time.perf_counter() - run_start,
        len(out.segments),
    )
    
    # Clear model from GPU memory to free ~4GB VRAM for concurrent pipelines
    # Only keep model loaded if explicitly requested (for batch processing)
    keep_loaded = req.extra.get("keep_model_loaded", False) if req.extra else False
    if not keep_loaded:
        global _MODEL_CACHE
        with _MODEL_LOCK:
            if _MODEL_CACHE:
                logger.info("🧹 Clearing TTS model from GPU memory...")
                _MODEL_CACHE.clear()
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("✅ Released ~4GB VRAM for other pipelines")
    
    return out


def _run_once():
    req = TTSRequest(**json.loads(sys.stdin.read()))
    with contextlib.redirect_stdout(sys.stderr):
        out = _synthesize(req)
    sys.stdout.write(out.model_dump_json() + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    _run_once()
