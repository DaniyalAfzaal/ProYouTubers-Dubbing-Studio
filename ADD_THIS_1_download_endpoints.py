# CODE TO ADD #1: Download Endpoints
# Location: apps/backend/services/orchestrator/app/main.py
# Add AFTER the @app.get(OPTIONS_ROUTE) endpoint (around line 1250)

@app.get(f"{API_PREFIX}/download/{{video_id}}/{{filename}}")
async def download_video(video_id: str, filename: str):
    """Download a completed video from persistent storage or local directory"""
    from fastapi.responses import FileResponse
    
    # Try persistent storage first (Modal volume)
    persistent_root = Path("/persistent-outputs")
    if persistent_root.exists():
        video_path = persistent_root / video_id / filename
        if video_path.exists():
            return FileResponse(
                path=str(video_path),
                filename=filename,
                media_type="video/mp4" if filename.endswith(".mp4") else "application/octet-stream"
            )
    
    # Fallback to local outs directory
    local_path = BASE / "outs" / video_id / filename
    if local_path.exists():
        return FileResponse(
            path=str(local_path),
            filename=filename,
            media_type="video/mp4" if filename.endswith(".mp4") else "application/octet-stream"
        )
    
    raise HTTPException(404, f"Video not found: {filename}")


@app.get(f"{API_PREFIX}/outputs/{{video_id}}")
async def list_outputs(video_id: str):
    """List all output files for a video ID"""
    # Try persistent storage first
    persistent_root = Path("/persistent-outputs")
    video_dir = None
    
    if persistent_root.exists():
        test_dir = persistent_root / video_id
        if test_dir.exists():
            video_dir = test_dir
    
    # Fallback to local
    if not video_dir:
        video_dir = BASE / "outs" / video_id
        if not video_dir.exists():
            raise HTTPException(404, f"No outputs found for: {video_id}")
    
    files = []
    for file_path in video_dir.glob("*"):
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "download_url": f"/api/download/{video_id}/{file_path.name}"
            })
    
    return {"video_id": video_id, "files": files}
