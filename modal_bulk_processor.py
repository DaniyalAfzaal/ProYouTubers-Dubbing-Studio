"""
Modal Bulk Dubbing Processor - Phase 2
True 10-GPU Parallelization using Modal Functions

This module enables processing up to 10 videos simultaneously,
each on its own L4 GPU, for maximum throughput.
"""

import modal
import os
import sys
import json
from pathlib import Path

# Create Modal app
app = modal.App("proyoutubers-bulk-dubbing")

# Volume for storing results (persists across function calls)
results_volume = modal.Volume.from_name("bulk-dubbing-results", create_if_missing=True)

# Define the container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "git",
        "ffmpeg",
        "libsndfile1",
        "build-essential",
    )
    .pip_install(
        "fastapi==0.115.6",
        "uvicorn[standard]==0.34.0",
        "python-multipart==0.0.20",
        "httpx==0.28.1",
        "pydantic==2.10.4",
        "pydantic-settings==2.7.0",
        "yt-dlp==2024.12.13",
        "deep-translator==1.11.4",
        "openai==1.59.6",
        "anthropic==0.42.0",
        "google-generativeai==0.8.3",
        "audio-separator[gpu]==0.39.0",
        "faster-whisper==1.1.0",
        "whisperx @ git+https://github.com/m-bain/whisperX.git@v3.1.6",
        "torch==2.6.0",
        "torchaudio==2.6.0",
        "transformers==4.47.1",
        "diffusers==0.32.2",
        "accelerate==1.2.1",
        "pyrubberband==0.3.0",
        "soundfile==0.12.1",
        "librosa==0.10.2",
        "numpy<2.0.0",
        "scipy==1.14.1",
        "scikit-learn==1.6.0",
    )
)

@app.function(
    gpu="L4",  # Each function gets its own L4 GPU (24GB VRAM)
    timeout=900,  # 15 minutes max per video
    concurrency_limit=10,  # Max 10 functions running simultaneously
    volumes={"/results": results_volume},
    secrets=[modal.Secret.from_name("hf-token")],
    image=image,
    cpu=4.0,  # 4 vCPUs
    memory=16384,  # 16GB RAM
)
def process_single_video(
    video_input: dict,
    options: dict,
    batch_id: str,
    video_index: int,
    repo_url: str = "https://github.com/DaniyalAfzaal/ProYouTubers-Dubbing-Studio.git"
) -> dict:
    """
    Process a single video with complete dubbing pipeline.
    
    Args:
        video_input: {url: str} or {file_data: bytes, filename: str}
        options: All dubbing options (languages, models, etc.)
        batch_id: Unique batch identifier
        video_index: Index in the batch (0-based)
        repo_url: GitHub repo to clone
    
    Returns:
        {status: "success"|"error", index: int, result: dict, error: str}
    """
    print(f"[GPU-{video_index}] Starting video {video_index} in batch {batch_id}")
    
    try:
        # Clone repository
        workspace = "/workspace"
        if not Path(workspace).exists():
            print(f"[GPU-{video_index}] Cloning repository...")
            os.system(f"git clone {repo_url} {workspace}")
        
        sys.path.insert(0, workspace)
        os.chdir(workspace)
        
        # Import dubbing pipeline
        from apps.backend.pipeline_runner import run_dubbing_pipeline
        
        # Prepare input
        input_source = None
        if "url" in video_input:
            input_source = video_input["url"]
            print(f"[GPU-{video_index}] Processing URL: {input_source}")
        elif "file_data" in video_input:
            # Save uploaded file to temp
            temp_dir = Path("/tmp/uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / f"video_{video_index}_{video_input['filename']}"
            temp_file.write_bytes(video_input["file_data"])
            input_source = str(temp_file)
            print(f"[GPU-{video_index}] Processing uploaded file: {video_input['filename']}")
        else:
            raise ValueError("No valid input provided")
        
        # Run dubbing pipeline
        print(f"[GPU-{video_index}] Starting dubbing pipeline...")
        result = run_dubbing_pipeline(
            source=input_source,
            **options
        )
        
        # Save results to volume
        output_dir = Path(f"/results/{batch_id}/video_{video_index}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[GPU-{video_index}] Saving results to volume...")
        
        # Copy result files to volume
        result_files = {}
        for lang, lang_result in result.get("languages", {}).items():
            if lang_result.get("video_url"):
                src = Path(lang_result["video_url"])
                if src.exists():
                    dst = output_dir / f"dubbed_video_{lang}.mp4"
                    os.system(f"cp '{src}' '{dst}'")
                    result_files[f"video_{lang}"] = str(dst)
            
            if lang_result.get("dubbed_audio_url"):
                src = Path(lang_result["dubbed_audio_url"])
                if src.exists():
                    dst = output_dir / f"dubbed_audio_{lang}.wav"
                    os.system(f"cp '{src}' '{dst}'")
                    result_files[f"audio_{lang}"] = str(dst)
        
        # Save metadata
        metadata = {
            "batch_id": batch_id,
            "video_index": video_index,
            "input": video_input.get("url") or video_input.get("filename"),
            "result": result,
            "files": result_files
        }
        
        metadata_file = output_dir / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Commit volume changes
        results_volume.commit()
        
        print(f"[GPU-{video_index}] ✅ Completed successfully!")
        
        return {
            "status": "success",
            "index": video_index,
            "result": result,
            "output_dir": str(output_dir),
            "files": result_files
        }
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[GPU-{video_index}] ❌ Error: {error_msg}")
        
        return {
            "status": "error",
            "index": video_index,
            "error": error_msg
        }

@app.local_entrypoint()
def test_bulk():
    """Test the bulk processor with sample videos"""
    print("Testing bulk processor with 3 sample videos...")
    
    # Sample videos (replace with actual URLs)
    videos = [
        {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        {"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"},
        {"url": "https://www.youtube.com/watch?v=9bZkp7q19f0"},
    ]
    
    options = {
        "target_languages": ["en"],
        "source_language": "auto",
        "asr_model": "whisperx",
        "translation_model": "deep_translator",
        "tts_model": "chatterbox",
        "translation_strategy": "direct",
        "dubbing_strategy": "keep_bg_music",
    }
    
    batch_id = "test-batch-001"
    
    # Process in parallel using .map()
    print(f"Starting parallel processing of {len(videos)} videos...")
    results = list(process_single_video.map(
        videos,
        [options] * len(videos),
        [batch_id] * len(videos),
        list(range(len(videos)))
    ))
    
    # Print results
    print("\n" + "="*60)
    print("BATCH RESULTS")
    print("="*60)
    
    for result in results:
        if result["status"] == "success":
            print(f"✅ Video {result['index']}: SUCCESS")
            print(f"   Output: {result['output_dir']}")
        else:
            print(f"❌ Video {result['index']}: FAILED")
            print(f"   Error: {result['error'][:100]}...")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n{success_count}/{len(videos)} videos completed successfully")
    
    return results
