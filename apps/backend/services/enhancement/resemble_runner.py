"""
Stage 1.5: The Polisher (Enhancement)
Model: Resemble Enhance
Purpose: Upscale audio to studio quality, remove noise/artifacts
Link: https://github.com/resemble-ai/resemble-enhance
"""

import logging
import subprocess
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ResembleRunner:
    """
    Stage 1.5: The Polisher
    Wraps resemble-enhance CLI for audio enhancement.
    """
    
    def __init__(self, denoise_only: bool = False):
        self.denoise_only = denoise_only
        
    def polish(self, input_wav: str, output_wav: str = None) -> str:
        """
        Enhances audio quality using Resemble Enhance.
        
        Args:
            input_wav: Path to input audio file
            output_wav: Path to save enhanced audio (optional)
            
        Returns:
            Path to enhanced audio file
        """
        if output_wav is None:
            input_path = Path(input_wav)
            output_wav = str(input_path.parent / f"{input_path.stem}_polished.wav")
        
        logger.info(f"✨ The Polisher: Enhancing {os.path.basename(input_wav)}")
        
        try:
            # Build resemble-enhance command
            cmd = [
                "resemble-enhance",
                input_wav,
                "-o", output_wav
            ]
            
            if self.denoise_only:
                cmd.append("--denoise_only")
            
            #Run enhancement
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("✅ Audio enhanced successfully")
            if result.stdout:
                logger.debug(f"Resemble output: {result.stdout}")
            
            return output_wav
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Resemble Enhance failed: {e.stderr}")
            logger.warning("Returning original audio (enhancement skipped)")
            return input_wav
            
        except FileNotFoundError:
            logger.error("resemble-enhance CLI not found. Install with: pip install resemble-enhance")
            logger.warning("Returning original audio (enhancement skipped)")
            return input_wav
    
    def unload(self):
        """No GPU model to unload (CLI-based)."""
        pass


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = ResembleRunner()
    # result = runner.polish("test.wav")
    print("✅ Resemble runner initialized")
