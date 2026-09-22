import asyncio
import os
import shutil
import time
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

async def cleanup_task_directory(task_id: str, delay_seconds: int = 300):
    """
    Cleans up the temporary folder for a given task after a delay
    to ensure the file transfer has finished and handles are closed.
    """
    await asyncio.sleep(delay_seconds)
    target_dir = settings.DOWNLOAD_DIR / task_id
    if target_dir.exists():
        try:
            shutil.rmtree(target_dir, ignore_errors=True)
            logger.info(f"Purged transient folder: {target_dir}")
        except Exception as e:
            logger.error(f"Failed to purge folder {target_dir}: {e}")

async def start_periodic_cleanup_loop():
    """
    Background worker that runs every CLEANUP_INTERVAL_SECONDS to remove orphaned folders.
    """
    logger.info("Starting transient storage garbage collection loop...")
    while True:
        try:
            await asyncio.sleep(settings.CLEANUP_INTERVAL_SECONDS)
            now = time.time()
            if not settings.DOWNLOAD_DIR.exists():
                continue

            for item in settings.DOWNLOAD_DIR.iterdir():
                if item.is_dir():
                    try:
                        mtime = item.stat().st_mtime
                        if now - mtime > settings.TASK_RETENTION_SECONDS:
                            shutil.rmtree(item, ignore_errors=True)
                            logger.info(f"Swept expired directory: {item.name}")
                    except Exception as e:
                        logger.debug(f"Could not stat/remove {item}: {e}")
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}", exc_info=True)
