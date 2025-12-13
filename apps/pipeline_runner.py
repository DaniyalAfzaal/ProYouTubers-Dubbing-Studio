"""
Pipeline runner for Modal bulk processing.
Wrapper around the orchestrator pipeline for use in Modal Functions.
"""

import sys
import os
from pathlib import Path

def run_dubbing_pipeline(
    source: str,
    target_languages: list[str],
    source_language: str = "auto",
    asr_model: str = "whisperx",
    translation_model: str = "deep_translator",
    tts_model: str = "chatterbox",
    translation_strategy: str = "direct",
    dubbing_strategy: str = "keep_bg_music",
    **kwargs
) -> dict:
    """
    Run the complete dubbing pipeline.
    
    This is a simplified interface for Modal Functions.
    """
    # Add backend to path
    backend_path = Path(__file__).parent.parent / "backend"
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    # Import orchestrator logic
    from services.orchestrator.app.main import run_pipeline_sync
    
    # Prepare options
    options = {
        "source": source,
        "target_languages": target_languages,
        "source_language": source_language,
        "asr_model": asr_model,
        "translation_model": translation_model,
        "tts_model": tts_model,
        "translation_strategy": translation_strategy,
        "dubbing_strategy": dubbing_strategy,
        **kwargs
    }
    
    # Run pipeline
    result = run_pipeline_sync(options)
    
    return result
