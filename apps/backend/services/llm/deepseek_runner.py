import os
import logging
import json
from typing import List, Dict, Union
# deepseek acts like OpenAI client usually
from openai import OpenAI

logger = logging.getLogger(__name__)

class DeepSeekRunner:
    """
    Stage 6: The Logic
    DeepSeek-V3.2 - Translates and times the script.
    """
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1"):
        self.client = None
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url

    def _ensure_client(self):
        if not self.client and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        elif not self.api_key:
            logger.warning("DeepSeek API Key missing!")

    def process_script(self, transcript: List[Dict], target_lang: str = "English") -> List[Dict]:
        """
        Takes transcript [{'text': '...', 'start': 0, 'end': 3}]
        Returns translated [{'text': '...', 'start': 0, 'end': 3, 'emotion': 'sad'}]
        """
        self._ensure_client()
        if not self.client:
            return transcript # Return original if no AI

        logger.info(f"🤔 DeepSeek: Translating {len(transcript)} lines to {target_lang}...")
        
        # Construct Prompt
        # Simplified for brevity
        prompt = f"Translate the following subtitles to {target_lang}. Maintain timing. Output JSON."
        input_text = json.dumps(transcript)
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a professional dubbing script writer."},
                    {"role": "user", "content": f"{prompt}\n{input_text}"}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"DeepSeek Logic Failed: {e}")
            return transcript

    def unload(self):
        # API client has no state
        pass
