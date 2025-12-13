/* Simple inline script to show GPU mode on bulk start */
// FIX Bug #10: Avoid DOMContentLoaded race condition
(function initGPUModeDisplay() {
    const originalFetch = window.fetch;

    window.fetch = async (...args) => {
        const response = await originalFetch(...args);

        // Intercept bulk-run response
        if (args[0] && args[0].includes('/api/jobs/bulk-run')) {
            try {
                const clone = response.clone();
                const data = await clone.json();

                if (data.gpus) {
                    const isModal = data.gpus > 2;
                    const badge = document.createElement('div');
                    badge.className = `gpu-mode-badge ${isModal ? 'modal-mode' : 'queue-mode'}`;
                    badge.innerHTML = `
                        <span class="gpu-icon">${isModal ? '🚀' : '📋'}</span>
                        <span class="gpu-label">${isModal ? 'Modal Functions' : 'Queue Mode'}</span>
                        <span class="gpu-count">${data.gpus} GPU${data.gpus > 1 ? 's' : ''}</span>
                        ${isModal ? '<span class="gpu-speed">⚡ 10x Faster</span>' : ''}
                    `;

                    const container = document.getElementById('bulk-progress-container');
                    if (container && !container.querySelector('.gpu-mode-badge')) {
                        container.insertBefore(badge, container.firstChild);
                    }
                }
            } catch (err) {
                // Silently fail if response isn't JSON or element not found
                console.warn('GPU mode display failed:', err);
            }
        }

        return response;
    };
})();
