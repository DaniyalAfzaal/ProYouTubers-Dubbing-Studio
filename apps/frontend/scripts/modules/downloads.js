// ============================================
// DOWNLOADS MANAGER
// ============================================

export const downloads = {
    processes: [],

    init() {
        const downloadsBtn = document.getElementById('downloads-btn');
        const closeBtn = document.getElementById('close-downloads');
        const downloadsPage = document.getElementById('downloads-page');

        if (downloadsBtn) {
            downloadsBtn.addEventListener('click', () => {
                downloadsPage.hidden = false;
                this.loadProcesses();
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                downloadsPage.hidden = true;
            });
        }
    },

    loadProcesses() {
        const stored = localStorage.getItem('dubbing_processes');
        this.processes = stored ? JSON.parse(stored) : [];
        this.renderProcessList();
    },

    saveProcess(processData) {
        this.processes.unshift(processData);
        if (this.processes.length > 50) this.processes.pop();
        localStorage.setItem('dubbing_processes', JSON.stringify(this.processes));
    },

    renderProcessList() {
        const list = document.getElementById('process-list');

        if (this.processes.length === 0) {
            list.innerHTML = '<div class="empty-state"><span class="empty-icon">📋</span><p>No completed processes yet</p></div>';
            return;
        }

        list.innerHTML = this.processes.map((proc, i) => `
            <div class="process-item${i === 0 ? ' active' : ''}" data-index="${i}">
                <div><strong>${this.escapeHtml(proc.name || 'Dubbing Process')}</strong></div>
                <div style="font-size:0.85rem;color:var(--text-muted);margin-top:0.25rem">${new Date(proc.timestamp).toLocalString()}</div>
            </div>
        `).join('');

        list.querySelectorAll('.process-item').forEach(item => {
            item.addEventListener('click', () => {
                list.querySelectorAll('.process-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
                this.showProcessDetails(this.processes[parseInt(item.dataset.index)]);
            });
        });

        if (this.processes.length > 0) {
            this.showProcessDetails(this.processes[0]);
        }
    },

    showProcessDetails(process) {
        const details = document.getElementById('download-details');

        details.innerHTML = `
            <div class="download-section">
                <h3>📥 Download Options</h3>
                <div class="download-buttons">
                    <button class="download-btn" onclick="window.open('${process.videoUrl || '#'}', '_blank')">
                        <span style="font-size:1.5rem">🎬</span>
                        <div>
                            <div>Complete Dubbed Video</div>
                            <small style="opacity:0.8">Exported with audio</small>
                        </div>
                    </button>
                    <button class="download-btn" onclick="window.open('${process.audioUrl || '#'}', '_blank')">
                        <span style="font-size:1.5rem">🎵</span>
                        <div>
                            <div>Dubbed Audio</div>
                            <small style="opacity:0.8">Time-adjusted</small>
                        </div>
                    </button>
                    <button class="download-btn" onclick="window.open('${process.rawAudioUrl || '#'}', '_blank')">
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
                    <div><strong>Duration:</strong> ${process.duration || 'N/A'}</div>
                </div>
            </div>
            
            <div class="download-section">
                <h3>📝 Process Logs</h3>
                <div class="process-logs">${this.escapeHtml(process.logs || 'No logs available')}</div>
            </div>
        `;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
