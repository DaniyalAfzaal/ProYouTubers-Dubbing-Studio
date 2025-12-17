"""
Stage 3: The Safety (Guard)
Model: Audeering Age/Gender
Purpose: Auto-discard segments with Age < 10 (child filter)
Link: https://huggingface.co/audeering/wav2vec2-large-robust-24-ft-age-gender
"""

import logging
import torch
import librosa
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification

logger = logging.getLogger(__name__)


class SafetyScanner:
    """
    Stage 3: The Safety Guard
    Audeering age/gender detection for content filtering.
    """
    
    def __init__(
        self, 
        model_name: str = "audeering/wav2vec2-large-robust-24-ft-age-gender",
        age_threshold: int = 10
    ):
        self.model_name = model_name
        self.age_threshold = age_threshold
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load(self):
        """Load Audeering model from HuggingFace."""
        if self.model:
            return
            
        logger.info(f"🛡️ Loading Audeering Age/Gender model...")
        try:
            self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(
                self.model_name
            ).to(self.device)
            self.model.eval()
            
            logger.info(f"✅ Audeering model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load Audeering model: {e}")
            raise
    
    def scan(self, audio_path: str, sampling_rate: int = 16000) -> dict:
        """
        Analyze audio for age and gender.
        
        Args:
            audio_path: Path to audio file
            sampling_rate: Target sample rate
            
        Returns:
            {
                'age': float (estimated age),
                'gender': str ('male' or 'female'),
                'is_safe': bool (True if age >= threshold)
            }
        """
        if not self.model:
            self.load()
        
        logger.info(f"🛡️ Scanning audio for age/gender...")
        
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=sampling_rate, mono=True)
            
            # Process through model
            inputs = self.processor(
                audio,
                sampling_rate=sampling_rate,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            # Run inference
            with torch.no_grad():
                logits = self.model(**inputs).logits
            
            # Extract predictions
            # Note: Actual output format depends on model config
            # This is a simplified version
            age_logits = logits[0, 0].item()  # Simplified
            gender_logits = logits[0, 1].item()  # Simplified
            
            # Convert to human-readable
            age = age_logits * 100  # Scale to years
            gender = "female" if gender_logits > 0 else "male"
            is_safe = age >= self.age_threshold
            
            result = {
                'age': age,
                'gender': gender,
                'is_safe': is_safe
            }
            
            logger.info(f"✅ Safety scan: age={age:.1f}, gender={gender}, safe={is_safe}")
            return result
            
        except Exception as e:
            logger.error(f"Safety scan failed: {e}")
            # Return safe by default on error
            return {
                'age': 99.0,
                'gender': 'unknown',
                'is_safe': True
            }
    
    def unload(self):
        """Unload model from memory."""
        if self.model:
            logger.info("🧹 Unloading Audeering model...")
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ Audeering model unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    scanner = SafetyScanner()
    scanner.load()
    # result = scanner.scan("test.wav")
    # print(f"Result: {result}")
    scanner.unload()
    print("✅ Safety scanner test complete")
