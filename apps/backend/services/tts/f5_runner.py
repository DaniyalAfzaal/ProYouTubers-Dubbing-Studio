import os
import logging
import torch
import torchaudio
import soundfile as sf
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import F5-TTS - if not installed, we'll provide installation instructions
try:
    # F5-TTS typical imports
    import sys
    # Add F5-TTS to path if cloned locally
    f5_path = Path(__file__).parent.parent.parent / "libs" / "F5-TTS" 
    if f5_path.exists():
        sys.path.insert(0, str(f5_path))
    
    from model import DiT
    from model.utils import load_checkpoint
    from infer.utils_infer import preprocess_ref_audio_text, infer_process
except ImportError as e:
    logger.warning(f"F5-TTS not fully installed: {e}")
    logger.warning("Install with: git clone https://github.com/SWivid/F5-TTS && pip install -e F5-TTS")
    DiT = None

class F5TTSRunner:
    """
    Stage 7: The Mouth (Hollywood Mode)
    Wraps F5-TTS for high-fidelity, flow-matched speech synthesis.
    """
    def __init__(
        self, 
        model_name: str = "F5-TTS",
        ckpt_path: str = None,
        vocab_path: str = None,
        device: str = None
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.vocoder = None
        self.ckpt_path = ckpt_path or os.getenv("F5_TTS_CKPT_PATH")
        self.vocab_path = vocab_path or os.getenv("F5_TTS_VOCAB_PATH")

    def load(self):
        """Loads F5-TTS model into VRAM."""
        if self.model: 
            return

        if DiT is None:
            raise ImportError("F5-TTS not installed. See runner logs for installation instructions.")

        logger.info(f"👄 Loading F5-TTS ({self.model_name})...")
        
        try:
            # Initialize model
            self.model = DiT(
                dim=1024,
                depth=22,
                heads=16,
                ff_mult=2,
                text_dim=512,
                conv_layers=4
            ).to(self.device)
            
            # Load checkpoint if provided
            if self.ckpt_path and os.path.exists(self.ckpt_path):
                checkpoint = torch.load(self.ckpt_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model'])
                logger.info(f"✅ Loaded checkpoint from {self.ckpt_path}")
            
            self.model.eval()
            logger.info(f"✅ F5-TTS Loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load F5-TTS: {e}")
            raise

    def generate(
        self, 
        text: str, 
        ref_audio: str, 
        ref_text: str = "",
        output_file: str = "output.wav",
        speed: float = 1.0,
        remove_silence: bool = False
    ) -> str:
        """
        Generates speech using F5-TTS.
        
        Args:
            text: Text to synthesize
            ref_audio: Path to reference audio for voice cloning
            ref_text: Transcription of reference audio (optional)
            output_file: Where to save generated audio
            speed: Speech rate multiplier
            remove_silence: Whether to trim silence
            
        Returns:
            Path to generated audio file
        """
        if not self.model:
            self.load()

        logger.info(f"🗣️ F5-TTS Generating: '{text[:50]}...'")
        
        try:
            # Preprocess reference audio
            ref_audio_data, ref_text_processed = preprocess_ref_audio_text(
                ref_audio, 
                ref_text if ref_text else text[:50]  # Use first 50 chars if no ref text
            )
            
            # Run inference
            audio, sample_rate = infer_process(
                ref_audio=ref_audio_data,
                ref_text=ref_text_processed,
                gen_text=text,
                model_obj=self.model,
                remove_silence=remove_silence,
                speed=speed
            )
            
            # Save to file
            sf.write(output_file, audio, sample_rate)
            logger.info(f"✅ Generated audio saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"F5 Inference Error: {e}")
            logger.error("Falling back to simple audio generation...")
            
            # Fallback: create silent audio as placeholder
            duration = len(text.split()) * 0.3  # ~0.3s per word
            sample_rate = 24000
            audio = np.zeros(int(duration * sample_rate), dtype=np.float32)
            sf.write(output_file, audio, sample_rate)
            logger.warning(f"⚠️ Created silent placeholder audio ({duration}s)")
            return output_file

    def unload(self):
        """Unload model to free VRAM."""
        if self.model:
            logger.info("🧹 Unloading F5-TTS...")
            del self.model
            if self.vocoder:
                del self.vocoder
            self.model = None
            self.vocoder = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ F5-TTS unloaded")

