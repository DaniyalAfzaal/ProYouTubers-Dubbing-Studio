import os
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
from audio_separator.separator import Separator
import torch

logger = logging.getLogger(__name__)

class RoformerRunner:
    """
    Stage 1: The Surgeon
    Wraps 'audio-separator' to perform high-fidelity vocal isolation.
    """
    def __init__(self, model_dir: str = "/tmp/audio-separator-models/"):
        self.model_dir = model_dir
        self.separator = None
        self._ensure_init()

    def _ensure_init(self):
        """Lazy initialization of the Separator to avoid loading CUDA context until needed."""
        if not self.separator:
            logger.info("Initializing Roformer Separator...")
            self.separator = Separator(
                model_file_dir=self.model_dir,
                log_level=logging.INFO,
                output_format="mp3" # Can be changed to wav/flac
            )

    def separate(
        self, 
        input_file: str, 
        output_dir: str, 
        model_name: str = "model_bs_roformer_ep_317_sdr_12.9755.ckpt", # Viperx 1297
        custom_output_names: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str]:
        """
        Separates audio into vocals and instrumental.
        Returns paths to (vocals_file, instrumental_file).
        """
        self._ensure_init()
        
        logger.info(f"🔪 The Surgeon: Separating {os.path.basename(input_file)} using {model_name}")
        
        # Configure output
        os.makedirs(output_dir, exist_ok=True)
        self.separator.output_dir = output_dir
        
        # Load Model (this downloads if missing)
        try:
            self.separator.load_model(model_filename=model_name)
        except Exception as e:
            logger.error(f"Failed to load separation model {model_name}: {e}")
            raise

        # Run Separation
        outputs = self.separator.separate(input_file, custom_output_names=custom_output_names)
        
        # Resolve output paths
        # outputs is usually a list of filenames created in output_dir
        vocals_path = None
        inst_path = None
        
        for fname in outputs:
            full_path = os.path.join(output_dir, fname)
            if "Vocals" in fname or (custom_output_names and custom_output_names.get("Vocals") in fname):
                vocals_path = full_path
            elif "Instrumental" in fname or (custom_output_names and custom_output_names.get("Instrumental") in fname):
                inst_path = full_path
                
        logger.info(f"✅ Separation Complete. Vocals: {vocals_path}")
        return vocals_path, inst_path

    def unload(self):
        """
        Unloads model from VRAM.
        Essential for the sequential 'Hollywood' pipeline.
        """
        if self.separator:
            logger.info("🧹 Unloading Roformer from VRAM...")
            del self.separator
            self.separator = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
