import torch
import logging
import os
from pprint import pprint

logger = logging.getLogger(__name__)

class SileroV6Runner:
    """
    Stage 3: The Ears
    Silero VAD v6.2 - Smart Gatekeeper.
    """
    def __init__(self, use_onnx: bool = True):
        self.model = None
        self.utils = None
        self.use_onnx = use_onnx

    def load(self):
        if self.model: return
        
        logger.info("👂 Loading Silero VAD v6...")
        try:
            # Force reload to get latest v5+ (Silero repo wraps v5/v6 in same hub)
            # 'snakers4/silero-vad'
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=self.use_onnx
            )
            logger.info("✅ Silero VAD Loaded.")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise

    def process(self, audio_path: str, return_seconds: bool = True) -> list:
        """
        Returns list of speech timestamps {'start': 0.5, 'end': 1.2}
        """
        if not self.model:
            self.load()
            
        (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = self.utils
        
        wav = read_audio(audio_path)
        
        # Get speech timestamps
        # V6 might have specific params for 'baby' filtering if available in their API?
        # Standard VAD doesn't have explicit 'ignore_baby' flag, 
        # but the model itself is trained to be more robust.
        logger.info(f"👂 Scanning {os.path.basename(audio_path)} for speech...")
        
        speech_timestamps = get_speech_timestamps(
            wav, 
            self.model, 
            return_seconds=return_seconds
        )
        
        logger.info(f"✅ Found {len(speech_timestamps)} speech segments.")
        return speech_timestamps

    def unload(self):
        if self.model:
            del self.model
            # utils contains functions, not heavy objects, but acceptable to clear
            del self.utils
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
