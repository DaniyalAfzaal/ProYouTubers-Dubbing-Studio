// ============================================
// TOAST NOTIFICATIONS UTILITY
// ============================================

export const toast = {
    show(message, type = 'info', duration = 4000) {
        // Create toast element
        const toastEl = document.createElement('div');
        toastEl.className = `toast toast-${type}`;
        toastEl.textContent = message;

        // Add to body
        document.body.appendChild(toastEl);

        // Trigger animation
        requestAnimationFrame(() => {
            toastEl.classList.add('show');
        });

        // Auto-remove
        setTimeout(() => {
            toastEl.classList.remove('show');
            setTimeout(() => {
                toastEl.remove();
            }, 300);
        }, duration);
    },

    error(message) {
        this.show(message, 'error', 5000);
    },

    success(message) {
        this.show(message, 'success', 3000);
    },

    warning(message) {
        this.show(message, 'warning', 4000);
    },

    info(message) {
        this.show(message, 'info', 3000);
    }
};

// Add toast CSS dynamically
const toastStyles = `
.toast {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    color: white;
    font-weight: 600;
    font-size: 1rem;
    z-index: 10000;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s ease;
    max-width: 400px;
}

.toast.show {
    opacity: 1;
    transform: translateY(0);
}

.toast-error {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    border-left: 4px solid #991b1b;
}

.toast-success {
    background: linear-gradient(135deg, #10b981, #059669);
    border-left: 4px solid #047857;
}

.toast-warning {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    border-left: 4px solid #b45309;
}

.toast-info {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border-left: 4px solid #1d4ed8;
}

@media (max-width: 768px) {
    .toast {
        bottom: 1rem;
        right: 1rem;
        left: 1rem;
        max-width: none;
    }
}
`;

// Inject styles
const styleEl = document.createElement('style');
styleEl.textContent = toastStyles;
document.head.appendChild(styleEl);
