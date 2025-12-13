# CODE TO ADD #2: Copy to Persistent Storage
# Location: apps/backend/services/orchestrator/app/main.py 
# Add AFTER line: workspace.maybe_dump_json("final_result.json", final_result)
# Which is around line 2345

        # FIX: Copy to persistent storage if on Modal
        try:
            await copy_to_persistent_storage(workspace.workspace_id, workspace.workspace)
        except Exception as exc:
            logger.error(f"Failed to persist outputs: {exc}", exc_info=True)
