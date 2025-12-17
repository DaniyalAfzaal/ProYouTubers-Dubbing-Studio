import logging
import os
from typing import Literal

# Import Stages
from apps.backend.services.separation.roformer_runner import RoformerRunner
from apps.backend.services.enhancement.resemble_runner import ResembleRunner
from apps.backend.services.vad.silero_v6_runner import SileroV6Runner
from apps.backend.services.safety.age_gender_scanner import SafetyScanner
from apps.backend.services.asr.glm_runner import GLMASRRunner
from apps.backend.services.vision.glm_vision_runner import GLMVisionRunner  # NEW: Stage 5
from apps.backend.services.llm.deepseek_runner import DeepSeekRunner
from apps.backend.services.tts.f5_runner import F5TTSRunner
from apps.backend.services.tts.kokoro_runner import KokoroRunner
from apps.backend.services.fx.chatterbox_runner import ChatterboxRunner  # NEW: Stage 7.5
from apps.backend.services.vc.applio_runner import ApplioRunner
from apps.backend.services.vocoder.bigvgan_runner import BigVGANRunner

logger = logging.getLogger(__name__)

class PipelineManager:
    """
    The Orchestrator of the 10-Stage Perfectionist Pipeline.
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
        self.vision = GLMVisionRunner()  # NEW: Stage 5
        self.deepseek = DeepSeekRunner()
        self.f5 = F5TTSRunner()
        self.kokoro = KokoroRunner()
        self.chatterbox = ChatterboxRunner()  # NEW: Stage 7.5
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
        Stack: Roformer -> Resemble -> Silero -> Guard -> GLM -> EYES -> DeepSeek -> F5 -> FX -> Applio -> BigVGAN
        SEQUENTIAL EXECUTION to save VRAM.
        """
        logger.info("🎬 STARTING HOLLYWOOD MODE PIPELINE (10 STAGES)")
        
        stages = {}
        segments = []  # Will hold ASR segments with metadata
        
        # Stage 1: The Surgeon
        vocals, inst = self.roformer.separate(video_path, self.work_dir)
        stages['step1'] = vocals
        self.roformer.unload()
        
        # Stage 1.5: The Polisher
        polished = self.resemble.polish(vocals, os.path.join(self.work_dir, "polished.wav"))
        stages['step1.5'] = polished
        # self.resemble.unload() # Not strictly needed if CLI
        
        # Stage 2: The Ears (VAD)
        timestamps = self.silero.process(polished)
        self.silero.unload()
        
        # Stage 3: The Guard (Safety)
        scan_res = self.safety.scan(polished, 16000)
        self.safety.unload()
        if not scan_res.get('is_safe'):
             logger.warning("⚠️ Safety Guard flagged content. Proceeding with caution.")
        
        # Stage 4: The Brain (ASR)
        text = self.glm.transcribe(polished)
        segments = text if isinstance(text, list) else [{'text': text, 'start': 0, 'end': 0}]
        stages['step4'] = segments
        self.glm.unload()
        
        # Stage 5: The Eyes (Vision) - NEW
        logger.info("👁️ Stage 5: Analyzing video frames for gender context")
        try:
            self.vision.load()
            segments = self.vision.analyze_gender(video_path, segments)
            self.vision.unload()
            logger.info("✅ Vision analysis complete")
        except Exception as e:
            logger.warning(f"Vision stage failed (continuing): {e}")
            # Continue without vision if it fails
        
        # Stage 6: The Logic (LLM Translation - API, No VRAM)
        # translated_script = self.deepseek.process(segments)
        translated_script = segments  # Placeholder
        
        # Stage 7: The Mouth (F5-TTS)
        tts_raw = self.f5.generate(translated_script, polished)
        self.f5.unload()
        
        # Stage 7.5: The FX (Humanizer) - NEW
        logger.info("🎭 Stage 7.5: Applying emotional effects (Chatterbox)")
        try:
            self.chatterbox.load()
            # Extract script text for tag detection
            script_text = " ".join([s.get('text', '') for s in segments])
            tts_with_fx = self.chatterbox.apply_effects(tts_raw, script_text)
            self.chatterbox.unload()
            logger.info("✅ FX applied")
        except Exception as e:
            logger.warning(f"FX stage failed (continuing): {e}")
            tts_with_fx = tts_raw  # Use original if FX fails
        
        # Stage 8: The Skin (RVC Voice Cloning)
        # cloned = self.applio.apply_skin(tts_with_fx, ref_model_path...)
        cloned = tts_with_fx  # Placeholder until model path logic provided
        self.applio.unload()
        
        # Stage 9: The Renderer (BigVGAN Vocoder)
        final = self.bigvgan.render(cloned, os.path.join(self.work_dir, "final_master.wav"))
        self.bigvgan.unload()
        
        logger.info("🏆 HOLLYWOOD MODE COMPLETE (10 STAGES)")
        return final
