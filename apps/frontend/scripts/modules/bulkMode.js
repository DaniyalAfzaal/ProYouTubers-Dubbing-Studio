// ============================================
// BULK DUBBING MODE HANDLERS
// ============================================

import { toast } from './toast.js';
import { downloads } from './downloads.js';

export const bulkMode = {
    currentBatchId: null,
    pollInterval: null,
    pollErrorCount: 0,
    maxPollErrors: 5,
    videoItemsCache: new Map(),
    pollDelay: 2000,
    savedDownloads: new Set(), // Track which videos have been saved to downloads
    saveMutex: new Set(), // Prevent race conditions when saving

    init() {
        this.setupModeToggle();
        this.setupFileHandlers();
        this.setupBulkTargetLangs();  // FIX Bug #15: Add bulk target lang setup
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

        // Debug: Log what we found
        console.log('BulkMode: Setting up mode toggle');
        console.log('BulkMode: Found', radios.length, 'radio buttons');
        console.log('BulkMode: singleInputs =', singleInputs);
        console.log('BulkMode: bulkInputs =', bulkInputs);

        // Safety check
        if (!singleInputs || !bulkInputs) {
            console.error('BulkMode: Could not find required input containers!');
            return;
        }

        // FIX: Set initial state - single mode visible, bulk hidden
        singleInputs.style.display = 'block';
        bulkInputs.style.display = 'none';
        bulkInputs.hidden = true;

        radios.forEach(radio => {
            radio.addEventListener('change', () => {
                console.log('BulkMode: Radio changed to', radio.value);

                // Disable mode switching if currently processing
                if (this.currentBatchId && this.pollInterval) {
                    console.warn('BulkMode: Cannot switch modes while processing');
                    // Revert radio selection
                    radios.forEach(r => r.checked = (r.value !== radio.value));
                    return;
                }

                // FIX: Toggle visibility based on selected mode
                if (radio.value === 'bulk') {
                    // Bulk mode selected
                    singleInputs.style.display = 'none';
                    singleInputs.hidden = true;
                    bulkInputs.style.display = 'block';
                    bulkInputs.hidden = false;
                    if (submitBtn) submitBtn.textContent = '🚀 Start Bulk Dubbing';
                    console.log('BulkMode: Switched to BULK mode');
                } else {
                    // Single mode selected
                    singleInputs.style.display = 'block';
                    singleInputs.hidden = false;
                    bulkInputs.style.display = 'none';
                    bulkInputs.hidden = true;
                    if (submitBtn) submitBtn.textContent = '🚀 Start Dubbing';
                    console.log('BulkMode: Switched to SINGLE mode');
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

    // FIX Bug #15: Setup bulk target language tag input
    setupBulkTargetLangs() {
        const input = document.getElementById('bulk-target-lang-input');
        const tagsContainer = document.getElementById('bulk-target-lang-tags');

        if (!input || !tagsContainer) {
            console.warn('BulkMode: Bulk target lang elements not found');
            return;
        }

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const value = input.value.trim();

                if (value) {
                    // FIX: Capitalize first letter for proper display
                    const capitalized = value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();

                    // Check if already added
                    const existing = Array.from(tagsContainer.querySelectorAll('.tag-badge'))
                        .find(tag => tag.querySelector('span').textContent.toLowerCase() === value.toLowerCase());

                    if (!existing) {
                        this.addBulkTargetLangTag(capitalized);
                    }
                    input.value = '';
                }
            }
        });
    },

    addBulkTargetLangTag(code) {
        const tagsContainer = document.getElementById('bulk-target-lang-tags');
        if (!tagsContainer) return;

        const tag = document.createElement('span');
        tag.className = 'tag-badge'; // FIX: Use 'tag-badge' class for consistent styling
        const display = document.createElement('span');
        display.textContent = code;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'tag-remove';
        removeBtn.setAttribute('aria-label', `Remove ${code}`);
        removeBtn.textContent = '×';
        removeBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            tag.remove();
        };

        // FIX: Add hidden input for form submission
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'bulk_target_langs';
        hidden.value = code.toLowerCase(); // Store lowercase code

        tag.appendChild(display);
        tag.appendChild(removeBtn);
        tag.appendChild(hidden);
        tagsContainer.appendChild(tag);
    },

    setupSubmitHandler() {
        const form = document.getElementById('dub-form');

        // Listen for form submission, only intercept bulk mode
        form.addEventListener('submit', async (e) => {
            const mode = document.querySelector('[name="processing-mode"]:checked')?.value;

            // Only handle bulk mode here
            if (mode === 'bulk') {
                e.preventDefault();
                e.stopPropagation();
                await this.submitBulkDubbing();
            }
            // For single mode: do nothing, let the original form.onsubmit handler in app.js work
        });
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

        // FIX Bug #5: Add all form options (including model selections)
        const dubForm = document.getElementById('dub-form');
        const singleFormData = new FormData(dubForm);

        // FIX Bug #18: Get target languages from BULK tag input (using correct selector)
        const targetLangs = Array.from(document.querySelectorAll('#bulk-target-lang-tags .tag-badge'))
            .map(tag => {
                const hiddenInput = tag.querySelector('input[type="hidden"]');
                return hiddenInput ? hiddenInput.value : '';
            })
            .filter(code => code)
            .join(',');

        if (!targetLangs) {
            toast.error('Please add at least one target language in bulk mode');
            modeRadios.forEach(r => r.disabled = false);
            return;
        }

        formData.append('target_langs', targetLangs);

        // Get bulk-specific task and source language
        const bulkTask = document.getElementById('bulk-task')?.value || 'dub';
        const bulkSourceLang = document.getElementById('bulk-source-lang')?.value || 'auto';

        formData.append('target_work', bulkTask);
        formData.append('source_lang', bulkSourceLang);

        // Copy all form fields to bulk FormData
        for (let [key, value] of singleFormData.entries()) {
            // Skip fields that shouldn't be in bulk submission
            if (key !== 'file' &&
                key !== 'video_url' &&
                key !== 'reuse_media_token' &&
                key !== 'processing-mode' &&
                key !== 'target_lang' &&  // Skip the tag input field itself
                !key.startsWith('target_')) {  // Skip other target_ fields
                formData.append(key, value);
            }
        }

        try {
            // Disable submit button
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '⏳ Starting batch...';
            }

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
            document.getElementById('batch-total').textContent = result.total;
            document.getElementById('batch-queued').textContent = result.total;

            // Reset input counts
            document.getElementById('bulk-file-count').textContent = '';
            document.getElementById('bulk-url-count').textContent = '';
            filesInput.value = '';
            document.getElementById('bulk-urls').value = '';

            // Re-enable button and mode toggle
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Start Bulk Dubbing';
            }
            modeRadios.forEach(r => r.disabled = false);

            toast.success(`Batch started! Processing ${result.total} videos`);

            // Start polling for updates
            this.currentBatchId = result.batch_id;
            this.startPolling(result.batch_id);

        } catch (error) {
            console.error('Failed to start bulk dubbing:', error);



            toast.error(`Failed to start bulk dubbing: ${error.message}`);


            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Start Bulk Dubbing';
            }
            const modeRadios = document.querySelectorAll('[name="processing-mode"]');
            modeRadios.forEach(r => r.disabled = false);
        }
    },

    startPolling(batchId) {
        // FIX: Prevent race condition - clear existing interval first
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }

        // FIX: Clear cache for new batch to prevent memory leak
        this.videoItemsCache.clear();

        // Reset error count BEFORE starting interval
        this.pollErrorCount = 0;

        // Update current batch ID
        this.currentBatchId = batchId;

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
        // Update stats with new IDs
        const setTextIfExists = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        const completed = data.completed || 0;
        const processing = data.processing || 0;
        const failed = data.failed || 0;
        const queued = data.queued || 0;
        const total = data.total || 0;

        setTextIfExists('batch-total', total);
        setTextIfExists('batch-complete', completed);
        setTextIfExists('batch-processing', processing);
        setTextIfExists('batch-failed', failed);
        setTextIfExists('batch-queued', queued);

        // Update progress bar
        const percentage = total > 0 ? Math.round((completed + failed) / total * 100) : 0;
        const fill = document.getElementById('batch-progress-fill');
        const percentText = document.getElementById('batch-percentage');

        if (fill) fill.style.width = `${percentage}%`;
        if (percentText) percentText.textContent = `${percentage}%`;

        // Update video list
        if (data.videos && Array.isArray(data.videos)) {
            this.updateVideoList(data.videos);
        }
    },

    updateVideoList(videos) {
        const list = document.getElementById('bulk-video-list');
        if (!list) return;

        if (!videos || !Array.isArray(videos) || videos.length === 0) {
            list.innerHTML = `
                <div class="batch-empty-state">
                    <div class="icon">📦</div>
                    <p>No videos in queue</p>
                </div>
            `;
            return;
        }

        // Clear list
        list.innerHTML = '';

        videos.forEach((video, index) => {
            const card = this.renderVideoCard(video, index);
            list.appendChild(card);

            // Auto-save completed videos to downloads (if not already saved)
            if ((video.status === 'complete' || video.status === 'completed') &&
                !this.savedDownloads.has(video.name)) {
                this.saveToDownloads(video);
            }

            // Track failed jobs in downloads
            if (video.status === 'failed' && !this.savedDownloads.has(video.name)) {
                if (typeof downloads !== 'undefined' && downloads.saveProcess) {
                    const sanitizeName = (name) => {
                        if (!name || typeof name !== 'string') return 'Video';
                        return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100).trim() || 'Video';
                    };

                    downloads.saveProcess({
                        name: sanitizeName(video.name),
                        timestamp: Date.now(),
                        timestampISO: new Date().toISOString(),
                        source: video.name || 'Unknown',
                        status: 'failed',
                        error: video.error || 'Processing failed',
                        logs: `Bulk mode: ${video.error || 'Unknown error'}`,
                        mode: 'bulk',
                        videoUrl: ''  // Empty but present for validation
                    });
                    this.savedDownloads.add(video.name);
                }
            }
        });
    },

    renderVideoCard(video, index) {
        const card = document.createElement('div');
        card.className = `video-card status-${video.status}`;

        const statusIcons = {
            complete: '✅',
            completed: '✅',
            processing: '⚡',
            failed: '❌',
            queued: '⏸',
            cancelled: '⏹'
        };

        const statusIcon = statusIcons[video.status] || '📝';
        const displayName = video.name.length > 60 ? video.name.substring(0, 57) + '...' : video.name;

        let cardHTML = `
            <div class="video-card-header">
                <span class="video-icon">🎬</span>
                <h4 class="video-name" title="${this.escapeHtml(video.name)}">${this.escapeHtml(displayName)}</h4>
                <span class="video-status ${video.status}">
                    ${statusIcon} ${video.status}
                </span>
            </div>
        `;

        // Add progress bar for processing videos
        if (video.status === 'processing' && video.progress) {
            cardHTML += `
                <div class="video-progress">
                    <div class="video-progress-bar">
                        <div class="video-progress-fill" style="width: ${video.progress}%"></div>
                    </div>
                    <span class="video-progress-text">Processing: ${video.progress}%</span>
                </div>
            `;
        }

        // Add video info if available
        if (video.target_langs || video.status === 'completed') {
            cardHTML += '<div class="video-info">';
            if (video.target_langs) {
                const langs = Array.isArray(video.target_langs)
                    ? video.target_langs.join(', ')
                    : video.target_langs;
                cardHTML += `<div class="info-item"><span>🌐 Languages:</span> ${this.escapeHtml(langs)}</div>`;
            }
            cardHTML += '</div>';
        }

        // Add error message if failed
        if (video.error && video.status === 'failed') {
            cardHTML += `
                <div class="video-error">
                    ⚠️ ${this.escapeHtml(video.error)}
                </div>
            `;
        }

        // Add footer with actions
        cardHTML += '<div class="video-card-footer">';

        // Download button for completed videos
        if ((video.status === 'complete' || video.status === 'completed') && video.result?.video_url) {
            const videoUrl = video.result.video_url;
            cardHTML += `
                <a href="${this.escapeHtml(videoUrl)}" 
                   class="btn-download" 
                   download="${this.escapeHtml(video.name)}">
                    <span class="btn-icon">⬇️</span>
                    Download
                </a>
            `;

            // Save to downloads manager
            if (!this.savedDownloads.has(video.name)) {
                this.saveToDownloads(video);
                this.savedDownloads.add(video.name);
            }
        }

        cardHTML += '</div>';

        card.innerHTML = cardHTML;
        return card;
    },


    saveToDownloads(video) {
        if (typeof downloads === 'undefined' || !downloads.saveProcess) {
            return;
        }

        // Check if already being saved (prevent race condition)
        if (this.saveMutex.has(video.name)) {
            console.log(`Save already in progress for: ${video.name}`);
            return;
        }

        // Lock
        this.saveMutex.add(video.name);

        try {
            // Check localStorage for actual duplicates
            const existing = downloads.getProcesses();
            const isDuplicate = existing.some(p =>
                p.videoUrl === video.result.video_url &&
                p.name === video.name
            );

            if (isDuplicate) {
                console.log(`Skipping duplicate download entry for: ${video.name}`);
                return;
            }

            // Validate video data
            if (!video.result?.video_url) {
                console.warn(`No video URL for: ${video.name}`);
                return;
            }

            // Sanitize name
            const sanitizeName = (name) => {
                if (!name || typeof name !== 'string') return 'Video';
                return name.replace(/[<>:"/\\|?*]/g, '_').substring(0, 100).trim() || 'Video';
            };

            const langs = Array.isArray(video.target_langs)
                ? video.target_langs.join(', ')
                : (video.target_langs || 'Multiple');

            const downloadEntry = {
                name: sanitizeName(video.name),
                timestamp: Date.now(),
                timestampISO: new Date().toISOString(),
                source: video.name || 'Unknown',
                languages: langs,
                videoUrl: video.result.video_url,
                logs: `Bulk dubbing completed successfully for languages: ${langs}`,
                mode: 'bulk',
                status: 'completed'
            };

            const saved = downloads.saveProcess(downloadEntry);

            if (saved) {
                this.savedDownloads.add(video.name);
            } else {
                console.warn(`Failed to save download for: ${video.name}`);
            }
        } catch (error) {
            console.error(`Error saving download for ${video.name}:`, error);
        } finally {
            // Always unlock
            this.saveMutex.delete(video.name);
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
