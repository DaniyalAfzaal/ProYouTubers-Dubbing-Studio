import torch
import logging
from transformers import AutoModel, AutoTokenizer
# GLM-ASR might use specific audio processing flow.
# Assuming standard HF Interface for "zai-org/GLM-ASR-Nano-2512"
# If it requires 'glmasr' library, user needs to install it. 
# Providing the generic HF implementation wrapper.

logger = logging.getLogger(__name__)

class GLMASRRunner:
    """
    Stage 5: The Brain
    GLM-ASR-Nano-2512 - Hallucination free ASR.
    """
    def __init__(self, model_path: str = "zai-org/GLM-ASR-Nano-2512"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

    def load(self):
        if self.model: return

        logger.info(f"🧠 Loading GLM-ASR ({self.model_path})...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True)
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
                self.model.eval()
            logger.info("✅ GLM-ASR Loaded.")
        except Exception as e:
            logger.error(f"Failed to load GLM-ASR: {e}")
            raise

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio file to text.
        """
        if not self.model:
            self.load()
            
        logger.info(f"🧠 Transcribing {audio_path}...")
        try:
            # NOTE: Actual inference API depends on the remote model code.
            # GLM models often have a .transcribe() or .chat() method if it's GLM-4 class.
            # Assuming a .transcribe method exposed by the trust_remote_code=True model.
            
            # Placeholder for exact inference syntax:
            res = self.model.transcribe(audio_path)
            
            # If it returns a structure, extract text
            text = res if isinstance(res, str) else str(res)
            logger.info(f"✅ Text: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"GLM Transcription Failed: {e}")
            raise

    def unload(self):
        if self.model:
            del self.model
            del self.tokenizer
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
