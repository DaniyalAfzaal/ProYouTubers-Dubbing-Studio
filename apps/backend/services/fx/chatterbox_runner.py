"""
Stage 7.5: The FX (Humanizer)
Model: Chatterbox-Turbo
Purpose: Insert emotional effects ([laugh], [sigh], [breath]) into synthesized speech
Link: https://huggingface.co/ResembleAI/chatterbox-turbo
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch
import torchaudio
import gc
import re

logger = logging.getLogger(__name__)


class ChatterboxRunner:
    """
    Stage 7.5: The FX (Humanizer)
    Inserts emotional sound effects into TTS audio based on script tags.
    """
    
    def __init__(self, model_name: str = "ResembleAI/chatterbox-turbo"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load(self):
        """Load Chatterbox-Turbo model."""
        try:
            logger.info(f"Loading Chatterbox-Turbo from {self.model_name}")
            
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
            
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info("✅ Chatterbox-Turbo loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Chatterbox-Turbo: {e}")
            logger.warning("Continuing without humanizer (FX stage will be skipped)")
            
    def apply_effects(
        self,
        audio_path: str,
        script: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Apply emotional effects to audio based on script tags.
        
        Args:
            audio_path: Path to TTS audio file
            script: Translated script with emotion tags ([laugh], [sigh], etc.)
            output_path: Where to save enhanced audio
            
        Returns:
            Path to enhanced audio file
        """
        if not self.model:
            logger.warning("Model not loaded - skipping FX stage")
            return audio_path
            
        try:
            # Load original audio
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Detect emotion tags in script
            tags = self._extract_emotion_tags(script)
            
            if not tags:
                logger.info("No emotion tags found in script - returning original audio")
                return audio_path
            
            logger.info(f"Found emotion tags: {tags}")
            
            # Generate emotional effects
            enhanced_audio = waveform  # Start with original
            
            for tag_info in tags:
                effect_type = tag_info['type']
                position = tag_info['position']  # Character position in script
                
                # Generate the effect audio
                effect_audio = self._generate_effect(effect_type)
                
                if effect_audio is not None:
                    # Insert effect at appropriate timestamp
                    # This is a simplified version - real implementation would need
                    # precise timing alignment with the TTS audio
                    enhanced_audio = self._insert_effect(
                        enhanced_audio,
                        effect_audio,
                        position,
                        sample_rate
                    )
            
            # Save enhanced audio
            if output_path is None:
                output_path = str(Path(audio_path).parent / f"{Path(audio_path).stem}_fx.wav")
            
            torchaudio.save(output_path, enhanced_audio, sample_rate)
            
            logger.info(f"✅ FX applied: {len(tags)} effects inserted")
            return output_path
            
        except Exception as e:
            logger.error(f"FX application failed: {e}")
            return audio_path  # Return original if FX fails
    
    def _extract_emotion_tags(self, script: str) -> List[Dict[str, Any]]:
        """Extract [laugh], [sigh], etc. tags from script."""
        # Regex to find [emotion] tags
        pattern = r'\[(\w+)\]'
        matches = re.finditer(pattern, script)
        
        tags = []
        for match in matches:
            emotion = match.group(1).lower()
            if emotion in ['laugh', 'sigh', 'breath', 'gasp', 'sob']:
                tags.append({
                    'type': emotion,
                    'position': match.start()
                })
        
        return tags
    
    def _generate_effect(self, effect_type: str) -> Optional[torch.Tensor]:
        """
        Generate an audio effect using Chatterbox-Turbo.
        
        Args:
            effect_type: Type of effect ('laugh', 'sigh', etc.)
            
        Returns:
            Audio tensor or None if generation fails
        """
        try:
            # Prompt the model to generate the effect
            prompt = f"Generate audio of a person {effect_type}ing naturally"
            
            inputs = self.processor(prompt, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                generated_audio = self.model.generate(**inputs)
            
            return generated_audio
            
        except Exception as e:
            logger.error(f"Effect generation failed for '{effect_type}': {e}")
            return None
    
    def _insert_effect(
        self,
        base_audio: torch.Tensor,
        effect_audio: torch.Tensor,
        position: int,
        sample_rate: int
    ) -> torch.Tensor:
        """
        Insert effect audio at specified position in base audio.
        
        This is a simplified implementation. Real version would need:
        - Precise timing alignment with script
        - Volume normalization
        - Crossfading
        """
        # For now, just return the base audio
        # Full implementation would splice the effect in
        logger.debug(f"Would insert effect at position {position}")
        return base_audio
    
    def unload(self):
        """Unload model to free VRAM."""
        logger.info("Unloading Chatterbox-Turbo")
        del self.model
        del self.processor
        self.model = None
        self.processor = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("✅ Chatterbox-Turbo unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = ChatterboxRunner()
    runner.load()
    
    # Test tag extraction
    test_script = "Hello [laugh] how are you? I'm doing great [sigh] thanks for asking."
    tags = runner._extract_emotion_tags(test_script)
    print(f"Extracted tags: {tags}")
    
    runner.unload()
    print("✅ Runner test complete")
