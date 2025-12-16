"""
Silero VAD Utilities for WhisperX - Production Grade
=====================================================

This module provides centralized, production-ready Silero V5 VAD integration
for the WhisperX ASR pipeline. It replaces the outdated Pyannote VAD with
a modern ML-trained voice activity detector that accurately distinguishes
speech phonemes from breaths, transients, and background noise.

Key Features:
- ML-trained speech detection (not energy-based)
- Singleton pattern for efficient model reuse
- Comprehensive error handling with fallbacks
- Configurable parameters for fine-tuning
- Professional-grade logging

Author: Bluez AI Dubbing System
License: MIT
"""

from __future__ import annotations
import logging
import torch
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Global VAD model cache (singleton pattern)
_vad_model: Optional[Any] = None
_vad_model_loaded: bool = False


def get_vad_model() -> Any:
    """
    Get or load Silero VAD model using singleton pattern.
    
    The model is loaded once and cached for subsequent calls,
    improving performance across multiple VAD operations.
    
    Returns:
        Loaded Silero VAD model
        
    Raises:
        RuntimeError: If model loading fails
    """
    global _vad_model, _vad_model_loaded
    
    if _vad_model_loaded:
        return _vad_model
    
    try:
        logger.info("🔄 Loading Silero VAD model (v5)...")
        
        # Import here to avoid loading if not needed
        from silero_vad import load_silero_vad
        
        # Load model
        _vad_model = load_silero_vad()
        _vad_model_loaded = True
        
        logger.info("✅ Silero VAD model loaded successfully")
        return _vad_model
        
    except ImportError as e:
        logger.error(f"Silero VAD library not found: {e}")
        logger.error("Install with: pip install silero-vad")
        raise RuntimeError("Silero VAD not available") from e
        
    except Exception as e:
        logger.error(f"Failed to load Silero VAD model: {e}", exc_info=True)
        raise RuntimeError(f"Could not load Silero VAD: {e}") from e


def detect_speech_segments(
    audio: np.ndarray,
    sampling_rate: int = 16000,
    threshold: float = 0.5,
    min_speech_duration_ms: int = 250,
    min_silence_duration_ms: int = 100,
    speech_pad_ms: int = 30,
    return_seconds: bool = True
) -> Optional[List[Dict[str, float]]]:
    """
    Detect speech segments in audio using Silero V5 VAD with ML-based classification.
    
    This function uses a neural network trained to distinguish speech phonemes from:
    - Pre-speech breath intake
    - Lip smacks and clicks  
    - Background noise
    - Transient sounds
    - Audio compression artifacts
    
    The min_speech_duration_ms parameter is CRITICAL - it ensures only sustained
    speech (actual words) is detected, not transient sounds like breathing.
    
    Args:
        audio: Audio array (numpy, mono, float32)
        sampling_rate: Audio sample rate in Hz (default: 16000 for WhisperX)
        threshold: Voice probability threshold 0.0-1.0 (default: 0.5 = balanced)
            - Lower (0.3-0.4): More sensitive, may catch breaths
            - Higher (0.6-0.7): More conservative, may miss soft speech
        min_speech_duration_ms: Minimum duration for valid speech in milliseconds
            - This is the KEY parameter that filters out breaths/transients
            - Default 250ms = quarter second minimum for speech
            - Breaths typically last 50-150ms, so they get filtered out
        min_silence_duration_ms: Minimum silence to split segments
            - Segments separated by less than this are merged
            - Default 100ms allows for natural pauses within sentences
        speech_pad_ms: Padding added around detected speech boundaries
            - Reduced from Pyannote's ~400ms default to 30ms
            - Prevents premature audio start
        return_seconds: If True, return timestamps in seconds; if False, in samples
        
    Returns:
        List of speech segments: [{"start": 0.5, "end": 5.2}, ...]
        Returns None if VAD fails (caller should use fallback VAD)
        
    Example:
        >>> audio, sr = librosa.load("audio.wav", sr=16000)
        >>> segments = detect_speech_segments(audio, sr)
        >>> print(segments)
        [{"start": 0.79, "end": 5.94}, {"start": 7.12, "end": 31.68}]
    """
    if audio is None or len(audio) == 0:
        logger.warning("Empty audio provided to VAD, returning None")
        return None
    
    try:
        # Get VAD model (cached after first call)
        vad_model = get_vad_model()
        
        # Import here to avoid dependency if VAD not used
        from silero_vad import get_speech_timestamps
        
        # Convert numpy array to PyTorch tensor
        if isinstance(audio, np.ndarray):
            audio_tensor = torch.from_numpy(audio.astype(np.float32))
        elif isinstance(audio, torch.Tensor):
            audio_tensor = audio.float()
        else:
            logger.error(f"Unexpected audio type: {type(audio)}")
            return None
        
        # Handle multi-channel audio (convert to mono)
        if len(audio_tensor.shape) > 1:
            logger.warning(f"Multi-channel audio detected, converting to mono")
            audio_tensor = torch.mean(audio_tensor, dim=0)
        
        # Validate tensor
        if torch.isnan(audio_tensor).any() or torch.isinf(audio_tensor).any():
            logger.error("Audio contains NaN or Inf values")
            return None
        
        # Get speech timestamps from Silero
        logger.debug(
            f"Running Silero VAD: threshold={threshold}, "
            f"min_speech={min_speech_duration_ms}ms, "
            f"min_silence={min_silence_duration_ms}ms, "
            f"pad={speech_pad_ms}ms"
        )
        
        speech_timestamps = get_speech_timestamps(
            audio_tensor,
            vad_model,
            threshold=threshold,
            sampling_rate=sampling_rate,
            min_speech_duration_ms=min_speech_duration_ms,
            min_silence_duration_ms=min_silence_duration_ms,
            speech_pad_ms=speech_pad_ms,
            return_seconds=return_seconds
        )
        
        if not speech_timestamps:
            logger.warning("Silero VAD detected no speech in audio")
            return None
        
        # Log results
        total_speech = sum(ts['end'] - ts['start'] for ts in speech_timestamps)
        audio_duration = len(audio) / sampling_rate
        speech_ratio = (total_speech / audio_duration) * 100 if audio_duration > 0 else 0
        
        logger.info(f"🎯 Silero VAD Results:")
        logger.info(f"   Audio duration: {audio_duration:.2f}s")
        logger.info(f"   Detected segments: {len(speech_timestamps)}")
        logger.info(f"   Total speech: {total_speech:.2f}s ({speech_ratio:.1f}%)")
        logger.info(f"   First segment: [{speech_timestamps[0]['start']:.2f}-{speech_timestamps[0]['end']:.2f}s]")
        
        # Log first few segments for verification
        for i, ts in enumerate(speech_timestamps[:3]):
            duration = ts['end'] - ts['start']
            logger.info(f"   Segment {i}: [{ts['start']:.2f}-{ts['end']:.2f}s] (dur={duration:.2f}s)")
        
        if len(speech_timestamps) > 3:
            logger.info(f"   ... and {len(speech_timestamps) - 3} more segments")
        
        # Convert to standard format for WhisperX
        segments = [
            {
                "start": float(ts["start"]),
                "end": float(ts["end"])
            }
            for ts in speech_timestamps
        ]
        
        return segments
        
    except ImportError as e:
        logger.error(f"Silero VAD import failed: {e}")
        logger.warning("Falling back to WhisperX built-in VAD (Pyannote)")
        return None
        
    except RuntimeError as e:
        logger.error(f"Silero VAD runtime error: {e}")
        logger.warning("Falling back to WhisperX built-in VAD")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error in Silero VAD: {e}", exc_info=True)
        logger.warning("Falling back to WhisperX built-in VAD")
        return None


