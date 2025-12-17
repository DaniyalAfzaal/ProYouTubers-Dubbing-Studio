import logging
import os
from typing import Literal

# Import Stages
from apps.backend.services.separation.roformer_runner import RoformerRunner
from apps.backend.services.enhancement.resemble_runner import ResembleRunner
from apps.backend.services.vad.silero_v6_runner import SileroV6Runner
from apps.backend.services.safety.age_gender_scanner import SafetyScanner
from apps.backend.services.asr.glm_runner import GLMASRRunner
from apps.backend.services.llm.deepseek_runner import DeepSeekRunner
from apps.backend.services.tts.f5_runner import F5TTSRunner
from apps.backend.services.tts.kokoro_runner import KokoroRunner
from apps.backend.services.vc.applio_runner import ApplioRunner
from apps.backend.services.vocoder.bigvgan_runner import BigVGANRunner

logger = logging.getLogger(__name__)

class PipelineManager:
    """
    The Orchestrator of the 9-Stage God Tier Pipeline.
    Manages VRAM by sequentially loading/unloading models in 'Hollywood' mode.
    """
    def __init__(self, work_dir: str = "output/"):
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)
        
        # Initialize Runners (Lazy Loading)
        self.roformer = RoformerRunner()
        self.resemble = ResembleRunner()
        self.silero = SileroV6Runner()
        self.safety = SafetyScanner()
        self.glm = GLMASRRunner()
        self.deepseek = DeepSeekRunner()
        self.f5 = F5TTSRunner()
        self.kokoro = KokoroRunner()
        self.applio = ApplioRunner()
        self.bigvgan = BigVGANRunner()

    def run_draft(self, video_path: str):
        """
        Mode A: Speed Run (Check Timing)
        Stack: Silero -> GLM -> DeepSeek -> Kokoro
        """
        logger.info("🏎️ STARTING DRAFT MODE PIPELINE")
        
        # 1. Extract Audio (Simple ffmpeg)
        # Using media_separation utils or simple ffmpeg here for speed
        raw_audio = os.path.join(self.work_dir, "raw.mp3")
        # subprocess call to ffmpeg... (omitted for brevity)
        
        # 2. VAD (Keep bad segments, just need timestamps for existing speech)
        timestamps = self.silero.process(raw_audio)
        
        # 3. ASR
        transcript = self.glm.transcribe(raw_audio) # Or parse timestamps
        
        # 4. LLM
        # translated = self.deepseek.process(transcript)
        translated = transcript # Placeholder
        
        # 5. TTS (Kokoro)
        out_audio = self.kokoro.generate(translated)
        
        logger.info("🏁 Draft Mode Complete.")
        return out_audio

    def run_hollywood(self, video_path: str):
        """
        Mode B: Hollywood Render (Max Fidelity)
        Stack: Roformer -> Resemble -> Silero -> Guard -> GLM -> DeepSeek -> F5 -> Applio -> BigVGAN
        SEQUENTIAL EXECUTION to save VRAM.
        """
        logger.info("🎬 STARTING HOLLYWOOD MODE PIPELINE")
        
        stages = {}
        
        # Stage 1: The Surgeon
        vocals, inst = self.roformer.separate(video_path, self.work_dir)
        stages['step1'] = vocals
        self.roformer.unload()
        
        # Stage 2: The Polisher
        polished = self.resemble.polish(vocals, os.path.join(self.work_dir, "polished.wav"))
        stages['step2'] = polished
        # self.resemble.unload() # Not strictly needed if CLI
        
        # Stage 3: The Ears
        timestamps = self.silero.process(polished)
        self.silero.unload()
        
        # Stage 4: The Guard
        scan_res = self.safety.scan(polished, 16000) # Load audio properly in real impl
        self.safety.unload()
        if not scan_res.get('is_safe'):
             logger.warning("⚠️ Safety Guard flagged content. Proceeding with caution.")
        
        # Stage 5: The Brain
        text = self.glm.transcribe(polished)
        stages['step5'] = text
        self.glm.unload()
        
        # Stage 6: The Logic (API - No VRAM)
        # translated = self.deepseek.process(text)
        
        # Stage 7: The Mouth (F5)
        tts_raw = self.f5.generate(text, polished) # Using polished as ref
        self.f5.unload()
        
        # Stage 8: The Skin
        # cloned = self.applio.apply_skin(tts_raw, ref_model_path...)
        cloned = tts_raw # Placeholder until model path logic provided
        self.applio.unload()
        
        # Stage 9: The Renderer
        final = self.bigvgan.render(cloned, os.path.join(self.work_dir, "final_master.wav"))
        self.bigvgan.unload()
        
        logger.info("🏆 Hollywood Mode Complete.")
        return final
