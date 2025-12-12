// ============================================
// BULK DUBBING MODE HANDLERS
// ============================================

export const bulkMode = {
    currentBatchId: null,
    pollInterval: null,

    init() {
        this.setupModeToggle();
        this.setupFileHandlers();
        this.setupSubmitHandler();
    },

    setupModeToggle() {
        const radios = document.querySelectorAll('[name="processing-mode"]');
        const singleInputs = document.getElementById('single-mode-inputs');
        const bulkInputs = document.getElementById('bulk-mode-inputs');
        const submitBtn = document.querySelector('button[type="submit"]');

        radios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'bulk') {
                    singleInputs.hidden = true;
                    bulkInputs.hidden = false;
                    submitBtn.textContent = '🚀 Start Bulk Dubbing';
                } else {
                    singleInputs.hidden = false;
                    bulkInputs.hidden = true;
                    submitBtn.textContent = 'Start Dubbing';
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
        const originalSubmit = form.onsubmit;

        form.onsubmit = async (e) => {
            e.preventDefault();

            const mode = document.querySelector('[name="processing-mode"]:checked')?.value;

            if (mode === 'bulk') {
                await this.submitBulkDubbing();
            } else {
                // Call original single mode handler
                if (originalSubmit) {
                    originalSubmit.call(form, e);
                }
            }
        };
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
            alert('Please select files or enter URLs');
            return;
        }

        // FIX: Frontend validation for max 100 videos
        const totalVideos = (filesInput?.files?.length || 0) + (urlsText ? urlsText.split('\n').filter(u => u.trim()).length : 0);
        if (totalVideos > 100) {
            alert('Maximum 100 videos allowed per batch');
            return;
        }

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

            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Start Bulk Dubbing';

            // Start polling for updates
            this.currentBatchId = result.batch_id;
            this.startPolling(result.batch_id);

        } catch (error) {
            console.error('Bulk dubbing error:', error);
            alert(`Failed to start bulk dubbing: ${error.message}`);

            const submitBtn = document.querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Start Bulk Dubbing';
        }
    },

    startPolling(batchId) {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/jobs/bulk-status/${batchId}`);
                if (!resp.ok) {
                    throw new Error('Status fetch failed');
                }

                const data = await resp.json();
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

        // FIX: Reset error count on successful start
        this.pollErrorCount = 0;
    },

    updateProgress(data) {
        // Update stats
        document.getElementById('bulk-completed').textContent = data.completed;
        document.getElementById('bulk-processing').textContent = data.processing;
        document.getElementById('bulk-queued').textContent = data.queued;
        document.getElementById('bulk-failed').textContent = data.failed;

        // Update progress bar
        const progress = ((data.completed + data.failed) / data.total) * 100;
        document.getElementById('bulk-progress-bar').style.width = `${progress}%`;

        // Update video list
        this.updateVideoList(data.videos);
    },

    updateVideoList(videos) {
        const list = document.getElementById('bulk-video-list');
        if (!list) return;

        list.innerHTML = '';

        videos.forEach((video, index) => {
            const item = document.createElement('div');
            item.className = `video-item ${video.status}`;

            let content = `
                <h4>${this.escapeHtml(video.name)}</h4>
                <span class="status">${video.status}</span>
            `;

            if (video.error) {
                content += `<div class="error">${this.escapeHtml(video.error)}</div>`;
            }

            if (video.result && video.result.video_url) {
                content += `<a href="${video.result.video_url}" class="download-link" download>⬇️ Download</a>`;
            }

            item.innerHTML = content;
            list.appendChild(item);
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
