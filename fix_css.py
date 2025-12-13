import re

# Read the corrupted CSS file
input_file = r'c:\Users\daniy\OneDrive\Desktop\ProYouTubers Ai Dubbing Tool\apps\frontend\styles\main.css'
output_file = r'c:\Users\daniy\OneDrive\Desktop\ProYouTubers Ai Dubbing Tool\apps\frontend\styles\main_fixed.css'
backup_file = r'c:\Users\daniy\OneDrive\Desktop\ProYouTubers Ai Dubbing Tool\apps\frontend\styles\main_backup.css'

# Read with encoding that handles NULL bytes
with open(input_file, 'rb') as f:
    content_bytes = f.read()

# Backup the original
with open(backup_file, 'wb') as f:
    f.write(content_bytes)

# Convert to string and remove NULL bytes
content = content_bytes.decode('utf-8', errors='ignore')
# Remove NULL bytes
content_clean = content.replace('\x00', '')

# Find where corruption starts (around line 850 based on our analysis)
# We'll trim and add clean CSS from that point

# Split into lines and find first corrupted section
lines = content_clean.split('\n')

# Find the last clean CSS before corruption (look for "Mode Selector" comment)
clean_end_index = 0
for i, line in enumerate(lines):
    if '/* Mode Selector */' in line:
        clean_end_index = i + 50  # Keep some buffer
        break

