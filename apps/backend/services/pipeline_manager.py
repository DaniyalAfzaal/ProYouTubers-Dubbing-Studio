import logging
import os
import subprocess
from typing import Literal

# Import Stages
from apps.backend.services.separation.roformer_runner import RoformerRunner
from apps.backend.services.enhancement.resemble_runner import ResembleRunner
from apps.backend.services.vad.silero_v6_runner import SileroV6Runner
from apps.backend.services.safety.age_gender_scanner import SafetyScanner
from apps.backend.services.asr.glm_runner import GLMASRRunner
from apps.backend.services.vision.glm_vision_runner import GLMVisionRunner
from apps.backend.services.llm.deepseek_runner import DeepSeekRunner
from apps.backend.services.tts.f5_runner import F5TTSRunner
from apps.backend.services.tts.kokoro_runner import KokoroRunner
from apps.backend.services.fx.chatterbox_runner import ChatterboxRunner
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
        self.vision = GLMVisionRunner()
        self.deepseek = DeepSeekRunner()
        self.f5 = F5TTSRunner()
        self.kokoro = KokoroRunner()
        self.chatterbox = ChatterboxRunner()
        self.applio = ApplioRunner()
        self.bigvgan = BigVGANRunner()
    
    def is_stage_enabled(self, stage_id: str) -> bool:
        """Check if a stage is enabled in user configuration."""
        return self.stages_enabled.get(f'stage{stage_id}', True)  # Default: enabled
    
    def extract_audio(self, video_path: str, output_path: str) -> str:
        """Extract audio from video using ffmpeg."""
        try:
            logger.info(f"🎵 Extracting audio from {video_path}")
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz for ASR
                '-ac', '1',  # Mono
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"✅ Audio extracted to {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            # Fallback: assume input is already audio
            return video_path
        except FileNotFoundError:
            logger.warning("FFmpeg not found, assuming input is audio")
            return video_path

    def run_draft(self, video_path: str):
        """
        Mode A: Speed Run (Check Timing)
        Stack: Audio Extract -> Silero -> GLM -> DeepSeek -> Kokoro
        """
        logger.info("🏎️ STARTING DRAFT MODE PIPELINE")
        
        # 1. Extract Audio
        raw_audio = os.path.join(self.work_dir, "raw_audio.wav")
        raw_audio = self.extract_audio(video_path, raw_audio)
        
        # 2. VAD
        if self.is_stage_enabled('2'):
            logger.info("👂 VAD: Detecting speech segments")
            self.silero.process(raw_audio)
            self.silero.unload()
        
        # 3. ASR
        if self.is_stage_enabled('4'):
            logger.info("🧠 ASR: Transcribing")
            transcript_result = self.glm.transcribe(raw_audio)
            transcript = transcript_result if isinstance(transcript_result, dict) else {'text': str(transcript_result)}
            self.glm.unload()
        else:
            transcript = {'text': 'Draft mode transcription skipped'}
        
        # 4. LLM Translation
        if self.is_stage_enabled('6'):
            logger.info("🤔 Translation")
            segments = transcript.get('segments', [{'text': transcript.get('text', '')}])
            translated = self.deepseek.process_script(segments)
        else:
            translated = transcript.get('segments', [{'text': transcript.get('text', '')}])
        
        # 5. TTS (Kokoro - Fast)
        if self.is_stage_enabled('7'):
            logger.info("🗣️ TTS: Generating speech (Kokoro)")
            combined_text = " ".join([s.get('text', '') for s in translated])
            output_path = os.path.join(self.work_dir, "draft_output.wav")
            out_audio = self.kokoro.generate(combined_text, output_file=output_path)
            self.kokoro.unload()
        else:
            out_audio = raw_audio
        
        logger.info("🏁 Draft Mode Complete")
        
        # Validation
        if not out_audio or not os.path.exists(out_audio):
            logger.error("Draft mode failed to produce output!")
            return raw_audio  # Fallback
        
        return out_audio

    def run_hollywood(self, video_path: str):
        """
        Mode B: Hollywood Render (Max Fidelity)
        Stack: Roformer → Resemble → Siler → Guard → GLM → Eyes → DeepSeek → F5 → FX → Applio → BigVGAN
        SEQUENTIAL EXECUTION to save VRAM.
        """
        logger.info("🎬 STARTING HOLLYWOOD MODE PIPELINE (10 STAGES)")
        
        # Track current audio through pipeline
        current_audio = video_path
        segments = []
        enabled_stages = 0
        
        # Stage 1: The Surgeon
        if self.is_stage_enabled('1'):
            logger.info("🔪 Stage 1: Isolating vocals")
            try:
                vocals, inst = self.roformer.separate(video_path, self.work_dir)
                current_audio = vocals
                self.roformer.unload()
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 1 failed: {e}, using original")
                current_audio = video_path
        else:
            logger.info("⏭️ Stage 1: SKIPPED (user disabled)")
        
        # Stage 1.5: The Polisher
        if self.is_stage_enabled('1.5'):
            logger.info("✨ Stage 1.5: Enhancing audio quality")
            try:
                polished_path = os.path.join(self.work_dir, "polished.wav")
                polished = self.resemble.polish(current_audio, polished_path)
                current_audio = polished
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 1.5 failed: {e}, using previous")
        else:
            logger.info("⏭️ Stage 1.5: SKIPPED (user disabled)")
        
        # Stage 2: The Ears (VAD)
        if self.is_stage_enabled('2'):
            logger.info("👂 Stage 2: Voice Activity Detection")
            try:
                speech_timestamps = self.silero.process(current_audio)
                self.silero.unload()
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 2 failed: {e}")
        else:
            logger.info("⏭️ Stage 2: SKIPPED (user disabled)")
        
        # Stage 3: The Guard (Safety)
        if self.is_stage_enabled('3'):
            logger.info("🛡️ Stage 3: Safety check")
            try:
                scan_res = self.safety.scan(current_audio, 16000)
                self.safety.unload()
                if not scan_res.get('is_safe'):
                     logger.warning("⚠️ Safety Guard flagged content")
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 3 failed: {e}")
        else:
            logger.info("⏭️ Stage 3: SKIPPED (user disabled)")
        
        # Stage 4: The Brain (ASR)
        if self.is_stage_enabled('4'):
            logger.info("🧠 Stage 4: Transcription")
            try:
                text_result = self.glm.transcribe(current_audio)
                if isinstance(text_result, dict):
                    segments = text_result.get('segments', [])
                elif isinstance(text_result, list):
                    segments = text_result
                else:
                    segments = [{'text': str(text_result), 'start': 0, 'end': 0}]
                self.glm.unload()
                enabled_stages += 1
            except Exception as e:
                logger.error(f"Stage 4 critical failure: {e}")
                segments = [{'text': '', 'start': 0, 'end': 0}]
        else:
            logger.info("⏭️ Stage 4: SKIPPED (user disabled)")
            segments = [{'text': 'Transcription skipped', 'start': 0, 'end': 0}]
        
        # Stage 5: The Eyes (Vision)
        if self.is_stage_enabled('5'):
            logger.info("👁️ Stage 5: Analyzing video frames")
            try:
                self.vision.load()
                segments = self.vision.analyze_gender(video_path, segments)
                self.vision.unload()
                logger.info("✅ Vision analysis complete")
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Vision stage failed: {e}")
        else:
            logger.info("⏭️ Stage 5: SKIPPED (user disabled)")
        
        # Stage 6: The Logic (LLM Translation)
        if self.is_stage_enabled('6'):
            logger.info("🤔 Stage 6: Translation and timing")
            try:
                translated_script = self.deepseek.process_script(segments)
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 6 failed: {e}, using original")
                translated_script = segments
        else:
            logger.info("⏭️ Stage 6: SKIPPED (user disabled)")
            translated_script = segments
        
        # Stage 7: The Mouth (F5-TTS)
        if self.is_stage_enabled('7'):
            logger.info("👄 Stage 7: Text-to-Speech synthesis")
            try:
                combined_text = " ".join([s.get('text', '') for s in translated_script])
                tts_output = os.path.join(self.work_dir, "tts_output.wav")
                # Extract reference text from first segment for better voice matching
                ref_text = segments[0].get('text', '')[:100] if segments else ""
                tts_raw = self.f5.generate(
                    text=combined_text,
                    ref_audio=current_audio,
                    ref_text=ref_text,
                    output_file=tts_output
                )
                current_audio = tts_raw
                self.f5.unload()
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 7 failed: {e}, keeping previous audio")
        else:
            logger.info("⏭️ Stage 7: SKIPPED (user disabled)")
        
        # Stage 7.5: The FX (Humanizer)
        if self.is_stage_enabled('7.5'):
            logger.info("🎭 Stage 7.5: Applying emotional effects")
            try:
                self.chatterbox.load()
                script_text = " ".join([s.get('text', '') for s in segments])
                tts_with_fx = self.chatterbox.apply_effects(current_audio, script_text)
                current_audio = tts_with_fx
                self.chatterbox.unload()
                logger.info("✅ FX applied")
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"FX stage failed: {e}")
        else:
            logger.info("⏭️ Stage 7.5: SKIPPED (user disabled)")
        
        # Stage 8: The Skin (RVC Voice Cloning)
        if self.is_stage_enabled('8'):
            logger.info("🎨 Stage 8: Voice cloning")
            try:
                cloned_output = os.path.join(self.work_dir, "cloned.wav")
                cloned = self.applio.apply_skin(current_audio, output_audio=cloned_output)
                current_audio = cloned
                self.applio.unload()
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 8 failed: {e}")
        else:
            logger.info("⏭️ Stage 8: SKIPPED (user disabled)")
        
        # Stage 9: The Renderer (BigVGAN Vocoder)
        if self.is_stage_enabled('9'):
            logger.info("🎛️ Stage 9: Final rendering")
            try:
                final_path = os.path.join(self.work_dir, "final_master.wav")
                final = self.bigvgan.render(current_audio, final_path)
                current_audio = final
                self.bigvgan.unload()
                enabled_stages += 1
            except Exception as e:
                logger.warning(f"Stage 9 failed: {e}, using previous")
        else:
            logger.info("⏭️ Stage 9: SKIPPED (user disabled)")
        
        logger.info(f"🏆 HOLLYWOOD MODE COMPLETE ({enabled_stages}/10 stages executed)")
        
        # Final validation
        if not current_audio or not os.path.exists(current_audio):
            logger.error("Hollywood pipeline failed to produce valid output!")
            logger.error(f"Last known audio path: {current_audio}")
            # Return input as absolute fallback
            return video_path
        
        return current_audio
