import asyncio
import os
import shutil
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, AsyncGenerator
from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class TaskState:
    task_id: str
    url: str
    format_type: str
    quality: str
    ext: str
    output_dir: Path
    stage: str = "queued"
    progress: float = 0.0
    speed: Optional[str] = None
    eta: Optional[str] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    message: Optional[str] = None
    result_filepath: Optional[Path] = None
    filename: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    subscribers: List[asyncio.Queue] = field(default_factory=list)
    completed: bool = False

class DownloadManager:
    def __init__(self):
        self._tasks: Dict[str, TaskState] = {}
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
        self._lock = asyncio.Lock()

    async def create_task(self, task_id: str, url: str, format_type: str, quality: str, ext: str) -> TaskState:
        output_dir = settings.DOWNLOAD_DIR / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        task = TaskState(
            task_id=task_id,
            url=url,
            format_type=format_type,
            quality=quality,
            ext=ext,
            output_dir=output_dir,
        )
        async with self._lock:
            self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[TaskState]:
        return self._tasks.get(task_id)

    def update_progress(
        self,
        task_id: str,
        stage: str,
        progress: float,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        message: Optional[str] = None,
    ):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.stage = stage
        task.progress = round(progress, 1)
        task.speed = speed
        task.eta = eta
        task.downloaded_bytes = downloaded_bytes
        task.total_bytes = total_bytes
        task.message = message

        payload = {
            "task_id": task_id,
            "stage": stage,
            "progress": task.progress,
            "speed": speed,
            "eta": eta,
            "message": message,
        }
        for queue in list(task.subscribers):
            try:
                queue.put_nowait(payload)
            except Exception:
                pass

    def complete_task(self, task_id: str, filepath: Path, filename: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.stage = "completed"
        task.progress = 100.0
        task.result_filepath = filepath
        task.filename = filename
        task.completed = True

        file_url = f"/api/v1/download/file/{task_id}"
        payload = {
            "task_id": task_id,
            "stage": "completed",
            "progress": 100.0,
            "file_url": file_url,
            "filename": filename,
            "message": "File ready for download",
        }
        for queue in list(task.subscribers):
            try:
                queue.put_nowait(payload)
            except Exception:
                pass

    def fail_task(self, task_id: str, error: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.stage = "failed"
        task.error = error
        task.completed = True

        payload = {
            "task_id": task_id,
            "stage": "failed",
            "progress": 0.0,
            "error": error,
        }
        for queue in list(task.subscribers):
            try:
                queue.put_nowait(payload)
            except Exception:
                pass

    async def subscribe(self, task_id: str) -> AsyncGenerator[dict, None]:
        task = self._tasks.get(task_id)
        if not task:
            yield {"stage": "failed", "error": "Task not found"}
            return

        queue: asyncio.Queue = asyncio.Queue()
        task.subscribers.append(queue)

        # Emit initial current state immediately
        initial_payload = {
            "task_id": task_id,
            "stage": task.stage,
            "progress": task.progress,
            "speed": task.speed,
            "eta": task.eta,
            "message": task.message,
            "error": task.error,
        }
        if task.completed and task.result_filepath:
            initial_payload["file_url"] = f"/api/v1/download/file/{task_id}"
            initial_payload["filename"] = task.filename
        yield initial_payload

        try:
            while True:
                payload = await queue.get()
                yield payload
                if payload.get("stage") in ("completed", "failed"):
                    break
        finally:
            if queue in task.subscribers:
                task.subscribers.remove(queue)

    def cleanup_task(self, task_id: str):
        task = self._tasks.pop(task_id, None)
        if task and task.output_dir.exists():
            try:
                shutil.rmtree(task.output_dir, ignore_errors=True)
                logger.info(f"Cleaned up directory for task {task_id}")
            except Exception as e:
                logger.warning(f"Error cleaning task {task_id}: {e}")

download_manager = DownloadManager()
