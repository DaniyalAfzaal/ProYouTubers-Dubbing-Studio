"""
Audio Quality Validation Module

Provides validation functions to detect corrupted, silent, or invalid audio
files early in the dubbing pipeline before expensive processing.
"""

from pathlib import Path
from typing import Tuple
import numpy as np
import soundfile as sf
import logging

logger = logging.getLogger(__name__)


def validate_audio_quality(audio_path: Path, min_duration: float = 0.1) -> Tuple[bool, str]:
    """
    Check if audio is valid and not silent/corrupted.
    
    Args:
        audio_path: Path to audio file to validate
        min_duration: Minimum acceptable duration in seconds (default 0.1s)
        
    Returns:
        (is_valid, error_message): Tuple of validation result and error description
        
    Example:
        is_valid, error = validate_audio_quality(Path("segment_001.wav"))
        if not is_valid:
            logger.error(f"Invalid audio: {error}")
    """
    try:
        # Read audio file
        audio, sr = sf.read(str(audio_path))
        
        # Check duration
        duration = len(audio) / sr if sr > 0 else 0
        if duration < min_duration:
            return False, f"Audio too short: {duration:.3f}s (minimum {min_duration}s)"
        
        # Check if silent (RMS threshold)
        if len(audio.shape) > 1:
            # Stereo - check both channels
            rms = np.sqrt(np.mean(audio**2, axis=0))
            max_rms = np.max(rms)
        else:
            # Mono
            rms = np.sqrt(np.mean(audio**2))
            max_rms = rms
            
        if max_rms < 0.001:
            return False, f"Audio is silent (RMS: {max_rms:.6f})"
        
        # Check for NaN/Inf values
        if np.any(np.isnan(audio)):
            return False, "Audio contains NaN values (corrupted data)"
        if np.any(np.isinf(audio)):
            return False, "Audio contains Inf values (corrupted data)"
        
        # Check for clipping (values outside [-1, 1])
        if np.any(np.abs(audio) > 1.0):
            clipped_pct = 100 * np.sum(np.abs(audio) > 1.0) / audio.size
            if clipped_pct > 5:  # More than 5% clipped
                return False, f"Audio is clipped: {clipped_pct:.1f}% of samples exceed range"
        
        return True, ""
        
    except FileNotFoundError:
        return False, f"Audio file not found: {audio_path}"
    except Exception as e:
        return False, f"Failed to read audio: {type(e).__name__}: {e}"


def validate_segment_audio(segment_path: Path, expected_duration: float, tolerance: float = 0.5) -> Tuple[bool, str]:
    """
    Validate a TTS segment with duration expectations.
    
    Args:
        segment_path: Path to segment audio file
        expected_duration: Expected duration in seconds
        tolerance: Acceptable deviation in seconds (default 0.5s)
        
    Returns:
        (is_valid, error_message): Validation result and error description
    """
    # Basic quality check
    is_valid, error = validate_audio_quality(segment_path, min_duration=0.05)
    if not is_valid:
        return False, error
    
    # Duration check
    try:
        audio, sr = sf.read(str(segment_path))
        actual_duration = len(audio) / sr
        deviation = abs(actual_duration - expected_duration)
        
        if deviation > tolerance:
            return False, (
                f"Duration mismatch: expected {expected_duration:.2f}s, "
                f"got {actual_duration:.2f}s (deviation: {deviation:.2f}s)"
            )
        
        return True, ""
    except Exception as e:
        return False, f"Duration check failed: {e}"
