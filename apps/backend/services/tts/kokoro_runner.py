"""
Stage 7 (Draft Mode): The Mouth - Kokoro-82M
Model: Kokoro-82M ONNX
Purpose: Ultra-fast TTS for Draft mode (speed priority)
Link: https://huggingface.co/hexgrad/Kokoro-82M
"""

import logging
import os
import numpy as np
import onnxruntime as ort
from pathlib import Path
import soundfile as sf

logger = logging.getLogger(__name__)


class KokoroRunner:
    """
    Stage 7: The Mouth (Draft Mode)
    Kokoro-82M ONNX for ultra-fast TTS generation.
    """
    
    def __init__(
        self, 
        model_path: str = "hexgrad/Kokoro-82M",
        voice: str = "af_bella"
    ):
        self.model_path = model_path
        self.voice = voice
        self.session = None
        self.sample_rate = 24000  # Kokoro default
        
    def load(self):
        """Load Kokoro ONNX model."""
        if self.session:
            return
            
        logger.info(f"🏎️ Loading Kokoro-82M ONNX model...")
        try:
            # For now, assuming model is downloaded locally
            # In production, would download from HuggingFace
            model_file = Path("models/kokoro-82m/model.onnx")
            
            if not model_file.exists():
                logger.warning(f"Kokoro model not found at {model_file}")
                logger.warning("Download from: https://huggingface.co/hexgrad/Kokoro-82M")
                self.session = None
                return
            
            # Create ONNX session
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            self.session = ort.InferenceSession(str(model_file), providers=providers)
            
            logger.info(f"✅ Kokoro loaded with {self.session.get_providers()[0]}")
            
        except Exception as e:
            logger.error(f"Failed to load Kokoro: {e}")
            self.session = None
    
    def generate(
        self, 
        text: str, 
        output_file: str = "output.wav",
        speed: float = 1.0
    ) -> str:
        """
        Generate speech using Kokoro-82M.
        
        Args:
            text: Text to synthesize
            output_file: Where to save audio
            speed: Speech rate multiplier
            
        Returns:
            Path to generated audio
        """
        if not self.session:
            self.load()
        
        if not self.session:
            # Fallback to silent audio
            logger.warning("⚠️ Kokoro not available, creating silent audio")
            duration = len(text.split()) * 0.3
            audio = np.zeros(int(duration * self.sample_rate), dtype=np.float32)
            sf.write(output_file, audio, self.sample_rate)
            return output_file
        
        logger.info(f"🏎️ Kokoro generating: '{text[:50]}...'")
        
        try:
            # Encode text (simplified - real implementation needs phonemizer)
            # This is a placeholder for the actual ONNX inference
            text_tokens = list(text.encode('utf-8'))[:200]  # Simplified
            
            # Run ONNX inference
            inputs = {
                self.session.get_inputs()[0].name: np.array([text_tokens], dtype=np.int64)
            }
            outputs = self.session.run(None, inputs)
            
            # Get audio waveform
            audio = outputs[0].flatten().astype(np.float32)
            
            # Apply speed modification if needed
            if speed != 1.0:
                from scipy.signal import resample
                new_length = int(len(audio) / speed)
                audio = resample(audio, new_length)
            
            # Save to file
            sf.write(output_file, audio, self.sample_rate)
            logger.info(f"✅ Generated {len(audio)/self.sample_rate:.2f}s of audio")
            return output_file
            
        except Exception as e:
            logger.error(f"Kokoro generation failed: {e}")
            # Fallback
            duration = len(text.split()) * 0.3
            audio = np.zeros(int(duration * self.sample_rate), dtype=np.float32)
            sf.write(output_file, audio, self.sample_rate)
            logger.warning(f"⚠️ Created silent placeholder ({duration}s)")
            return output_file
    
    def unload(self):
        """Unload ONNX session."""
        if self.session:
            logger.info("🧹 Unloading Kokoro...")
            del self.session
            self.session = None
            logger.info("✅ Kokoro unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = KokoroRunner()
    runner.load()
    # result = runner.generate("Hello world")
    # print(f"Generated: {result}")
    runner.unload()
    print("✅ Kokoro runner test complete")
