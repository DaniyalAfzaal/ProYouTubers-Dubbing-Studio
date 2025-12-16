"""
VAD Offset Correction Module
============================

Automatically detects real speech start to correct inaccurate VAD timestamps.

This module fixes the common issue where Voice Activity Detection (VAD) detects
pre-speech sounds (breaths, noise) as speech start, causing dubbed audio to play
too early. It analyzes audio energy to find the real sustained speech start.

Usage:
    auto_offset, manual_offset, total_offset = calculate_vad_offset(
        audio_path=vocals_path,
        vad_first_segment_start=0.03,
        config=general_cfg
    )
    apply_offset_to_segments(segments, total_offset)

Author: Bluez AI Dubbing System
License: MIT
"""

from __future__ import annotations
import logging
import numpy as np
import librosa
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def detect_speech_start_time(
    audio_path: Path | str,
    silence_threshold_percentile: int = 10,
    energy_multiplier: float = 3.0,
    min_sustained_duration: float = 0.3
) -> float:
    """
    Detect when real speech starts by analyzing audio energy.
    
    Uses RMS energy analysis to distinguish sustained speech from transient
    sounds like breaths, clicks, or background noise.
    
    Args:
        audio_path: Path to audio file (vocals track recommended)
        silence_threshold_percentile: Percentile for noise floor calculation (10th = conservative)
        energy_multiplier: Multiplier above noise floor for speech detection (3.0 = balanced)
        min_sustained_duration: Minimum duration for valid speech in seconds (0.3s filters transients)
        
    Returns:
        Timestamp in seconds when sustained speech starts (0.0 if detection fails)
        
    Example:
        >>> speech_start = detect_speech_start_time("vocals.wav")
        >>> print(f"Real speech starts at {speech_start:.2f}s")
        Real speech starts at 0.79s
    """
    try:
        # Load audio at 16kHz (WhisperX standard)
        audio, sr = librosa.load(str(audio_path), sr=16000)
        
        if len(audio) == 0:
            logger.warning("Empty audio file, cannot detect speech start")
            return 0.0
        
        # Compute RMS energy with small hop for temporal precision
        hop_length = 512  # ~32ms resolution at 16kHz
        energy = librosa.feature.rms(
            y=audio,
            frame_length=2048,
            hop_length=hop_length
        )[0]
        
        # Calculate adaptive noise floor (10th percentile of energy)
        noise_floor = np.percentile(energy, silence_threshold_percentile)
        speech_threshold = noise_floor * energy_multiplier
        
        logger.debug(
            f"Silence detection: noise_floor={noise_floor:.4f}, "
            f"speech_threshold={speech_threshold:.4f}, "
            f"audio_duration={len(audio)/sr:.2f}s"
        )
        
        # Calculate window size for sustained energy check
        window_frames = int((min_sustained_duration * sr) / hop_length)
        
        if window_frames >= len(energy):
            logger.warning("Audio too short for sustained speech detection")
            return 0.0
        
        # Find first sustained energy period
        for i in range(len(energy) - window_frames):
            window = energy[i:i + window_frames]
            
            # Check if sustained above threshold
            # Mean must be above speech threshold AND minimum above 1.5x noise
            if np.mean(window) > speech_threshold and np.min(window) > noise_floor * 1.5:
                speech_start = (i * hop_length) / sr
                logger.info(f"🎯 Detected real speech start at {speech_start:.2f}s")
                return speech_start
        
        # No sustained speech found
        logger.warning("Could not detect sustained speech in audio, returning 0.0s")
        return 0.0
        
    except Exception as e:
        logger.error(f"Silence detection failed: {e}", exc_info=True)
        return 0.0


