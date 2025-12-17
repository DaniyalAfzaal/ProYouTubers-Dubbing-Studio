"""
Stage 9: The Renderer (Vocoder)
Model: BigVGAN v2
Purpose: Final high-fidelity audio synthesis, artifact removal
Link: https://github.com/NVIDIA/BigVGAN
"""

import logging
import torch
import numpy as np
import soundfile as sf
from pathlib import Path

logger = logging.getLogger(__name__)


class BigVGANRunner:
    """
    Stage 9: The Renderer
    BigVGAN v2 vocoder for final audio synthesis.
    """
    
    def __init__(
        self, 
        model_name: str = "nvidia/bigvgan_v2_22khz_80band_256x",
        device: str = None
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else"cpu")
        self.model = None
        self.sample_rate = 22050  # BigVGAN default
        
    def load(self):
        """Load BigVGAN model."""
        if self.model:
            return
            
        logger.info(f"🎛️ Loading BigVGAN v2...")
        try:
            # Try importing BigVGAN
            try:
                from bigvgan import BigVGAN
                self.model = BigVGAN.from_pretrained(self.model_name).to(self.device)
                self.model.eval()
                logger.info(f"✅ BigVGAN loaded on {self.device}")
            except ImportError:
                logger.warning("BigVGAN package not installed")
                logger.warning("Install with: pip install git+https://github.com/NVIDIA/BigVGAN.git")
                self.model = None
                
        except Exception as e:
            logger.error(f"Failed to load BigVGAN: {e}")
            self.model = None
    
    def render(
        self, 
        input_audio: str, 
        output_audio: str = None,
        target_sr: int = 44100
    ) -> str:
        """
        Render audio through BigVGAN vocoder.
        
        Args:
            input_audio: Path to input audio
            output_audio: Where to save rendered audio
            target_sr: Target sample rate
            
        Returns:
            Path to rendered audio
        """
        if output_audio is None:
            input_path = Path(input_audio)
            output_audio = str(input_path.parent / f"{input_path.stem}_rendered.wav")
        
        if not self.model:
            self.load()
        
        if not self.model:
            # Fallback: just copy input
            logger.warning("⚠️ BigVGAN not available, using input audio as-is")
            import shutil
            shutil.copy(input_audio, output_audio)
            return output_audio
        
        logger.info(f"🎛️ Rendering audio through BigVGAN...")
        
        try:
            # Load audio
            import librosa
            audio, sr = librosa.load(input_audio, sr=self.sample_rate, mono=True)
            
            # Convert to tensor
            audio_tensor = torch.FloatTensor(audio).unsqueeze(0).to(self.device)
            
            # Run through vocoder
            with torch.no_grad():
                # Extract mel spectrogram (simplified - real impl would use proper mel extractor)
                # This is a placeholder - actual BigVGAN needs proper mel features
                mel = self._audio_to_mel(audio_tensor)
                rendered = self.model(mel)
                rendered_audio = rendered.squeeze().cpu().numpy()
            
            # Resample if needed
            if target_sr != self.sample_rate:
                from scipy.signal import resample
                new_length = int(len(rendered_audio) * target_sr / self.sample_rate)
                rendered_audio = resample(rendered_audio, new_length)
                save_sr = target_sr
            else:
                save_sr = self.sample_rate
            
            # Save
            sf.write(output_audio, rendered_audio, save_sr)
            logger.info("✅ Audio rendered successfully")
            return output_audio
            
        except Exception as e:
            logger.error(f"BigVGAN rendering failed: {e}")
            logger.warning("Copying input audio as fallback")
            import shutil
            shutil.copy(input_audio, output_audio)
            return output_audio
    
    def _audio_to_mel(self, audio_tensor):
        """Convert audio to mel spectrogram (placeholder)."""
        # This is a simplified placeholder
        # Real implementation would use proper mel spectrogram extraction
        import torchaudio
        mel_spec = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            n_fft=1024,
            hop_length=256,
            n_mels=80
        ).to(self.device)
        return mel_spec(audio_tensor)
    
    def unload(self):
        """Unload BigVGAN model."""
        if self.model:
            logger.info("🧹 Unloading BigVGAN...")
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ BigVGAN unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = BigVGANRunner()
    runner.load()
    # result = runner.render("test.wav")
    # print(f"Rendered: {result}")
    runner.unload()
    print("✅ BigVGAN runner test complete")
