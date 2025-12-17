// God Tier Advanced Controls Module
export const godTierControls = {
    stagesConfig: [
        {
            id: 1, name: 'The Surgeon', desc: 'Isolation', models: [
                { value: 'bs_roformer_revive', label: 'BS-Roformer-Revive (Bleedless)' },
                { value: 'viperx_1297', label: 'Viperx-1297 (Backup)' }
            ], hint: 'Isolates vocals from background music/noise', defaultEnabled: true
        },

        {
            id: '1.5', name: 'The Polisher', desc: 'Enhancement', models: null,
            hint: 'Upscales audio to studio quality (Resemble Enhance)', defaultEnabled: true
        },

        {
            id: 2, name: 'The Ears', desc: 'VAD', models: [
                { value: 'silero_v6', label: 'Silero VAD v6.2 (Baby Filter)' },
                { value: 'funasr', label: 'FunASR-FSMN (Sensitive)' }
            ], hint: 'Voice Activity Detection with baby cry filtering', defaultEnabled: true
        },

        {
            id: 3, name: 'The Guard', desc: 'Safety', models: null,
            hint: 'Auto-discard segments with Age < 10 (Audeering)', defaultEnabled: false
        },

        {
            id: 4, name: 'The Brain', desc: 'ASR', models: [
                { value: 'glm_asr_nano', label: 'GLM-ASR-Nano (No Hallucination)' },
                { value: 'nvidia_canary', label: 'NVIDIA Canary-Qwen (Accents)' }
            ], hint: 'Speech recognition optimized for dialects', defaultEnabled: true
        },

        {
            id: 5, name: 'The Eyes', desc: 'Vision', models: null,
            hint: 'Analyze video frames to fix gender pronouns (GLM-4.6V-Flash)', defaultEnabled: true
        },

        {
            id: 6, name: 'The Logic', desc: 'LLM Translation', models: [
                { value: 'deepseek_v3', label: 'DeepSeek-V3 (Reasoning)' },
                { value: 'qwen3_drama', label: 'Qwen3-Drama-8B (Emotional)' }
            ], hint: 'Time-synced translation with emotional subtext', defaultEnabled: true
        },

        {
            id: 7, name: 'The Mouth', desc: 'TTS', models: [
                { value: 'f5_tts', label: 'F5-TTS (Flow Matching - Hollywood)' },
                { value: 'kokoro_82m', label: 'Kokoro-82M (ONNX - Draft)' }
            ], hint: 'Text-to-Speech synthesis', defaultEnabled: true
        },

        {
            id: '7.5', name: 'The FX', desc: 'Humanizer', models: null,
            hint: 'Insert [laugh], [sigh] emotional effects (Chatterbox-Turbo)', defaultEnabled: false
        },

        {
            id: 8, name: 'The Skin', desc: 'Voice Cloning', models: null,
            hint: 'Applies original speaker\'s timbre via RVC (Applio)', defaultEnabled: true
        },

        {
            id: 9, name: 'The Renderer', desc: 'Vocoder', models: [
                { value: 'bigvgan_v2', label: 'BigVGAN v2 (Fidelity)' },
                { value: 'hifigan', label: 'HiFi-GAN (Low VRAM)' }
            ], hint: 'Final audio synthesis, removes metallic artifacts', defaultEnabled: true
        }
    ],

    init() {
        this.renderStages();
        this.setupVisibilityToggle();
        this.setupPresets();
    },

    renderStages() {
        const container = document.getElementById('god-tier-stages-container');
        if (!container) return;

        container.innerHTML = this.stagesConfig.map(stage => `
            <div class="stage-control">
                <div class="stage-header">
                    <label class="checkbox-row stage-toggle">
                        <input type="checkbox" 
                               id="stage${stage.id}-enabled" 
                               name="stage${stage.id}_enabled" 
                               ${stage.defaultEnabled ? 'checked' : ''}>
                        <strong>Stage ${stage.id}: ${stage.name} (${stage.desc})</strong>
                    </label>
                </div>
                <div class="stage-options">
                    ${stage.models ? `
                        <label>
                            Model
                            <select name="stage${stage.id}_model" id="stage${stage.id}-model">
                                ${stage.models.map(m =>
            `<option value="${m.value}">${m.label}</option>`
        ).join('')}
                            </select>
                        </label>
                    ` : ''}
                    <small class="hint-text">${stage.hint}</small>
                </div>
            </div>
        `).join('');
    },

    setupVisibilityToggle() {
        const dubbingStrategy = document.getElementById('dubbing-strategy');
        const controlsPanel = document.getElementById('god-tier-controls');

        if (!dubbingStrategy || !controlsPanel) return;

        dubbingStrategy.addEventListener('change', () => {
            const val = dubbingStrategy.value;
            if (val === 'god_tier_draft' || val === 'god_tier_hollywood') {
                controlsPanel.style.display = 'block';
            } else {
                controlsPanel.style.display = 'none';
            }
        });
    },

    setupPresets() {
        const presetFull = document.getElementById('preset-full');
        const presetEssential = document.getElementById('preset-essential');
        const presetQuality = document.getElementById('preset-quality');

        if (presetFull) {
            presetFull.addEventListener('click', () => {
                this.applyPreset('full');
            });
        }

        if (presetEssential) {
            presetEssential.addEventListener('click', () => {
                this.applyPreset('essential');
            });
        }

        if (presetQuality) {
            presetQuality.addEventListener('click', () => {
                this.applyPreset('quality');
            });
        }
    },

    applyPreset(presetName) {
        const presets = {
            full: [1, '1.5', 2, 3, 4, 5, 6, 7, '7.5', 8, 9], // All 11 stages
            essential: [1, 2, 4, 6, 7], // Core only: Surgeon, VAD, ASR, LLM, TTS
            quality: [1, '1.5', 2, 4, 5, 6, 7, '7.5', 8, 9] // Skip Safety only
        };

        const enabledStages = presets[presetName] || [];

        this.stagesConfig.forEach(stage => {
            const checkbox = document.getElementById(`stage${stage.id}-enabled`);
            if (checkbox) {
                checkbox.checked = enabledStages.includes(stage.id);
            }
        });

        // Visual feedback
        const messages = {
            full: '🎬 All 11 stages enabled (Maximum Quality)',
            essential: '⚡ Core 5 stages (Speed Mode)',
            quality: '✨ 10 stages (Premium Quality, no Safety filter)'
        };

        console.log(`✨ Preset applied: ${messages[presetName]}`);
    },

    getConfig() {
        // Returns current stage configuration for backend
        const config = {
            stages_enabled: {},
            stage_models: {}
        };

        this.stagesConfig.forEach(stage => {
            const checkbox = document.getElementById(`stage${stage.id}-enabled`);
            const select = document.getElementById(`stage${stage.id}-model`);

            config.stages_enabled[`stage${stage.id}`] = checkbox ? checkbox.checked : false;

            if (select && checkbox?.checked) {
                config.stage_models[`stage${stage.id}`] = select.value;
            }
        });

        return config;
    }
};
