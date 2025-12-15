// ============================================
// DOWNLOADS MANAGER
// ============================================

export const downloads = {
    processes: [],

    init() {
        const downloadsBtn = document.getElementById('downloads-btn');
        const closeBtn = document.getElementById('close-downloads');
        const downloadsPage = document.getElementById('downloads-page');

        // FIX: Add null checks for all elements
        if (downloadsBtn && downloadsPage) {
            downloadsBtn.addEventListener('click', () => {
                // Show loading state
                const originalText = downloadsBtn.textContent;
                downloadsBtn.disabled = true;
                downloadsBtn.textContent = 'Loading...';

                // Small delay to show loading feedback
                setTimeout(() => {
                    downloadsPage.hidden = false;
                    this.loadProcesses();
                    downloadsBtn.disabled = false;
                    downloadsBtn.textContent = originalText;
                }, 100);
            });
        }

        if (closeBtn && downloadsPage) {
            closeBtn.addEventListener('click', () => {
                downloadsPage.hidden = true;
            });
        }

        // FIX: Add cleanup on page unload
        window.addEventListener('beforeunload', () => {
            // Cleanup if needed
        });
    },

    loadProcesses() {
        const stored = localStorage.getItem('dubbing_processes');
        // FIX: Wrap JSON.parse in try-catch
        try {
            this.processes = stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Failed to parse processes from localStorage:', e);
            this.processes = [];
            localStorage.removeItem('dubbing_processes');
        }
        this.renderProcessList();
    },

    saveProcess(processData) {
        // FIX: Validate process data structure
        if (!processData || !processData.timestamp || !processData.name) {
            console.error('Invalid process data:', processData);
            return;
        }
        this.processes.unshift(processData);
        if (this.processes.length > 50) this.processes.pop();
        try {
            localStorage.setItem('dubbing_processes', JSON.stringify(this.processes));
        } catch (e) {
            // FIX: Handle quota exceeded error
            if (e.name === 'QuotaExceededError') {
                console.warn('localStorage quota exceeded, removing oldest half');
                this.processes = this.processes.slice(0, 25);
                try {
                    localStorage.setItem('dubbing_processes', JSON.stringify(this.processes));
                } catch (retryError) {
                    console.error('Failed to save even after cleanup:', retryError);
                }
            } else {
                console.error('Failed to save processes to localStorage:', e);
            }
        }
    },

    renderProcessList() {
        const list = document.getElementById('process-list');
        if (!list) return;  // Safety check

        if (this.processes.length === 0) {
            list.innerHTML = `
                <div class="empty-state-beautiful">
                    <div class="empty-icon">📥</div>
                    <h3>No Downloads Yet</h3>
                    <p>Completed dubbing jobs will appear here</p>
                    <div class="quick-tip">
                        <span class="tip-icon">💡</span>
                        <span>Try dubbing a video to get started!</span>
                    </div>
                </div>
            `;
            document.getElementById('download-details').innerHTML = `
                <div class="empty-state-beautiful">
                    <div class="empty-icon">🎬</div>
                    <h3>Select a process to view details</h3>
                    <p>Your download history will show here</p>
                </div>
            `;
            return;
        }

        list.innerHTML = this.processes.map((proc, i) => `
            <div class="process-card${i === 0 ? ' active' : ''}" data-index="${i}">
                <div class="process-header">
                    <div class="process-status">
                        <span class="status-icon">✓</span>
                        <span class="status-text">Completed</span>
                    </div>
                    <button class="delete-btn" data-index="${i}" title="Delete" aria-label="Delete process">
                        <span>🗑️</span>
                    </button>
                </div>
                <div class="process-name">${this.escapeHtml(proc.name || 'Dubbing Process')}</div>
                <div class="process-meta">
                    <span class="meta-item">
                        <span class="meta-icon">🌐</span>
                        ${this.escapeHtml(proc.languages || 'N/A')}
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">⏱️</span>
                        ${this.formatTimeAgo(proc.timestamp)}
                    </span>
                </div>
            </div>
        `).join('');

        // Add click handlers for process cards
        list.querySelectorAll('.process-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking delete button
                if (e.target.closest('.delete-btn')) return;

                list.querySelectorAll('.process-card').forEach(el => el.classList.remove('active'));
                card.classList.add('active');
                this.showProcessDetails(this.processes[parseInt(card.dataset.index)]);
            });
        });

        // Add delete button handlers
        list.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                if (confirm('Delete this process?')) {
                    this.deleteProcess(index);
                }
            });
        });

        if (this.processes.length > 0) {
            this.showProcessDetails(this.processes[0]);
        }
    },

    showProcessDetails(process) {
        const details = document.getElementById('download-details');
        if (!details) return;  // Safety check

        // FIX: Remove inline onclick, use data attributes instead
        details.innerHTML = `
            <div class="download-section">
                <h3>📥 Download Options</h3>
                <div class="download-buttons">
                    <button class="download-btn" data-url="${this.escapeHtml(process.videoUrl || '')}">
                        <span style="font-size:1.5rem">🎬</span>
                        <div>
                            <div>Complete Dubbed Video</div>
                            <small style="opacity:0.8">Exported with audio</small>
                        </div>
                    </button>
                    <button class="download-btn" data-url="${this.escapeHtml(process.audioUrl || '')}">
                        <span style="font-size:1.5rem">🎵</span>
                        <div>
                            <div>Dubbed Audio</div>
                            <small style="opacity:0.8">Time-adjusted</small>
                        </div>
                    </button>
                    <button class="download-btn" data-url="${this.escapeHtml(process.rawAudioUrl || '')}">
                        <span style="font-size:1.5rem">🎤</span>
                        <div>
                            <div>Original Dubbed Audio</div>
                            <small style="opacity:0.8">No timing adjustments</small>
                        </div>
                    </button>
                </div>
            </div>
            
            <div class="download-section">
                <h3>📊 Process Details</h3>
                <div style="display:grid;gap:0.5rem">
                    <div><strong>Source:</strong> ${this.escapeHtml(process.source || 'N/A')}</div>
                    <div><strong>Target Languages:</strong> ${this.escapeHtml(process.languages || 'N/A')}</div>
                    <div><strong>Completed:</strong> ${new Date(process.timestamp).toLocaleString()}</div>
                    <div><strong>Duration:</strong> ${this.escapeHtml(process.duration || 'N/A')}</div>
                </div>
            </div>
            
            <div class="download-section">
                <h3>📝 Process Logs</h3>
                <div class="process-logs">${this.escapeHtml(process.logs || 'No logs available')}</div>
            </div>
        `;

        // FIX: Add event listeners for download buttons (XSS safe)
        details.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const url = btn.dataset.url;
                // FIX: More robust URL validation
                if (url && url.trim() && url !== '#' && url !== '') {
                    window.open(url, '_blank');
                }
            });
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatTimeAgo(timestamp) {
        const seconds = Math.floor((Date.now() - timestamp) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return new Date(timestamp).toLocaleDateString();
    },

    deleteProcess(index) {
        if (index >= 0 && index < this.processes.length) {
            this.processes.splice(index, 1);
            try {
                localStorage.setItem('dubbing_processes', JSON.stringify(this.processes));
            } catch (e) {
                console.error('Failed to update localStorage after delete:', e);
            }
            this.renderProcessList();
        }
    }
};
