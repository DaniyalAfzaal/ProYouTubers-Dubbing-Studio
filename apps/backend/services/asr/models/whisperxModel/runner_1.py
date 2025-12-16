import contextlib
import gc
import json
import logging
import os
import sys
import time

import torch
import whisperx
from dotenv import load_dotenv
from whisperx.diarize import DiarizationPipeline

from common_schemas.models import ASRResponse, Segment, Word
from common_schemas.utils import convert_whisperx_result_to_Segment, create_word_segments


def _clear_cuda_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    try:
        req = ASRResponse(**json.loads(sys.stdin.read()))
        extra = dict(req.extra or {})
        log_level = extra.get("log_level", "INFO").upper()
        log_level = getattr(logging, log_level, logging.INFO)

        logger = logging.getLogger("whisperx.runner.align")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(handler)
        logger.setLevel(log_level)
        logger.propagate = False

        with contextlib.redirect_stdout(sys.stderr):
            if not req.audio_url:
                raise ValueError("audio_url is required for alignment.")
            if not req.language:
                raise ValueError("language is required for alignment.")

            req_dict = req.model_dump()
            load_dotenv()
            diarize_enabled = bool(extra.get("enable_diarization", True))
            diarization_model_name = extra.get("diarization_model")
            min_speakers = extra.get("min_speakers")
            max_speakers = extra.get("max_speakers")

            device = extra.get("device") or os.getenv("WHISPERX_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
            
            # FIX: Properly initialize CUDA in subprocess with explicit device selection
            if device == "cuda" and torch.cuda.is_available():
                try:
                    # Initialize CUDA context and set device 0
                    torch.cuda.init()
                    torch.cuda.set_device(0)
                    # Test tensor to ensure CUDA works
                    _ = torch.zeros(1).cuda()
                    gpu_name = torch.cuda.get_device_name(0)
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                    logger.info(f"✅ CUDA initialized: {gpu_name} ({gpu_memory:.1f}GB)")
                except (RuntimeError, AssertionError) as e:
                    logger.warning(f"⚠️ CUDA initialization failed: {e}. Falling back to CPU")
                    device = "cpu"
            
            if device == "cpu":
                logger.warning("⚠️ Running alignment on CPU - timestamps may be less accurate")


            logger.info(
                "Starting alignment for audio=%s language=%s diarize=%s min_speakers=%s max_speakers=%s",
                req.audio_url,
                req.language,
                diarize_enabled,
                min_speakers,
                max_speakers,
            )

            audio = whisperx.load_audio(req.audio_url)

            # Clear GPU cache before loading alignment model
            if device == "cuda":
                _clear_cuda_cache()
                logger.info(f"GPU memory before alignment: {torch.cuda.memory_allocated()/1024**2:.1f}MB")
            
            align_start = time.perf_counter()
            try:
                model_a, metadata = whisperx.load_align_model(
                    language_code=req.language,
                    device=device,
                )
                logger.info(f"✅ Alignment model loaded on {device}")
            except RuntimeError as e:
                if "CUDA" in str(e) and device == "cuda":
                    logger.warning(f"❌ Failed to load alignment model on CUDA: {e}. Retrying on CPU...")
                    device = "cpu"
                    model_a, metadata = whisperx.load_align_model(
                        language_code=req.language,
                        device=device,
                    )
                    logger.info(f"✅ Alignment model loaded on CPU (fallback)")
                else:
                    raise
            logger.info("Loaded alignment model in %.2fs.", time.perf_counter() - align_start)

            # ============================================================
            # SILERO VAD VERIFICATION (Alignment Quality Check)
            # ============================================================
            # Run Silero VAD for comparison with ASR-detected timestamps.
            # This helps verify if Silero provides better timestamping than
            # the original Pyannote VAD used during transcription.
            # ============================================================
            try:
                from .vad_utils import detect_speech_segments
                
                logger.info("🔍 Running Silero VAD for timestamp quality verification...")
                
                vad_verification_segments = detect_speech_segments(
                    audio,
                    sampling_rate=16000,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=100,
                    speech_pad_ms=30
                )
                
                if vad_verification_segments and req_dict.get("segments"):
                    logger.info("📊 VAD Quality Comparison:")
                    logger.info(f"   Silero detected:  {len(vad_verification_segments)} segments")
                    logger.info(f"   ASR detected:     {len(req_dict['segments'])} segments")
                    
                    if vad_verification_segments and req_dict["segments"]:
                        silero_first = vad_verification_segments[0]
                        asr_first = req_dict["segments"][0]
                        timestamp_diff = asr_first['start'] - silero_first['start']
                        
                        logger.info(f"   Silero 1st start: {silero_first['start']:.2f}s")
                        logger.info(f"   ASR 1st start:    {asr_first['start']:.2f}s")
                        logger.info(f"   Difference:       {timestamp_diff:+.2f}s")
                        
                        if abs(timestamp_diff) > 0.3:
                            logger.warning(
                                f"⚠️  Large timestamp difference detected ({timestamp_diff:+.2f}s). "
                                f"Consider using Silero VAD in runner_0.py for better accuracy."
                            )
                        else:
                            logger.info("✅ Timestamps aligned well between Silero and ASR")
                            
            except ImportError:
                logger.debug("Silero VAD not available for verification, skipping")
            except Exception as e:
                logger.warning(f"Silero VAD verification failed: {e}")
            
            # ============================================================
            # Alignment (Uses ASR Segments)
            # ============================================================
            
            align_compute_start = time.perf_counter()
            result = whisperx.align(
                req_dict["segments"],
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False
            )
            logger.info("Alignment completed in %.2fs.", time.perf_counter() - align_compute_start)
            
            # DIAGNOSTIC: Log segment timing for verification
            logger.info("📊 Alignment Quality Check:")
            aligned_segments = result.get("segments", [])
            for i, seg in enumerate(aligned_segments[:5]):  # Log first 5 segments
                duration = seg['end'] - seg['start']
                text_preview = seg.get('text', '')[:60]
                logger.info(f"   Segment {i}: [{seg['start']:.2f}-{seg['end']:.2f}s] dur={duration:.2f}s")
                logger.info(f"      Text: '{text_preview}...'")
            if len(aligned_segments) > 5:
                logger.info(f"   ... and {len(aligned_segments) - 5} more segments")

            diarize_segments = None
            if diarize_enabled and diarization_model_name:
                hf_token = os.getenv("HF_TOKEN")
                diarize_start = time.perf_counter()
                diarize_model = DiarizationPipeline(
                    model_name=diarization_model_name,
                    use_auth_token=hf_token,
                    device=device,
                )
                diarize_segments = diarize_model(
                    audio,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers,
                )
                logger.info(
                    "Diarization produced %d segments in %.2fs.",
                    len(diarize_segments),
                    time.perf_counter() - diarize_start,
                )
                del diarize_model
                _clear_cuda_cache()
            elif diarize_enabled:
                logger.info("Diarization requested but no model configured; skipping speaker attribution.")
            else:
                logger.info("Diarization disabled for this run; skipping speaker attribution.")

            if diarize_segments is not None:
                result = whisperx.assign_word_speakers(diarize_segments, result)

            segments_out: list[Segment] = convert_whisperx_result_to_Segment(result)
            word_segments_out: list[Word] = create_word_segments(result, segments_out)

            out = ASRResponse(
                segments=segments_out,
                WordSegments=word_segments_out or None,
                language=req.language,
                audio_url=req.audio_url,
                extra=extra,
            )

            # Clean up GPU memory
            del audio
            del model_a
            gc.collect()
            if device == "cuda" and torch.cuda.is_available():
                _clear_cuda_cache()
                logger.info(f"GPU memory after cleanup: {torch.cuda.memory_allocated()/1024**2:.1f}MB")

        sys.stdout.write(json.dumps(out.model_dump(), indent=2) + "\n")
        sys.stdout.flush()

    except Exception as exc:
        logger.exception("Unhandled exception in WhisperX runner")
        error_data = {"error": str(exc), "type": type(exc).__name__}
        sys.stderr.write(f"❌ ASR Runner Error: {json.dumps(error_data, indent=2)}\n")
        sys.exit(1)
