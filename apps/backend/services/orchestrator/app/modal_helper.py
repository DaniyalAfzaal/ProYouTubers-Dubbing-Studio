"""
Helper function to process batch with Modal Functions
"""

async def _process_batch_with_modal(
    batch_id: str,
    video_inputs: list,
    options: dict
):
    """
    Process batch using Modal Functions - true 10-GPU parallelization.
    Each video gets its own L4 GPU.
    """
    job = BULK_JOBS.get(batch_id)
    if not job:
        return
    
    try:
        logger.info(f"🚀 Calling Modal.map() for batch {batch_id}...")
        
        # Update job status
        async with job.lock:
            for video in job.videos:
                video['status'] = 'processing'
        
        # Call Modal.map() for parallel processing
        # This will spin up up to 10 L4 GPUs simultaneously
        results = list(process_single_video_modal.map(
            video_inputs,
            [options] * len(video_inputs),
            [batch_id] * len(video_inputs),
            list(range(len(video_inputs)))
        ))
        
        # Update job with results
        async with job.lock:
            for result in results:
                index = result["index"]
                if index < len(job.videos):
                    if result["status"] == "success":
                        job.completed += 1
                        job.videos[index]['status'] = 'completed'
                        job.videos[index]['result'] = result.get('result', {})
                        job.videos[index]['output_dir'] = result.get('output_dir')
                    else:
                        job.failed += 1
                        job.videos[index]['status'] = 'failed'
                        job.videos[index]['error'] = result.get('error', 'Unknown error')
        
        duration = time.time() - job.timestamp
        logger.info(
            f"✅ Batch {batch_id} completed in {duration:.1f}s: "
            f"{job.completed} success, {job.failed} failed"
        )
        
    except Exception as e:
        logger.error(f"❌ Batch {batch_id} failed: {e}", exc_info=True)
        async with job.lock:
            for video in job.videos:
                if video['status'] == 'processing':
                    video['status'] = 'failed'
                    video['error'] = str(e)
            job.failed = job.total
