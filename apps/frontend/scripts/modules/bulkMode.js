// ============================================
// BULK DUBBING MODE HANDLERS
// ============================================

import { toast } from './toast.js';
import { downloads } from './downloads.js';

export const bulkMode = {
    currentBatchId: null,
    pollInterval: null,
    pollErrorCount: 0,
    videoItemsCache: new Map(),

    init() {
        this.setupModeToggle();
        this.setupFileHandlers();
        this.setupSubmitHandler();

        // FIX: Add cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }
        });
    },

    setupModeToggle() {
        const radios = document.querySelectorAll('[name="processing-mode"]');
        const singleInputs = document.getElementById('single-mode-inputs');
        const bulkInputs = document.getElementById('bulk-mode-inputs');
        const submitBtn = document.querySelector('button[type="submit"]');

        radios.forEach(radio => {
            radio.addEventListener('change', () => {
                // Disable mode switching if currently processing
                if (submitBtn.disabled) return;

                if (radio.value === 'bulk') {
                    singleInputs.hidden = true;
                    bulkInputs.hidden = false;
                    submitBtn.textContent = '🚀 Start Bulk Dubbing';
                } else {
                    singleInputs.hidden = false;
                    bulkInputs.hidden = true;
                    submitBtn.textContent = 'Run dubbing pipeline';
                }
            });
        });
    },

    setupFileHandlers() {
        const bulkFiles = document.getElementById('bulk-files');
        const bulkUrls = document.getElementById('bulk-urls');

        if (bulkFiles) {
            bulkFiles.addEventListener('change', (e) => {
                const count = e.target.files.length;
                const countEl = document.getElementById('bulk-file-count');
                if (countEl) {
                    countEl.textContent = count > 0 ?
                        `✅ ${count} file${count > 1 ? 's' : ''} selected` : '';
                }
            });
        }

        if (bulkUrls) {
            bulkUrls.addEventListener('input', (e) => {
                const urls = e.target.value.split('\n').filter(u => u.trim());
                const countEl = document.getElementById('bulk-url-count');
                if (countEl) {
                    countEl.textContent = urls.length > 0 ?
                        `✅ ${urls.length} URL${urls.length > 1 ? 's' : ''}` : '';
                }
            });
        }
    },

    setupSubmitHandler() {
        const form = document.getElementById('dub-form');

        // Store reference to any existing listeners via event capture
        let originalHandler = null;
        const listeners = [];

        // Capture current onsubmit if exists
        if (form.onsubmit) {
            originalHandler = form.onsubmit;
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            e.stopPropagation();

            const mode = document.querySelector('[name="processing-mode"]:checked')?.value;

            if (mode === 'bulk') {
                await this.submitBulkDubbing();
            } else if (originalHandler) {
                // Call original handler if it exists
                originalHandler.call(form, e);
            }
        }, { capture: true });
    },

    async submitBulkDubbing() {
        const formData = new FormData();

        // Get bulk files
        const filesInput = document.getElementById('bulk-files');
        if (filesInput?.files) {
            for (let file of filesInput.files) {
                formData.append('files', file);
            }
        }

        // Get bulk URLs
        const urlsText = document.getElementById('bulk-urls')?.value;
        if (urlsText?.trim()) {
            formData.append('urls', urlsText);
        }

        // Validate we have something
        if (!filesInput?.files?.length && !urlsText?.trim()) {
            toast.warning('Please select files or enter URLs');
            return;
        }

        // FIX: Frontend validation for max 100 videos
        const totalVideos = (filesInput?.files?.length || 0) + (urlsText ? urlsText.split('\n').filter(u => u.trim()).length : 0);
        if (totalVideos > 100) {
            toast.error('Maximum 100 videos allowed per batch');
            return;
        }

        // Disable mode toggle during submission
        const modeRadios = document.querySelectorAll('[name="processing-mode"]');
        modeRadios.forEach(r => r.disabled = true);

        // Add all other form options (same as single mode)
        const dubForm = document.getElementById('dub-form');
        const singleFormData = new FormData(dubForm);
        for (let [key, value] of singleFormData.entries()) {
            if (key !== 'file' && key !== 'video_url' && key !== 'reuse_media_token') {
                formData.append(key, value);
            }
        }

        try {
            // Disable submit button
            const submitBtn = document.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Starting batch...';

            const response = await fetch('/api/jobs/bulk-run', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.statusText}`);
            }

            const result = await response.json();

            // Show progress UI
            document.getElementById('bulk-progress').hidden = false;
            document.getElementById('bulk-total').textContent = result.total;
            document.getElementById('bulk-queued').textContent = result.total;

            // Reset input counts
            document.getElementById('bulk-file-count').textContent = '';
            document.getElementById('bulk-url-count').textContent = '';
            filesInput.value = '';
            document.getElementById('bulk-urls').value = '';

            // Re-enable button and mode toggle
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Start Bulk Dubbing';
            modeRadios.forEach(r => r.disabled = false);

            toast.success(`Batch started! Processing ${result.total} videos`);

            // Start polling for updates
            this.currentBatchId = result.batch_id;
            this.startPolling(result.batch_id);

        } catch (error) {
            console.error('Bulk dubbing error:', error);
            toast.error(`Failed to start bulk dubbing: ${error.message}`);

            const submitBtn = document.querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Start Bulk Dubbing';
            const modeRadios = document.querySelectorAll('[name="processing-mode"]');
            modeRadios.forEach(r => r.disabled = false);
        }
    },

    startPolling(batchId) {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        // FIX: Reset error count BEFORE starting interval
        this.pollErrorCount = 0;

        this.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/jobs/bulk-status/${batchId}`);
                if (!resp.ok) {
                    throw new Error('Status fetch failed');
                }

                const data = await resp.json();

                // FIX: Reset error count on success
                this.pollErrorCount = 0;

                this.updateProgress(data);

                // Stop when complete
                if (data.completed + data.failed >= data.total) {
                    clearInterval(this.pollInterval);
                    this.pollInterval = null;
                }
            } catch (error) {
                console.error('Polling error:', error);
                // FIX: Stop polling after 5 consecutive failures
                this.pollErrorCount = (this.pollErrorCount || 0) + 1;
                if (this.pollErrorCount >= 5) {
                    clearInterval(this.pollInterval);
                    this.pollInterval = null;
                    console.error('Stopped polling after 5 failures');
                }
            }
        }, 2000); // Poll every 2 seconds
    },

    updateProgress(data) {
        // FIX: Add fallback values for undefined data
        document.getElementById('bulk-completed').textContent = data.completed || 0;
        document.getElementById('bulk-processing').textContent = data.processing || 0;
        document.getElementById('bulk-queued').textContent = data.queued || 0;
        document.getElementById('bulk-failed').textContent = data.failed || 0;

        // FIX: Prevent divide by zero
        const progress = (data.total && data.total > 0) ?
            ((data.completed + data.failed) / data.total) * 100 : 0;
        document.getElementById('bulk-progress-bar').style.width = `${progress}%`;

        // Update video list
        this.updateVideoList(data.videos);
    },

    updateVideoList(videos) {
        const list = document.getElementById('bulk-video-list');
        if (!list) return;

        // Optimized: Update only changed items instead of full rebuild
        videos.forEach((video, index) => {
            const videoKey = `${this.currentBatchId}-${index}`;
            const cached = this.videoItemsCache.get(videoKey);

            // Check if we need to update this item
            const videoStr = JSON.stringify(video);
            if (cached && cached.data === videoStr) {
                return; // No change, skip
            }

            // Get or create element
            let item = cached?.element;
            if (!item) {
                item = document.createElement('div');
                list.appendChild(item);
            }

            item.className = `video-item ${video.status}`;

            let content = `
                <h4>${this.escapeHtml(video.name)}</h4>
                <span class="status">${video.status}</span>
            `;

            if (video.error) {
                content += `<div class="error">${this.escapeHtml(video.error)}</div>`;
            }

            if (video.result && video.result.video_url) {
                content += `<a href="${this.escapeHtml(video.result.video_url)}" class="download-link" download>⬇️ Download</a>`;

                // Save to downloads manager when completed
                if (video.status === 'completed' && !cached?.saved) {
                    downloads.saveProcess({
                        name: video.name,
                        timestamp: Date.now(),
                        source: video.name,
                        languages: 'Bulk Dubbing',
                        videoUrl: video.result.video_url,
                        logs: `Bulk dubbing completed successfully`
                    });
                    this.videoItemsCache.set(videoKey, {
                        element: item,
                        data: videoStr,
                        saved: true
                    });
                } else {
                    this.videoItemsCache.set(videoKey, {
                        element: item,
                        data: videoStr,
                        saved: cached?.saved || false
                    });
                }
            } else {
                this.videoItemsCache.set(videoKey, {
                    element: item,
                    data: videoStr,
                    saved: false
                });
            }

            item.innerHTML = content;
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
