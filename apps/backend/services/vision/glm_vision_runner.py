"""
Stage 5: The Eyes (Vision Context)
Model: GLM-4.6V-Flash
Purpose: Analyze video frames to determine speaker gender and fix pronoun mismatches
Link: https://huggingface.co/zai-org/GLM-4.6V-Flash
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import torch
import gc

logger = logging.getLogger(__name__)


class GLMVisionRunner:
    """
    Stage 5: The Eyes
    Analyzes video frames to detect speaker gender and fix pronoun references.
    """
    
    def __init__(self, model_name: str = "zai-org/GLM-4.6V-Flash"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load(self):
        """Load GLM-4.6V model for vision analysis."""
        try:
            logger.info(f"Loading GLM-4.6V-Flash from {self.model_name}")
            
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info("✅ GLM-4.6V-Flash loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load GLM-4.6V: {e}")
            raise
            
    def analyze_gender(self, video_path: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze video frames to determine speaker gender per segment.
        
        Args:
            video_path: Path to video file
            segments: List of ASR segments with timing
            
        Returns:
            Same segments with added 'gender' metadata
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load() first.")
            
        try:
            from PIL import Image
            import cv2
            
            logger.info(f"Analyzing video: {video_path}")
            
            # Extract key frames
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            for seg in segments:
                # Get frame at segment midpoint
                mid_time = (seg['start'] + seg['end']) / 2
                frame_number = int(mid_time * fps)
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"Could not extract frame at {mid_time}s")
                    seg['metadata'] = seg.get('metadata', {})
                    seg['metadata']['gender'] = 'unknown'
                    continue
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                
                # Query the vision model
                prompt = "Look at this image. Is the speaker male or female? Answer with only 'male' or 'female'."
                
                inputs = self.tokenizer(prompt, return_tensors="pt", return_token_type_ids=False)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Add image to inputs (GLM-4.6V specific)
                inputs['images'] = [image]
                
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=10,
                        do_sample=False
                    )
                
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract gender from response
                gender = 'unknown'
                if 'male' in response.lower() and 'female' not in response.lower():
                    gender = 'male'
                elif 'female' in response.lower():
                    gender = 'female'
                
                # Add to segment metadata
                seg['metadata'] = seg.get('metadata', {})
                seg['metadata']['gender'] = gender
                
                logger.info(f"Segment {seg.get('id', '?')}: Detected gender = {gender}")
            
            cap.release()
            logger.info(f"✅ Vision analysis complete: {len(segments)} segments analyzed")
            return segments
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            # Return segments unchanged if vision fails
            for seg in segments:
                seg['metadata'] = seg.get('metadata', {})
                seg['metadata']['gender'] = 'unknown'
            return segments
            
    def unload(self):
        """Unload model to free VRAM."""
        logger.info("Unloading GLM-4.6V-Flash")
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("✅ GLM-4.6V-Flash unloaded")


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    runner = GLMVisionRunner()
    runner.load()
    
    # Test with dummy segments
    test_segments = [
        {"id": 0, "start": 0.0, "end": 3.0, "text": "Hello"},
        {"id": 1, "start": 3.0, "end": 6.0, "text": "World"}
    ]
    
    # Note: Requires actual video file to test
    # result = runner.analyze_gender("test_video.mp4", test_segments)
    
    runner.unload()
    print("✅ Runner test complete")
