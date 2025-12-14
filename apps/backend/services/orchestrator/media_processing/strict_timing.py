from __future__ import annotations
import contextlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import librosa
import numpy as np
import soundfile as sf
import torch
import torchaudio
import pyrubberband as prb

logger = logging.getLogger(__name__)


def adjust_segment_to_exact_timing(
    segment_audio_path: str,
    expected_start: float,
    expected_end: float,
    output_path: str,
    max_speed_ratio: float = 1.35,  # Don't exceed 35% speed change
    logger: Optional[logging.Logger] = None
) -> Tuple[str, bool, float]:
    """
    Force a segment to EXACTLY match its expected timing using speed adjustment.
    
    This is the core function for strict segment-by-segment synchronization.
    It ensures dubbed audio starts/ends at the exact same timestamps as the original.
    
    Args:
        segment_audio_path: Path to TTS-generated segment
        expected_start: When this segment MUST start (from original)
        expected_end: When this segment MUST end (from original)
        output_path: Where to save adjusted segment
        max_speed_ratio: Maximum speed adjustment (1.35 = 35% faster/slower)
        logger: Optional logger instance
    
    Returns:
        Tuple of (adjusted_path, quality_warning, actual_speed_ratio)
        quality_warning=True if speed adjustment exceeded recommended limits
        actual_speed_ratio shows how much compression/expansion was applied
    
    Example:
        Original Chinese: [0.0s - 2.4s] "你好，我叫李明"
        TTS English: 3.2 seconds "Hello, my name is Li Ming"
        Speed ratio: 3.2 / 2.4 = 1.33x (acceptable)
        Result: English compressed to exactly 2.4s and placed at [0.0s - 2.4s]
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    expected_duration = expected_end - expected_start
    actual_duration = get_audio_duration(Path(segment_audio_path))
    
    speed_ratio = actual_duration / expected_duration
    quality_warning = False
    
    logger.debug(
        f"Segment timing: expected={expected_duration:.2f}s, "
        f"actual={actual_duration:.2f}s, ratio={speed_ratio:.2f}x"
    )
    
    if abs(speed_ratio - 1.0) < 0.01:
        # Already matches (within 1%), just copy
        shutil.copy(segment_audio_path, output_path)
        return output_path, False, speed_ratio
    
    if speed_ratio <= max_speed_ratio:
        # Acceptable - adjust speed to fit exactly
        try:
            rubberband_to_duration(
                segment_audio_path, 
                expected_duration * 1000,  # Convert to ms
                output_path
            )
            
            if speed_ratio > 1.2:
                logger.info(
                    f"   Compressed {speed_ratio:.2f}x to fit "
                    f"{expected_duration:.2f}s (good quality)"
                )
            elif speed_ratio < 0.9:
                logger.info(
                    f"   Stretched {1/speed_ratio:.2f}x to fit "
                    f"{expected_duration:.2f}s (good quality)"
                )
        except Exception as e:
            logger.error(f"Failed to adjust segment timing: {e}")
            shutil.copy(segment_audio_path, output_path)
            quality_warning = True
    else:
        # Too much compression needed - warn and limit
        quality_warning = True
        limited_duration = actual_duration / max_speed_ratio
        
        logger.warning(
            f"⚠️  Segment needs {speed_ratio:.2f}x compression to fit "
            f"{expected_duration:.2f}s, limiting to {max_speed_ratio:.2f}x"
        )
        logger.warning(
            f"   This may cause slight timing drift. Consider using shorter TTS text."
        )
        
        try:
            rubberband_to_duration(
                segment_audio_path,
                limited_duration * 1000,
                output_path
            )
        except Exception as e:
            logger.error(f"Failed to adjust segment timing: {e}")
            shutil.copy(segment_audio_path, output_path)
    
    return output_path, quality_warning, speed_ratio


def calculate_segment_timing_stats(
    segments: List[Dict],
    tts_audio_paths: List[str]
) -> Dict[str, Any]:
    """
    Analyze timing requirements for all segments.
    
    Returns statistics to help determine if strict timing is feasible.
    """
    stats = {
        "total_segments": len(segments),
        "segments_need_compression": 0,
        "segments_need_stretching": 0,
        "max_compression_ratio": 1.0,
        "max_stretch_ratio": 1.0,
        "avg_speed_ratio": 0.0,
        "quality_warnings_expected": 0,
        "timing_adjustments": []
    }
    
    speed_ratios = []
    
    for i, (seg, audio_path) in enumerate(zip(segments, tts_audio_paths)):
        expected_duration = seg["end"] - seg["start"]
        actual_duration = get_audio_duration(Path(audio_path))
        speed_ratio = actual_duration / expected_duration
        
        speed_ratios.append(speed_ratio)
        
        adjustment = {
            "index": i,
            "expected_duration": expected_duration,
            "actual_duration": actual_duration,
            "speed_ratio": speed_ratio,
            "needs_compression": speed_ratio > 1.0,
            "needs_stretching": speed_ratio < 1.0
        }
        
        if speed_ratio > 1.0:
            stats["segments_need_compression"] += 1
            stats["max_compression_ratio"] = max(stats["max_compression_ratio"], speed_ratio)
        elif speed_ratio < 1.0:
            stats["segments_need_stretching"] += 1
            stats["max_stretch_ratio"] = max(stats["max_stretch_ratio"], 1 / speed_ratio)
        
        if speed_ratio > 1.35:
            stats["quality_warnings_expected"] += 1
            adjustment["quality_warning"] = True
        
        stats["timing_adjustments"].append(adjustment)
    
    stats["avg_speed_ratio"] = sum(speed_ratios) / len(speed_ratios) if speed_ratios else 1.0
    
    return stats


def concatenate_audio_strict_timing(
    segments: List[Dict],
    output_file: str,
    target_duration: float,
    max_speed_ratio: float = 1.35,
    translation_segments: Optional[List[Dict]] = None
) -> Tuple[str, Optional[List[Dict]], int]:
    """
    Concatenate audio with STRICT segment-by-segment timing enforcement.
    
    This function ensures perfect lip-sync by forcing each dubbed segment
    to occupy the EXACT same timestamps as the original speech.
    
    Args:
        segments: Original segment timings with 'start', 'end', 'audio_url'
        output_file: Path for output concatenated audio
        target_duration: Total video duration
        max_speed_ratio: Maximum allowed speed adjustment (default 1.35 = 35%)
        translation_segments: Optional list to update with final timings
    
    Returns:
        Tuple of (output_path, updated_translation_segments, quality_warnings_count)
    
    Process:
        1. For each segment, calculate required speed adjustment
        2. Compress or stretch TTS audio to EXACTLY match original timing
        3. Place adjusted segments at their EXACT original timestamps
        4. Add silence only in gaps where there was no original speech
        5. Result: Perfect segment-by-segment synchronization
    
    Example:
        Original: [0-2.4s] Chinese, [5.0-7.5s] Chinese, [10.0-12.0s] Chinese
        Dubbed:   [0-2.4s] English, [5.0-7.5s] English, [10.0-12.0s] English
        Silence:  [2.4-5.0s], [7.5-10.0s] (preserves original gaps)
    """
    if len(segments) < 1:
        raise ValueError("At least 1 segment is required")
    
    logger.info("\n" + "="*60)
    logger.info("🎯 STRICT SEGMENT-BY-SEGMENT TIMING SYNCHRONIZATION")
    logger.info("="*60)
    
    # Extract audio paths
    tts_audio_paths = [seg["audio_url"] for seg in segments]
    
    # Step 1: Analyze timing requirements
    stats = calculate_segment_timing_stats(segments, tts_audio_paths)
    
    logger.info(f"\n📊 Timing Analysis:")
    logger.info(f"   Total segments: {stats['total_segments']}")
    logger.info(f"   Need compression: {stats['segments_need_compression']}")
    logger.info(f"   Need stretching: {stats['segments_need_stretching']}")
    logger.info(f"   Max compression: {stats['max_compression_ratio']:.2f}x")
    logger.info(f"   Average speed ratio: {stats['avg_speed_ratio']:.2f}x")
    
    if stats['quality_warnings_expected'] > 0:
        logger.warning(
            f"\n⚠️  {stats['quality_warnings_expected']} segment(s) need >{max_speed_ratio:.2f}x compression"
        )
        logger.warning(
            f"   This may affect audio quality. Consider using more concise translations."
        )
    
    # Step 2: Adjust each segment to exact timing
    adjusted_segments = []
    quality_warnings = 0
    temp_dir = Path(tempfile.mkdtemp())
    
    logger.info(f"\n🔧 Adjusting segments to exact timing:")
    
    for i, seg in enumerate(segments):
        expected_start = seg["start"]
        expected_end = seg["end"]
        expected_duration = expected_end - expected_start
        
        adjusted_path = temp_dir / f"strict_timing_seg_{i:03d}.wav"
        
        # Force segment to exact timing
        _, quality_warning, speed_ratio = adjust_segment_to_exact_timing(
            seg["audio_url"],
            expected_start,
            expected_end,
            str(adjusted_path),
            max_speed_ratio=max_speed_ratio,
            logger=logger
        )
        
        if quality_warning:
            quality_warnings += 1
        
        # Verify adjusted duration
        actual_adjusted_duration = get_audio_duration(adjusted_path)
        duration_error = abs(actual_adjusted_duration - expected_duration)
        
        if duration_error > 0.05:  # More than 50ms error
            logger.warning(
                f"   Segment {i}: Duration error {duration_error:.3f}s after adjustment"
            )
        
        adjusted_segments.append({
            "audio_path": str(adjusted_path),
            "start": expected_start,
            "end": expected_end,
            "duration": expected_duration,
            "original_duration": get_audio_duration(Path(seg["audio_url"])),
            "speed_ratio": speed_ratio
        })
        
        logger.info(
            f"   Segment {i}: [{expected_start:.2f}-{expected_end:.2f}s] "
            f"adjusted {speed_ratio:.2f}x"
        )
    
    # Step 3: Build timeline with EXACT placements
    logger.info(f"\n🎵 Building synchronized timeline:")
    
    timeline = []
    current_time = 0.0
    
    for i, adj_seg in enumerate(adjusted_segments):
        # Add silence before segment if there's a gap
        gap_duration = adj_seg["start"] - current_time
        
        if gap_duration > 0.01:  # More than 10ms gap
            timeline.append({
                "type": "silence",
                "duration": gap_duration,
                "start": current_time,
                "end": adj_seg["start"]
            })
            logger.info(f"   Silence: [{current_time:.2f}-{adj_seg['start']:.2f}s] ({gap_duration:.2f}s)")
            current_time = adj_seg["start"]
        
        # Add segment at exact position
        timeline.append({
            "type": "audio",
            "path": adj_seg["audio_path"],
            "start": adj_seg["start"],
            "end": adj_seg["end"],
            "duration": adj_seg["duration"]
        })
        logger.info(
            f"   Audio: [{adj_seg['start']:.2f}-{adj_seg['end']:.2f}s] "
            f"(ratio: {adj_seg['speed_ratio']:.2f}x)"
        )
        
        current_time = adj_seg["end"]
    
    # Add final silence if needed
    if current_time < target_duration:
        final_gap = target_duration - current_time
        timeline.append({
            "type": "silence",
            "duration": final_gap,
            "start": current_time,
            "end": target_duration
        })
        logger.info(f"   Final silence: [{current_time:.2f}-{target_duration:.2f}s] ({final_gap:.2f}s)")
    
    # Step 4: Concatenate timeline using ffmpeg
    logger.info(f"\n🔨 Concatenating {len(timeline)} elements...")
    _concatenate_timeline_ffmpeg(timeline, output_file)
    
    # Step 5: Update translation segments if provided
    if translation_segments and len(translation_segments) == len(segments):
        for i, seg in enumerate(segments):
            translation_segments[i]["start"] = float(seg["start"])
            translation_segments[i]["end"] = float(seg["end"])
    
    # Step 6: Verify final output
    final_duration = get_audio_duration(output_file)
    duration_error = abs(final_duration - target_duration)
    
    logger.info("\n" + "="*60)
    if duration_error < 0.1:
        logger.info("✅ STRICT TIMING SYNCHRONIZATION COMPLETE")
    else:
        logger.warning(f"⚠️ TIMING COMPLETE (duration error: {duration_error:.2f}s)")
    
    logger.info(f"   Final duration: {final_duration:.2f}s (target: {target_duration:.2f}s)")
    logger.info(f"   Quality warnings: {quality_warnings}/{len(segments)}")
    logger.info("="*60)
    
    # Cleanup temp directory
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp dir: {e}")
    
    return output_file, translation_segments, quality_warnings


def _concatenate_timeline_ffmpeg(timeline: List[Dict], output_file: str):
    """
    Helper function to concatenate timeline elements using ffmpeg.
    
    Args:
        timeline: List of {"type": "audio"|"silence", ...} dicts
        output_file: Output file path
    """
    import tempfile
    
    silence_temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Get audio properties from first audio segment
        first_audio = next(t["path"] for t in timeline if t["type"] == "audio")
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels',
            '-of', 'json',
            first_audio
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        audio_info = json.loads(probe_result.stdout)
        sample_rate = audio_info['streams'][0]['sample_rate']
        channels = audio_info['streams'][0]['channels']
        
        # Create silence files and build file list
        filelist_path = silence_temp_dir / "filelist.txt"
        silence_counter = 0
        
        with open(filelist_path, 'w') as f:
            for element in timeline:
                if element['type'] == 'silence':
                    if element['duration'] > 0.001:  # Only create if > 1ms
                        silence_file = silence_temp_dir / f"silence_{silence_counter}.wav"
                        silence_cmd = [
                            'ffmpeg', '-y', '-v', 'error',
                            '-f', 'lavfi',
                            '-i', f'anullsrc=channel_layout={"stereo" if channels == 2 else "mono"}:sample_rate={sample_rate}',
                            '-t', str(element['duration']),
                            str(silence_file)
                        ]
                        subprocess.run(silence_cmd, capture_output=True, text=True, check=True)
                        f.write(f"file '{silence_file.absolute()}'\n")
                        silence_counter += 1
                else:
                    # Audio segment
                    f.write(f"file '{Path(element['path']).absolute()}'\n")
        
        # Final concatenation
        cmd = [
            'ffmpeg', '-y', '-v', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(filelist_path),
            '-c', 'copy',
            str(output_file)
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
    finally:
        # Clean up temp dir
        shutil.rmtree(silence_temp_dir, ignore_errors=True)
