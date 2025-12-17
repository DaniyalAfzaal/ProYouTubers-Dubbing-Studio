import os
import logging
import torch
import soundfile as sf
import numpy as np
# Assuming we can import F5-TTS components. 
# If not installed as a package, we might need sys.path hacks or a specific sub-process wrapper.
# For now, drafting the class structure.
try:
    from f5_tts.model import DiT
    from f5_tts.infer.utils_infer import load_model, load_vocoder, infer_process
except ImportError:
    # Fallback/Placeholder if not installed yet
    DiT = None
    pass

logger = logging.getLogger(__name__)

class F5TTSRunner:
    """
    Stage 7: The Mouth (Production)
    Wraps F5-TTS for high-fidelity, flow-matched speech synthesis.
    """
    def __init__(self, model_path: str = "SWivid/F5-TTS", device: str = "cuda"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.vocoder = None
        self.processor = None

    def load(self):
        """Loads F5-TTS model into VRAM."""
        if self.model: 
            return # Already loaded

        logger.info(f"👄 Loading F5-TTS from {self.model_path}...")
        
        # NOTE: This implementation depends on the exact F5-TTS API
        # This is a generalized implementation based on common patterns in that repo
        try:
            self.model, self.processor = load_model(self.model_path, device=self.device)
            self.vocoder = load_vocoder(is_local=False) # Loads BigVGAN or equivalent default
            logger.info("✅ F5-TTS Loaded.")
        except Exception as e:
            logger.error(f"Failed to load F5-TTS: {e}")
            raise

    def generate(
        self, 
        text: str, 
        ref_audio: str, 
        ref_text: str = "",
        output_file: str = "output.wav",
        speed: float = 1.0
    ) -> str:
        """
        Generates speech using F5-TTS.
        """
        if not self.model:
            self.load()

        logger.info(f"🗣️ F5-TTS Generating: '{text[:20]}...'")
        
        try:
            # Main inference call
            audio, sample_rate, _ = infer_process(
                ref_audio, 
                ref_text, 
                text, 
                self.model, 
                self.vocoder, 
                self.processor,
                device=self.device,
                speed=speed
            )
            
            # Save to file
            sf.write(output_file, audio, sample_rate)
            return output_file
            
        except Exception as e:
            logger.error(f"F5 Inference Error: {e}")
            raise

    def unload(self):
        """Unloader for Sequential Pipeline."""
        if self.model:
            logger.info("🧹 Unloading F5-TTS...")
            del self.model
            del self.vocoder
            del self.processor
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
