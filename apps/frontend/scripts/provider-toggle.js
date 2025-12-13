// Translation provider dropdown logic
document.addEventListener('DOMContentLoaded', () => {
    const trModelSelect = document.getElementById('tr-model');
    const trProviderLabel = document.getElementById('tr-provider-label');

    if (!trModelSelect || !trProviderLabel) return;

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
});