def calculate_vad_offset(
    audio_path: Path | str,
    vad_first_segment_start: float,
    config: dict
) -> Tuple[float, float, float]:
    """
    Calculate VAD offset using automatic silence detection + manual override.
    
    Combines two approaches:
    1. Automatic: Detects real speech start via energy analysis
    2. Manual: User-configured offset from config file
    
    Args:
        audio_path: Path to vocals audio file
        vad_first_segment_start: Start time from VAD/ASR (e.g., 0.03s)
        config: Configuration dict with 'vad.timestamp_correction' settings
        
    Returns:
        Tuple of (auto_offset, manual_offset, total_offset) in seconds
        
    Example:
        >>> auto, manual, total = calculate_vad_offset(
        ...     "vocals.wav",
        ...     vad_first_segment_start=0.03,
        ...     config={"vad": {"timestamp_correction": {"enabled": True}}}
        ... )
        >>> print(f"Offsets: auto={auto:.2f}s, manual={manual:.2f}s, total={total:.2f}s")
        Offsets: auto=0.76s, manual=0.00s, total=0.76s
    """
    correction_cfg = config.get("vad", {}).get("timestamp_correction", {})
    
    # Check if enabled
    if not correction_cfg.get("enabled", False):
        logger.info("VAD timestamp correction disabled in config")
        return (0.0, 0.0, 0.0)
    
    # Auto-detect silence
    auto_offset = 0.0
    if correction_cfg.get("auto_detect_silence", True):
        try:
            real_speech_start = detect_speech_start_time(
                audio_path,
                silence_threshold_percentile=correction_cfg.get("silence_threshold_percentile", 10),
                energy_multiplier=correction_cfg.get("energy_multiplier", 3.0)
            )
            
            # Calculate offset (only if positive and significant)
            raw_offset = real_speech_start - vad_first_segment_start
            
            if raw_offset < 0:
                logger.info(f"✅ VAD ahead of detection (offset={raw_offset:.3f}s), no correction needed")
                auto_offset = 0.0
            elif raw_offset < 0.1:
                logger.info(f"✅ VAD timestamps accurate (offset={raw_offset:.3f}s < 0.1s threshold)")
                auto_offset = 0.0
            else:
                auto_offset = raw_offset
                logger.info(
                    f"📊 Auto-detected offset: "
                    f"VAD={vad_first_segment_start:.2f}s, "
                    f"Real={real_speech_start:.2f}s, "
                    f"Offset={auto_offset:.2f}s"
                )
                
        except Exception as e:
            logger.error(f"Auto-detection failed: {e}")
            auto_offset = 0.0
    
    # Manual offset
    manual_offset = float(correction_cfg.get("manual_offset_seconds", 0.0))
    
    # Combine
    total_offset = auto_offset + manual_offset
    
    # Logging
    if manual_offset != 0:
        logger.info(f"   Manual offset: {manual_offset:+.2f}s")
    
    if total_offset > 0:
        logger.info(f"🎯 Total VAD correction: {total_offset:+.2f}s")
    elif total_offset == 0 and auto_offset == 0 and manual_offset == 0:
        logger.info("✅ No VAD offset correction needed")
    
    return (auto_offset, manual_offset, total_offset)


def apply_offset_to_segments(segments: list, offset: float) -> None:
    """
    Apply time offset to all segments in-place.
    
    Modifies the .start and .end attributes of each segment by adding
    the specified offset. Clamps negative timestamps to 0s to prevent
    video player errors.
    
    Args:
        segments: List of segment objects with .start and .end attributes
        offset: Offset in seconds to add (can be negative)
        
    Example:
        >>> segments = [Segment(start=0.03, end=5.94)]
        >>> apply_offset_to_segments(segments, 0.76)
        >>> print(f"New start: {segments[0].start:.2f}s")
        New start: 0.79s
        
        >>> segments = [Segment(start=0.5, end=2.0)]
        >>> apply_offset_to_segments(segments, -0.8)  # Large negative
        >>> print(f"Clamped: {segments[0].start:.2f}s")
        Clamped: 0.00s
    """
    if offset == 0:
        return
    
    for seg in segments:
        seg.start += offset
        seg.end += offset
        
        # Clamp negative timestamps (video players can't handle negative times)
        if seg.start < 0:
            logger.warning(
                f"Offset {offset:+.2f}s pushed segment start to {seg.start:.2f}s, "
                f"clamping to 0.0s and preserving duration"
            )
            duration = seg.end - seg.start
            seg.start = 0.0
            seg.end = max(0.0, duration)  # Also clamp end if needed
    
    logger.debug(f"Applied {offset:+.2f}s offset to {len(segments)} segments")

