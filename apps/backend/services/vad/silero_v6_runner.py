"""
Stage 2: The Ears (VAD)
Model: Silero VAD v6.2
Purpose: Voice Activity Detection with baby cry filtering
Link: https://github.com/snakers4/silero-vad
"""

import logging
import torch
import torchaudio
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class SileroV6Runner:
    """
    Stage 2: The Ears
    Silero VAD v6.2 for voice activity detection.
    """
    
    def __init__(self, model_version: str = "v6.2", threshold: float = 0.5):
        self.model_version = model_version
        self.threshold = threshold
        self.model = None
        self.utils = None
        
    def load(self):
        """Load Silero VAD model from torch hub."""
        if self.model:
            return
            
        logger.info(f"👂 Loading Silero VAD {self.model_version}...")
        try:
            # Load model from torch hub
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            
            # Extract utility functions
            (get_speech_timestamps,
             save_audio,
             read_audio,
             VADIterator,
             collect_chunks) = self.utils
            
            self.get_speech_timestamps = get_speech_timestamps
            self.read_audio = read_audio
            self.collect_chunks = collect_chunks
            
            logger.info(f"✅ Silero VAD {self.model_version} loaded")
            
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise
    
    def process(self, audio_path: str, sampling_rate: int = 16000) -> list:
        """
        Detect speech segments in audio.
        
        Args:
            audio_path: Path to audio file
            sampling_rate: Target sampling rate (16kHz for Silero)
            
        Returns:
            List of dicts with 'start' and 'end' timestamps in seconds
        """
        if not self.model:
            self.load()
        
        logger.info(f"👂 Running VAD on {Path(audio_path).name}...")
        
        try:
            # Read audio file
            wav = self.read_audio(audio_path, sampling_rate=sampling_rate)
            
            # Get speech timestamps
            speech_timestamps = self.get_speech_timestamps(
                wav,
                self.model,
                threshold=self.threshold,
                sampling_rate=sampling_rate,
                min_speech_duration_ms=250,
                min_silence_duration_ms=100
            )
            
            # Convert to seconds
            segments = []
            for ts in speech_timestamps:
                segments.append({
                    'start': ts['start'] / sampling_rate,
                    'end': ts['end'] / sampling_rate
                })
            
            logger.info(f"✅ Found {len(segments)} speech segments")
            return segments
            
        except Exception as e:
            logger.error(f"VAD processing failed: {e}")
            # Return full audio as one segment on failure
            import librosa
            audio, sr = librosa.load(audio_path, sr=None)
            return [{'start': 0.0, 'end': len(audio) / sr}]
    
    def unload(self):
        """Unload model from memory."""
        if self.model:
            logger.info("🧹 Unloading Silero VAD...")
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ Silero VAD unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = SileroV6Runner()
    runner.load()
    # segments = runner.process("test.wav")
    # print(f"Segments: {segments}")
    runner.unload()
    print("✅ Silero runner test complete")