def validate_vad_segments(
    segments: List[Dict[str, float]],
    audio_duration: float,
    min_segment_duration: float = 0.1
) -> List[Dict[str, float]]:
    """
    Validate and sanitize VAD segments.
    
    Ensures segments are:
    - Within audio bounds
    - Non-overlapping
    - Above minimum duration
    - Properly ordered
    
    Args:
        segments: List of segments from VAD
        audio_duration: Total audio duration in seconds
        min_segment_duration: Minimum allowed segment duration
        
    Returns:
        Validated and cleaned segment list
    """
    if not segments:
        return []
    
    validated = []
    
    for i, seg in enumerate(segments):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        
        # Validate bounds
        if start < 0:
            logger.warning(f"Segment {i}: negative start time {start:.2f}s, clamping to 0")
            start = 0
        
        if end > audio_duration:
            logger.warning(f"Segment {i}: end {end:.2f}s exceeds audio duration, clamping to {audio_duration:.2f}s")
            end = audio_duration
        
        # Validate duration
        duration = end - start
        if duration < min_segment_duration:
            logger.warning(f"Segment {i}: duration {duration:.3f}s below minimum {min_segment_duration}s, skipping")
            continue
        
        # Validate ordering
        if start >= end:
            logger.warning(f"Segment {i}: invalid ordering start={start:.2f} >= end={end:.2f}, skipping")
            continue
        
        validated.append({"start": start, "end": end})
    
    # Sort by start time
    validated.sort(key=lambda x: x["start"])
    
    # Check for overlaps
    for i in range(len(validated) - 1):
        if validated[i]["end"] > validated[i+1]["start"]:
            logger.warning(
                f"Overlapping segments detected: "
                f"[{validated[i]['start']:.2f}-{validated[i]['end']:.2f}] and "
                f"[{validated[i+1]['start']:.2f}-{validated[i+1]['end']:.2f}]"
            )
    
    logger.debug(f"Validated {len(validated)}/{len(segments)} segments")
    return validated


def clear_vad_model_cache():
    """
    Clear the cached VAD model to free memory.
    
    Useful when switching between different audio processing tasks
    or when memory needs to be freed.
    """
    global _vad_model, _vad_model_loaded
    
    if _vad_model_loaded:
        logger.info("Clearing Silero VAD model from cache")
        _vad_model = None
        _vad_model_loaded = False
        
        # Force garbage collection if available
        try:
            import gc
            gc.collect()
        except:
            pass