# If we found it, keep everything up to that point + add our clean CSS
if clean_end_index > 0:
    clean_lines = lines[:clean_end_index]
    
    # Add the clean CSS sections
    additional_css = '''
/* ============================================
   MODE SELECTOR  
   ============================================ */
.mode-selector {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}

.mode-option {
    flex: 1;
    min-width: 200px;
    padding: 1.25rem;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.mode-option:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.mode-option:has(input:checked) {
    border-color: var(--accent-primary);
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white;
    box-shadow: var(--shadow-glow);
}

.mode-option input {
    cursor: pointer;
    width: 20px;
    height: 20px;
    accent-color: white;
}

.mode-option span {
    font-size: 1.1rem;
}

/* ============================================
   BULK PROGRESS DISPLAY
   ============================================ */
.bulk-progress-container {
    margin: 2rem 0;
    padding: 2rem;
    background: var(--bg-card);
    border-radius: 16px;
    border: 2px solid var(--border-color);
    box-shadow: var(--shadow-md);
}

.bulk-progress-container h2 {
    margin: 0 0 1.5rem 0;
    color: var(--text-primary);
    font-size: 1.5rem;
}

.overall-progress {
    margin-bottom: 2rem;
}

.progress-stats {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.progress-stats span {
    color: var(--text-secondary);
}

.progress-stats strong {
    color: var(--accent-primary);
    font-size: 1.25rem;
}

.progress-bar-container {
    width: 100%;
    height: 24px;
    background: var(--bg-tertiary);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-color);
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    transition: width 0.5s ease;
    box-shadow: 0 0 20px var(--accent-glow);
}

.video-list {
    display: grid;
    gap: 1rem;
}

.video-item {
    padding: 1.25rem;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    position: relative;
    transition: var(--transition);
    overflow: hidden;
}

.video-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--border-color);
    transition: var(--transition);
}

.video-item.queued::before {
    background: var(--text-muted);
}

.video-item.processing {
    border-color: var(--accent-secondary);
    animation: processing-pulse 2s infinite;
}

.video-item.processing::before {
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
    animation: progress-slide 1.5s infinite;
}

@keyframes processing-pulse {
    0%, 100% {
        box-shadow: 0 0 0 rgba(239, 68, 68, 0.4);
    }
    50% {
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
    }
}

@keyframes progress-slide {
    0% {
        transform: translateX(-100%);
    }
    100% {
        transform: translateX(100%);
    }
}

.video-item.completed {
    border-color: #10b981;
}

.video-item.completed::before {
    background: #10b981;
}

.video-item.failed {
    border-color: #ef4444;
}

.video-item.failed::before {
    background: #ef4444;
}

.video-item:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
}

.video-item h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    word-break: break-word;
    color: var(--text-primary);
}

.video-item .status {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    font-size: 0.75rem;
    text-transform: uppercase;
    font-weight: 700;
    border-radius: 6px;
    letter-spacing: 0.5px;
}

.video-item.queued .status {
    background: var(--bg-tertiary);
    color: var(--text-muted);
}

.video-item.processing .status {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: white;
    animation: status-glow 2s infinite;
}

@keyframes status-glow {
    0%, 100% {
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
    }
    50% {
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.8);
    }
}

.video-item.completed .status {
    background: #10b981;
    color: white;
}

.video-item.failed .status {
    background: #ef4444;
    color: white;
}

.video-item .error {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background: rgba(239, 68, 68, 0.1);
    border-left: 3px solid #ef4444;
    color: #ef4444;
    border-radius: 4px;
    font-size: 0.9rem;
}

.video-item .download-link {
    display: inline-block;
    margin-top: 0.75rem;
    padding: 0.5rem 1rem;
    background: var(--accent-primary);
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 600;
    transition: var(--transition);
}

.video-item .download-link:hover {
    background: var(--accent-secondary);
    transform: translateY(-2px);
}

/* ============================================
   HEADER REDESIGN - Typography Based
   ============================================ */
header {
    padding: 2rem 3rem;
    background: var(--bg-card);
    border-bottom: 3px solid var(--accent-primary);
    box-shadow: var(--shadow-lg);
}

.header-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
}

.brand-typography {
    flex: 1;
}

.brand-name {
    margin: 0;
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    line-height: 1;
    text-transform: uppercase;
}

.brand-subtitle {
    margin: 0.5rem 0 0 0;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.brand-tagline {
    margin: 0.75rem 0 0 0;
    font-size: 0.95rem;
    color: var(--text-muted);
    font-style: italic;
}

.header-nav {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.nav-btn, .theme-toggle {
    padding: 0.75rem 1.5rem;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
}

.nav-btn:hover, .theme-toggle:hover {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: white;
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.btn-icon {
    font-size: 1.25rem;
}

/* ============================================
   DOWNLOADS MANAGER - MODAL OVERLAY
   ============================================ */
.downloads-page {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

.downloads-page[hidden] {
    display: none;
}

.downloads-header {
    padding: 2rem 3rem;
    background: var(--bg-card);
    border-bottom: 3px solid var(--accent-primary);
    box-shadow: var(--shadow-md);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.downloads-header h1 {
    margin: 0;
    font-size: 2rem;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.btn-close {
    padding: 0.75rem 1.5rem;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    cursor: pointer;
    transition: var(--transition);
    font-size: 1.1rem;
    font-weight: 600;
}

.btn-close:hover {
    background: #ef4444;
    border-color: #ef4444;
    color: white;
    transform: scale(1.05);
}

.downloads-content {
    flex: 1;
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 0;
    overflow: hidden;
}

.downloads-sidebar {
    background: var(--bg-secondary);
    border-right: 2px solid var(--border-color);
    padding: 1.5rem;
    overflow-y: auto;
}

.downloads-sidebar h3 {
    margin: 0 0 1rem 0;
    color: var(--text-primary);
    font-size: 1.1rem;
}

.process-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.process-item {
    padding: 1rem;
    background: var(--bg-tertiary);
    border: 2px solid var(--border-color);
    border-radius: 8px;
    cursor: pointer;
    transition: var(--transition);
}

.process-item:hover {
    border-color: var(--accent-primary);
    transform: translateX(4px);
}

.process-item.active {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: white;
}

. downloads-main {
    background: var(--bg-primary);
    padding: 2rem;
    overflow-y: auto;
}

.download-details {
    max-width: 900px;
    margin: 0 auto;
}

.download-section {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: var(--bg-card);
    border-radius: 12px;
    border: 2px solid var(--border-color);
}

.download-section h3 {
    margin: 0 0 1.5rem 0;
    color: var(--text-primary);
    font-size: 1.3rem;
}

.download-buttons {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.download-btn {
    padding: 1.25rem;
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    align-items: center;
    gap: 1rem;
    text-align: left;
}

.download-btn:hover {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: white;
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
}

.process-logs {
    padding: 1.5rem;
    background: var(--bg-tertiary);
    border-radius: 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
}

.empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-muted);
}

.empty-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 1024px) {
    .header-container {
        flex-direction: column;
        align-items: flex-start;
        gap: 1.5rem;
    }

    .brand-name {
        font-size: 2.5rem;
    }

    .brand-subtitle {
        font-size: 1.25rem;
    }

    .downloads-content {
        grid-template-columns: 1fr;
        grid-template-rows: auto 1fr;
    }

    .downloads-sidebar {
        border-right: none;
        border-bottom: 2px solid var(--border-color);
        max-height: 200px;
    }
}

@media (max-width: 768px) {
    header {
        padding: 1.5rem;
    }

    .brand-name {
        font-size: 2rem;
    }

    .brand-subtitle {
        font-size: 1rem;
    }

    .brand-tagline {
        font-size: 0.85rem;
    }

    .header-nav {
        width: 100%;
        justify-content: space-between;
    }

    .downloads-header {
        padding: 1.5rem;
    }

    .downloads-header h1 {
        font-size: 1.5rem;
    }

    .downloads-main {
        padding: 1rem;
    }

    .download-buttons {
        grid-template-columns: 1fr;
    }

    .progress-stats {
        flex-direction: column;
        gap: 0.75rem;
    }

    .mode-selector {
        flex-direction: column;
    }

    .mode-option {
        min-width: 100%;
    }
}
'''
    
    # Combine
    final_content = '\n'.join(clean_lines) + additional_css
else:
    # Fallback: just remove NULL bytes
    final_content = content_clean

# Write the fixed version
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✅ CSS file cleaned successfully!")
print(f"📁 Backup saved to: {backup_file}")
print(f"📁 Fixed file created: {output_file}")
print(f"ℹ️  Total lines processed: {len(lines)}")
print(f"ℹ️  Clean section ends at line: {clean_end_index}")
