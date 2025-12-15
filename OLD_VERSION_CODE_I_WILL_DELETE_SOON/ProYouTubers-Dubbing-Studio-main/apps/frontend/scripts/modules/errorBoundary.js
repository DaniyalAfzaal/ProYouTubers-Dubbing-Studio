// ============================================
// GLOBAL ERROR BOUNDARY
// ============================================

export const errorBoundary = {
    init() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error caught:', event.error);
            this.handleError(event.error || event.message);
            event.preventDefault();
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.handleError(event.reason);
            event.preventDefault();
        });
    },

    handleError(error) {
        // Import toast dynamically to avoid circular dependency
        import('./toast.js').then(({ toast }) => {
            const message = error?.message || error?.toString() || 'An unexpected error occurred';
            toast.error(`Error: ${message}`);
        }).catch(() => {
            // Fallback if toast fails
            console.error('Failed to show error toast:', error);
        });
    },

    reportError(context, error) {
        console.error(`[${context}]`, error);
        this.handleError(error);
    }
};

// Auto-initialize
errorBoundary.init();
