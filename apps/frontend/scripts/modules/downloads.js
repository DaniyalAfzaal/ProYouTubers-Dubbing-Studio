// ============================================
// DOWNLOADS MANAGER
// ============================================

export const downloads = {
    processes: [],

    init() {
        const downloadsBtn = document.getElementById('downloads-btn');
        const closeBtn = document.getElementById('close-downloads');
        const downloadsPage = document.getElementById('downloads-page');

        if (downloadsBtn && downloadsPage) {
            downloadsBtn.addEventListener('click', () => {
                const originalText = downloadsBtn.textContent;
                downloadsBtn.disabled = true;
                downloadsBtn.textContent = 'Loading...';

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

        // Clear All button
        const clearAllBtn = document.getElementById('clear-all-btn');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAll();
            });
        }

        // Export button
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportHistory();
            });
        }

        // Search input
        const searchInput = document.getElementById('downloads-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterProcesses(e.target.value);
            });
        }

        // Sort dropdown
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortAndRender(e.target.value);
            });
        }

        window.addEventListener('beforeunload', () => {
            // Cleanup if needed
        });
    },

    loadProcesses() {
        const stored = localStorage.getItem('dubbing_processes');
        try {
            this.processes = stored ? JSON.parse(stored) : [];

            // Validate array structure
            if (!Array.isArray(this.processes)) {
                console.warn('Invalid processes data, resetting');
                this.processes = [];
            }

            // Filter out invalid entries
            this.processes = this.processes.filter(p =>
                p && p.id && p.name && p.videoUrl
            );
        } catch (e) {
            console.error('Failed to parse processes from localStorage:', e);

            // Backup corrupted data
            const corrupted = localStorage.getItem('dubbing_processes');
            if (corrupted) {
                localStorage.setItem('dubbing_processes_backup', corrupted);
            }

            this.processes = [];
            localStorage.removeItem('dubbing_processes');
        }
        this.renderProcessList();
    },

    saveProcess(processData) {
        // Validate process data structure
        if (!processData || !processData.timestamp || !processData.name) {
            console.error('Invalid process data:', processData);
            return false;
        }

        // Set default status if not provided
        if (!processData.status) {
            processData.status = 'completed';
        }

        // FIX: Check for duplicates before adding
        const isDuplicate = this.processes.some(p =>
            p.videoUrl === processData.videoUrl &&
            p.timestamp === processData.timestamp
        );

        if (isDuplicate) {
            console.log('Duplicate process detected, skipping');
            return false;
        }

        // Add unique ID if not present
        if (!processData.id) {
            processData.id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        }

        this.processes.unshift(processData);

        // Limit to 50 most recent
        if (this.processes.length > 50) {
            this.processes = this.processes.slice(0, 50);
        }

        return this.saveToStorage();
    },

    saveToStorage() {
        try {
            localStorage.setItem('dubbing_processes', JSON.stringify(this.processes));
            return true;
        } catch (e) {
            if (e.name === 'QuotaExceededError') {
                console.warn('localStorage quota exceeded, trimming to 25 entries');
                this.processes = this.processes.slice(0, 25);

                try {
                    localStorage.setItem('dubbing_processes', JSON.stringify(this.processes));

                    // Notify user if toast is available
                    if (typeof toast !== 'undefined') {
                        toast.warn('Download history trimmed due to storage limit');
                    }
                    return true;
                } catch (retryError) {
                    console.error('Failed to save even after cleanup:', retryError);
                    return false;
                }
            } else {
                console.error('Failed to save processes to localStorage:', e);
                return false;
            }
        }
    },

    getProcesses() {
        return this.processes;
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
            <div class="process-card${proc.status === 'failed' ? ' failed' : ''}${i === 0 ? ' active' : ''}" data-index="${i}" title="${this.escapeHtml(proc.name || 'Dubbing Process')}">
                <div class="process-header">
                    <div class="process-status ${proc.status === 'failed' ? 'failed' : 'completed'}">
                        <span class="status-icon">${proc.status === 'failed' ? '✗' : '✓'}</span>
                        <span class="status-text">${proc.status === 'failed' ? 'Failed' : 'Completed'}</span>
                    </div>
                    <button class="delete-btn" data-index="${i}" title="Delete" aria-label="Delete process">
                        <span>🗑️</span>
                    </button>
                </div>
                <div class="process-name">${this.escapeHtml(this.truncateName(proc.name || 'Dubbing Process'))}</div>
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
        if (!details) return;

        details.innerHTML = `
            <!-- Video Preview Section -->
            <div class="video-preview-section">
                <h3>🎬 Video Preview</h3>
                <video controls 
                       src="${this.escapeHtml(process.videoUrl)}"
                       class="preview-video"
                       preload="metadata">
                    Your browser does not support video playback.
                </video>
            </div>
            
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
                    <div class="detail-item" title="${this.escapeHtml(process.source || 'N/A')}">
                        <strong>Source:</strong> ${this.escapeHtml(this.truncatePath(process.source || 'N/A', 80))}
                    </div>
                    <div><strong>Target Languages:</strong> ${this.escapeHtml(process.languages || 'N/A')}</div>
                    <div><strong>Completed:</strong> ${new Date(process.timestamp).toLocaleString()}</div>
                    <div><strong>Duration:</strong> ${this.calculateDuration(process)}</div>
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
            this.saveToStorage();
            this.renderProcessList();
        }
    },

    clearAll() {
        if (confirm('Are you sure you want to clear all download history? This cannot be undone.')) {
            this.processes = [];
            localStorage.removeItem('dubbing_processes');
            this.renderProcessList();

            if (typeof toast !== 'undefined') {
                toast.success('Download history cleared');
            }
        }
    },

    // Auto-cleanup old entries (optional - can be called on init)
    autoCleanupOldEntries(daysToKeep = 30) {
        const cutoffTime = Date.now() - (daysToKeep * 24 * 60 * 60 * 1000);
        const initialCount = this.processes.length;

        this.processes = this.processes.filter(p => p.timestamp > cutoffTime);

        if (this.processes.length < initialCount) {
            this.saveToStorage();
            console.log(`Cleaned up ${initialCount - this.processes.length} old entries`);
        }
    },

    // Helper functions
    truncateName(name) {
        return name.length > 40 ? name.substring(0, 37) + '...' : name;
    },

    truncatePath(path, maxLength = 80) {
        if (path.length <= maxLength) return path;
        const parts = path.split('/');
        if (parts.length <= 3) return path.substring(0, maxLength - 3) + '...';
        return `${parts[0]}/.../${parts[parts.length - 1]}`;
    },

    calculateDuration(process) {
        if (process.duration && process.duration !== 'N/A' && process.duration !== 'Unknown') {
            return process.duration;
        }
        return 'Unknown';
    },

    // New Features for 100% Quality

    filterProcesses(query) {
        const searchInput = document.getElementById('downloads-search');
        if (!query || !query.trim()) {
            this.renderProcessList();
            return;
        }

        const filtered = this.processes.filter(p => {
            const searchTerm = query.toLowerCase();
            return (
                p.name?.toLowerCase().includes(searchTerm) ||
                p.languages?.toLowerCase().includes(searchTerm) ||
                p.source?.toLowerCase().includes(searchTerm) ||
                p.logs?.toLowerCase().includes(searchTerm)
            );
        });

        this.renderFilteredList(filtered, query);
    },

    renderFilteredList(filteredProcesses, query) {
        const list = document.getElementById('process-list');
        if (!list) return;

        if (filteredProcesses.length === 0) {
            list.innerHTML = `
                <div class="empty-state-beautiful">
                    <div class="empty-icon">🔍</div>
                    <h3>No Matches Found</h3>
                    <p>No results for "${this.escapeHtml(query)}"</p>
                    <div class="quick-tip">
                        <span class="tip-icon">💡</span>
                        <span>Try a different search term</span>
                    </div>
                </div>
            `;

            document.getElementById('download-details').innerHTML = `
                <div class="empty-state-beautiful">
                    <div class="empty-icon">🔍</div>
                    <h3>No Selection</h3>
                    <p>Refine your search to see results</p>
                </div>
            `;
            return;
        }

        // Render filtered list with same template as renderProcessList
        list.innerHTML = filteredProcesses.map((proc, i) => `
            <div class="process-card${i === 0 ? ' active' : ''}" data-index="${this.processes.indexOf(proc)}" title="${this.escapeHtml(proc.name || 'Dubbing Process')}">
                <div class="process-header">
                    <div class="process-status ${proc.status === 'failed' ? 'failed' : 'completed'}">
                        <span class="status-icon">${proc.status === 'failed' ? '✗' : '✓'}</span>
                        <span class="status-text">${proc.status === 'failed' ? 'Failed' : 'Completed'}</span>
                    </div>
                    <button class="delete-btn" data-index="${this.processes.indexOf(proc)}" title="Delete" aria-label="Delete process">
                        <span>🗑️</span>
                    </button>
                </div>
                <div class="process-name">${this.escapeHtml(this.truncateName(proc.name || 'Dubbing Process'))}</div>
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

        // Add event handlers
        list.querySelectorAll('.process-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.delete-btn')) return;
                list.querySelectorAll('.process-card').forEach(el => el.classList.remove('active'));
                card.classList.add('active');
                const index = parseInt(card.dataset.index);
                this.showProcessDetails(this.processes[index]);
            });
        });

        list.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(btn.dataset.index);
                if (confirm('Delete this process?')) {
                    this.deleteProcess(index);
                    // Re-apply search after deletion
                    const searchInput = document.getElementById('downloads-search');
                    if (searchInput && searchInput.value) {
                        this.filterProcesses(searchInput.value);
                    }
                }
            });
        });

        if (filteredProcesses.length > 0) {
            this.showProcessDetails(filteredProcesses[0]);
        }
    },

    sortAndRender(sortBy) {
        const processesCopy = [...this.processes];

        switch (sortBy) {
            case 'date-new':
                processesCopy.sort((a, b) => b.timestamp - a.timestamp);
                break;
            case 'date-old':
                processesCopy.sort((a, b) => a.timestamp - b.timestamp);
                break;
            case 'name-asc':
                processesCopy.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'name-desc':
                processesCopy.sort((a, b) => b.name.localeCompare(a.name));
                break;
        }

        // Temporarily set sorted array for rendering
        const original = this.processes;
        this.processes = processesCopy;
        this.renderProcessList();
        this.processes = original;
    },

    exportHistory() {
        if (this.processes.length === 0) {
            if (typeof toast !== 'undefined') {
                toast.warn('No download history to export');
            } else {
                alert('No download history to export');
            }
            return;
        }

        const data = {
            exported: new Date().toISOString(),
            exportedBy: 'ProYouTubers Dubbing Studio',
            totalProcesses: this.processes.length,
            processes: this.processes
        };

        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `dubbing-history-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        URL.revokeObjectURL(url);

        if (typeof toast !== 'undefined') {
            toast.success(`Exported ${this.processes.length} processes!`);
        }
    }
};
