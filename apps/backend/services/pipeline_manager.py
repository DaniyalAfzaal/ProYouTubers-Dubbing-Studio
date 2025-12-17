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
    def __init__(self, work_dir: str = "output/", config: dict = None):
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)
        
        # Parse God Tier configuration
        self.config = config or {}
        self.stages_enabled = self.config.get('stages_enabled', {})
        self.stage_models = self.config.get('stage_models', {})
        
        logger.info(f"🎛️ Pipeline config: {len(self.stages_enabled)} stage toggles, {len(self.stage_models)} model selections")
        
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
    
    def is_stage_enabled(self, stage_id: str) -> bool:
        """Check if a stage is enabled in user configuration."""
        return self.stages_enabled.get(f'stage{stage_id}', True)  # Default: enabled

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
        Stack: Roformer → Resemble → Silero → Guard → GLM → EYES → DeepSeek → F5 → FX → Applio → BigVGAN
        SEQUENTIAL EXECUTION to save VRAM.
        """
        logger.info("🎬 STARTING HOLLYWOOD MODE PIPELINE (10 STAGES)")
        
        stages = {}
        segments = []
        current_audio = video_path
        
        # Stage 1: The Surgeon
        if self.is_stage_enabled('1'):
            logger.info("🔪 Stage 1: Isolating vocals")
            vocals, inst = self.roformer.separate(video_path, self.work_dir)
            stages['step1'] = vocals
            current_audio = vocals
            self.roformer.unload()
        else:
            logger.info("⏭️ Stage 1: SKIPPED (user disabled)")
            vocals = video_path
        
        # Stage 1.5: The Polisher
        if self.is_stage_enabled('1.5'):
            logger.info("✨ Stage 1.5: Enhancing audio quality")
            polished = self.resemble.polish(vocals, os.path.join(self.work_dir, "polished.wav"))
            stages['step1.5'] = polished
            current_audio = polished
        else:
            logger.info("⏭️ Stage 1.5: SKIPPED (user disabled)")
            polished = vocals
        
        # Stage 2: The Ears (VAD)
        if self.is_stage_enabled('2'):
            logger.info("👂 Stage 2: Voice Activity Detection")
            timestamps = self.silero.process(polished)
            self.silero.unload()
        else:
            logger.info("⏭️ Stage 2: SKIPPED (user disabled)")
            timestamps = []
        
        # Stage 3: The Guard (Safety)
        if self.is_stage_enabled('3'):
            logger.info("🛡️ Stage 3: Safety check")
            scan_res = self.safety.scan(polished, 16000)
            self.safety.unload()
            if not scan_res.get('is_safe'):
                 logger.warning("⚠️ Safety Guard flagged content. Proceeding with caution.")
        else:
            logger.info("⏭️ Stage 3: SKIPPED (user disabled)")
        
        # Stage 4: The Brain (ASR)
        if self.is_stage_enabled('4'):
            logger.info("🧠 Stage 4: Transcription")
            text_result = self.glm.transcribe(polished)
            # Handle dict or list return
            if isinstance(text_result, dict):
                segments = text_result.get('segments', [])
            elif isinstance(text_result, list):
                segments = text_result
            else:
                segments = [{'text': str(text_result), 'start': 0, 'end': 0}]
            stages['step4'] = segments
            self.glm.unload()
        else:
            logger.info("⏭️ Stage 4: SKIPPED (user disabled)")
            segments = [{'text': 'No transcription', 'start': 0, 'end': 0}]
        
        # Stage 5: The Eyes (Vision)
        if self.is_stage_enabled('5'):
            logger.info("👁️ Stage 5: Analyzing video frames for gender context")
            try:
                self.vision.load()
                segments = self.vision.analyze_gender(video_path, segments)
                self.vision.unload()
                logger.info("✅ Vision analysis complete")
            except Exception as e:
                logger.warning(f"Vision stage failed (continuing): {e}")
        else:
            logger.info("⏭️ Stage 5: SKIPPED (user disabled)")
        
        # Stage 6: The Logic (LLM Translation)
        if self.is_stage_enabled('6'):
            logger.info("🤔 Stage 6: Translation and timing")
            translated_script = self.deepseek.process_script(segments)
        else:
            logger.info("⏭️ Stage 6: SKIPPED (user disabled)")
            translated_script = segments
        
        # Stage 7: The Mouth (F5-TTS)
        if self.is_stage_enabled('7'):
            logger.info("👄 Stage 7: Text-to-Speech synthesis")
            combined_text = " ".join([s.get('text', '') for s in translated_script])
            tts_output = os.path.join(self.work_dir, "tts_output.wav")
            tts_raw = self.f5.generate(combined_text, polished, output_file=tts_output)
            current_audio = tts_raw
            self.f5.unload()
        else:
            logger.info("⏭️ Stage 7: SKIPPED (user disabled)")
            tts_raw = current_audio
        
        # Stage 7.5: The FX (Humanizer)
        if self.is_stage_enabled('7.5'):
            logger.info("🎭 Stage 7.5: Applying emotional effects (Chatterbox)")
            try:
                self.chatterbox.load()
                script_text = " ".join([s.get('text', '') for s in segments])
                tts_with_fx = self.chatterbox.apply_effects(tts_raw, script_text)
                current_audio = tts_with_fx
                self.chatterbox.unload()
                logger.info("✅ FX applied")
            except Exception as e:
                logger.warning(f"FX stage failed (continuing): {e}")
                tts_with_fx = tts_raw
        else:
            logger.info("⏭️ Stage 7.5: SKIPPED (user disabled)")
            tts_with_fx = tts_raw
        
        # Stage 8: The Skin (RVC Voice Cloning)
        if self.is_stage_enabled('8'):
            logger.info("🎨 Stage 8: Voice cloning")
            cloned_output = os.path.join(self.work_dir, "cloned.wav")
            cloned = self.applio.apply_skin(tts_with_fx, output_audio=cloned_output)
            current_audio = cloned
            self.applio.unload()
        else:
            logger.info("⏭️ Stage 8: SKIPPED (user disabled)")
            cloned = tts_with_fx
        
        # Stage 9: The Renderer (BigVGAN Vocoder)
        if self.is_stage_enabled('9'):
            logger.info("🎛️ Stage 9: Final rendering")
            final = self.bigvgan.render(cloned, os.path.join(self.work_dir, "final_master.wav"))
            self.bigvgan.unload()
        else:
            logger.info("⏭️ Stage 9: SKIPPED (user disabled)")
            final = cloned
        
        logger.info("🏆 HOLLYWOOD MODE COMPLETE (10 STAGES)")
        return final
