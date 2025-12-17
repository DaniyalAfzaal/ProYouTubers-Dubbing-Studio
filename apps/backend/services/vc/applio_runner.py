"""
Stage 8: The Skin (Voice Cloning)
Model: Applio (RVC)
Purpose: Apply original speaker's voice timbre to TTS output
Link: https://github.com/IAHispano/Applio
"""

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class ApplioRunner:
    """
    Stage 8: The Skin
    Wraps Applio/RVC for voice cloning.
    """
    
    def __init__(self, models_dir: str = "models/rvc"):
        self.models_dir = Path(models_dir)
        self.current_model = None
        
    def load(self, model_path: str = None):
        """Load RVC model (if using Python bindings)."""
        logger.info(f"🎨 Preparing RVC voice cloning...")
        self.current_model = model_path
        # Note: Applio is primarily CLI-based
        # If using rvc-python package, would load model here
    
    def apply_skin(
        self, 
        input_audio: str, 
        reference_voice: str = None,
        output_audio: str = None,
        pitch_shift: int = 0,
        index_rate: float = 0.5
    ) -> str:
        """
        Apply voice cloning to audio.
        
        Args:
            input_audio: Path to input TTS audio
            reference_voice: Path to reference audio (for extracting voice model)
            output_audio: Where to save cloned audio
            pitch_shift: Semitones to shift pitch
            index_rate: Feature retrieval strength (0-1)
            
        Returns:
            Path to voice-cloned audio
        """
        if output_audio is None:
            input_path = Path(input_audio)
            output_audio = str(input_path.parent / f"{input_path.stem}_cloned.wav")
        
        logger.info(f"🎨 Applying RVC voice cloning...")
        
        try:
            # Method 1: Try using Applio CLI if installed
            if self.current_model:
                cmd = [
                    "python -m applio.infer",  
                    "--input", input_audio,
                    "--model", self.current_model,
                    "--output", output_audio,
                    "--pitch", str(pitch_shift),
                    "--index_rate", str(index_rate)
                ]
                
                result = subprocess.run(
                    " ".join(cmd),
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and Path(output_audio).exists():
                    logger.info("✅ Voice cloning successful")
                    return output_audio
            
            # Method 2: Try rvc-python package
            try:
                from rvc_python.infer import RVCInference
                rvc = RVCInference(device="cuda")
                rvc.infer_file(
                    input_path=input_audio,
                    output_path=output_audio,
                    model_path=self.current_model,
                    pitch=pitch_shift
                )
                logger.info("✅ Voice cloning successful (rvc-python)")
                return output_audio
            except ImportError:
                pass
            
            # Fallback: Return original audio
            logger.warning("⚠️ RVC not available, skipping voice cloning")
            return input_audio
            
        except Exception as e:
            logger.error(f"RVC cloning failed: {e}")
            logger.warning("Returning original audio")
            return input_audio
    
    def unload(self):
        """Unload model."""
        if self.current_model:
            logger.info("🧹 Unloading RVC model...")
            self.current_model = None
            logger.info("✅ RVC model unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = ApplioRunner()
    # result = runner.apply_skin("test.wav", reference_voice="ref.wav")
    # print(f"Result: {result}")
    print("✅ Applio runner initialized")
