// Translation provider dropdown logic
// FIX Bug #9: Avoid DOMContentLoaded race condition
(function initProviderToggle() {
    const trModelSelect = document.getElementById('tr-model');
    const trProviderLabel = document.getElementById('tr-provider-label');

    // If elements not found yet, wait for DOM
    if (!trModelSelect || !trProviderLabel) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initProviderToggle);
        }
        return;
    }

    // Function to toggle provider dropdown visibility
    const toggleProviderDropdown = () => {
        const selectedModel = trModelSelect.value;

        // Only show provider dropdown when deep_translator is selected
        if (selectedModel === 'deep_translator') {
            trProviderLabel.style.display = 'block';
        } else {
            trProviderLabel.style.display = 'none';
        }
    };

    // Toggle on load
    toggleProviderDropdown();

    // Toggle when model changes
    trModelSelect.addEventListener('change', toggleProviderDropdown);
})();
