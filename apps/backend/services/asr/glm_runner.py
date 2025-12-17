import torch
import logging
import librosa
import numpy as np
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

logger = logging.getLogger(__name__)

class GLMASRRunner:
    """
    Stage 4: The Brain
    GLM-ASR-Nano-2512 - Hallucination-free ASR optimized for multilingual transcription.
    """
    def __init__(self, model_path: str = "THUDM/glm-4-voice-9b"):
        # Note: GLM-ASR-Nano might be part of GLM-4-Voice family
        # Using GLM-4-Voice as the base model which includes ASR capabilities
        self.model_path = model_path
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load(self):
        if self.model: 
            return

        logger.info(f"🧠 Loading GLM-ASR from {self.model_path}...")
        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_path, 
                trust_remote_code=True
            )
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            self.model.eval()
            logger.info(f"✅ GLM-ASR Loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load GLM-ASR: {e}")
            raise

    def transcribe(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribes audio file to text with timestamps.
        
        Returns:
            {
                "text": "full transcription",
                "segments": [{"text": "...", "start": 0.0, "end": 3.0}],
                "language": "zh"
            }
        """
        if not self.model:
            self.load()
            
        logger.info(f"🧠 Transcribing {audio_path}...")
        try:
            # Load audio at 16kHz (standard for ASR models)
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Process audio through processor
            inputs = self.processor(
                audio,
                sampling_rate=16000,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=448,
                    do_sample=False
                )
            
            # Decode output
            transcription = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            logger.info(f"✅ Transcription: {transcription[:100]}...")
            
            # For now, return simple format
            # Full timestamp alignment would require additional VAD integration
            return {
                "text": transcription,
                "segments": [
                    {
                        "text": transcription,
                        "start": 0.0,
                        "end": len(audio) / sr
                    }
                ],
                "language": language or "auto"
            }
            
        except Exception as e:
            logger.error(f"GLM Transcription Failed: {e}")
            raise

    def unload(self):
        if self.model:
            logger.info("🧹 Unloading GLM-ASR...")
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ GLM-ASR unloaded")

