import os
import logging
import soundfile as sf
import time
import torch
# Assuming kokoro-onnx or similar wrapper
# If not, we might need to implement the ONNX session directly
try:
    from kokoro_onnx import Kokoro
except ImportError:
    Kokoro = None

logger = logging.getLogger(__name__)

class KokoroRunner:
    """
    Stage 7: The Mouth (Draft Mode - Kokoro-82M)
    Ultra-fast TTS for instant previews.
    """
    def __init__(self, model_path: str = "kokoro-v0_19.onnx", voices_path: str = "voices.json"):
        self.model_path = model_path
        self.voices_path = voices_path
        self.kokoro = None

    def load(self):
        if self.kokoro: return
        
        logger.info("🏎️ Loading Kokoro (Speed Mode)...")
        try:
            self.kokoro = Kokoro(self.model_path, self.voices_path)
            logger.info("✅ Kokoro Loaded.")
        except Exception as e:
            logger.error(f"Failed to load Kokoro: {e}")
            # Do not raise immediately if just init, rely on generate to fail
            pass

    def generate(self, text: str, voice: str = "af_sarah", output_file: str = "draft_out.wav") -> str:
        if not self.kokoro:
            self.load()
            
        start = time.time()
        # Kokoro generation
        # NOTE: Verify exact API of kokoro-onnx 
        try:
            audio, sample_rate = self.kokoro.create(text, voice=voice, speed=1.0, lang="en-us")
            sf.write(output_file, audio, sample_rate)
            
            dur = time.time() - start
            logger.info(f"⚡ Kokoro generated {len(text)} chars in {dur:.2f}s")
            return output_file
        except Exception as e:
            logger.error(f"Kokoro Generation Failed: {e}")
            raise

    def unload(self):
        # ONNX runtime doesn't hog VRAM like PyTorch, but good practice
        if self.kokoro:
            del self.kokoro
            self.kokoro = None
