import asyncio
import uuid
import json
import logging
import re
import shutil
from urllib.parse import quote
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.schemas.download import (
    InfoRequest,
    VideoInfoResponse,
    DownloadStartRequest,
    DownloadStartResponse,
    SaveToDownloadsRequest,
    SaveToDownloadsResponse,
    PathActionRequest,
    PathActionResponse,
)
from app.services.ytdl_service import YtDlpService, is_valid_youtube_url
from app.services.download_manager import download_manager
from app.services.cleanup_service import cleanup_task_directory
from app.services.file_service import (
    get_user_downloads_dir,
    get_unique_filename,
    open_in_file_explorer,
    open_file_native,
    choose_save_file_windows,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["download"])

@router.post("/info", response_model=VideoInfoResponse)
async def get_video_info(payload: InfoRequest):
    url = payload.url.strip()
    if not is_valid_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide a valid YouTube video or Shorts URL."
        )

    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, YtDlpService.fetch_video_info, url)
        return info
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching video info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve video metadata: {str(e)}"
        )

@router.post("/download/start", response_model=DownloadStartResponse)
async def start_download(payload: DownloadStartRequest, background_tasks: BackgroundTasks):
    url = payload.url.strip()
    if not is_valid_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid YouTube URL."
        )

    task_id = str(uuid.uuid4())
    task = await download_manager.create_task(
        task_id=task_id,
        url=url,
        format_type=payload.format_type,
        quality=payload.quality,
        ext=payload.ext,
    )

    # Spawn download worker in threadpool
    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        None,
        YtDlpService.run_download_task,
        task_id,
        url,
        payload.format_type,
        payload.quality,
        task.output_dir
    )

    return DownloadStartResponse(
        task_id=task_id,
        status="queued",
        message="Download initialized successfully."
    )

@router.get("/download/progress/{task_id}")
async def get_download_progress(task_id: str):
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task ID not found")

    async def event_generator():
        async for update in download_manager.subscribe(task_id):
            yield {
                "event": "progress" if update.get("stage") != "completed" else "complete",
                "data": json.dumps(update)
            }

    return EventSourceResponse(event_generator())

@router.get("/download/file/{task_id}")
async def download_file(task_id: str, background_tasks: BackgroundTasks):
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")

    if not task.completed or not task.result_filepath or not task.result_filepath.exists():
        if task.stage == "failed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=task.error or "Download failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is still processing or unavailable")

    filename = task.filename or task.result_filepath.name
    media_type = "audio/mpeg" if task.format_type == "audio" else "video/mp4"

    # Schedule cleanup of the directory with a safe delay (5 minutes) so active transfers are not interrupted
    background_tasks.add_task(cleanup_task_directory, task_id, delay_seconds=300)

    # RFC 6266 / RFC 5987 compliant Content-Disposition header
    # ASCII-safe fallback prevents Latin-1 UnicodeEncodeError on emojis/Unicode in Uvicorn
    ascii_name = re.sub(r'[^\x20-\x7E]', '', filename).replace('"', '').strip()
    if not ascii_name:
        ascii_name = "audio.mp3" if task.format_type == "audio" else "video.mp4"
    encoded_name = quote(filename)
    content_disposition = f'attachment; filename="{ascii_name}"; filename*=utf-8\'\'{encoded_name}'

    return FileResponse(
        path=task.result_filepath,
        media_type=media_type,
        headers={
            "Content-Disposition": content_disposition,
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )

@router.post("/download/save-to-downloads", response_model=SaveToDownloadsResponse)
async def save_to_downloads(payload: SaveToDownloadsRequest):
    task = download_manager.get_task(payload.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")

    if not task.completed or not task.result_filepath or not task.result_filepath.exists():
        if task.stage == "failed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=task.error or "Download failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is still processing or unavailable")

    try:
        downloads_dir = get_user_downloads_dir()
        filename = task.filename or task.result_filepath.name
        dest_path = get_unique_filename(downloads_dir, filename)

        # Copy the processed file to user's downloads folder
        shutil.copy2(task.result_filepath, dest_path)
        logger.info(f"File successfully saved to downloads: {dest_path}")

        return SaveToDownloadsResponse(
            success=True,
            path=str(dest_path),
            filename=dest_path.name
        )
    except Exception as e:
        logger.error(f"Failed to save file to downloads: {e}", exc_info=True)
        return SaveToDownloadsResponse(
            success=False,
            error=str(e)
        )

@router.post("/download/save-as", response_model=SaveToDownloadsResponse)
async def save_as(payload: SaveToDownloadsRequest):
    task = download_manager.get_task(payload.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")

    if not task.completed or not task.result_filepath or not task.result_filepath.exists():
        if task.stage == "failed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=task.error or "Download failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is still processing or unavailable")

    try:
        downloads_dir = str(get_user_downloads_dir())
        default_name = task.filename or task.result_filepath.name
        ext = task.result_filepath.suffix.lstrip(".").lower()

        # Run GetSaveFileNameW in threadpool so it does not block the FastAPI loop
        loop = asyncio.get_running_loop()
        selected_path_str = await loop.run_in_executor(
            None,
            choose_save_file_windows,
            downloads_dir,
            default_name,
            ext
        )

        if not selected_path_str:
            # User cancelled dialog
            return SaveToDownloadsResponse(success=False, error="cancelled")

        dest_path = Path(selected_path_str)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(task.result_filepath, dest_path)
        logger.info(f"File saved via Save As to: {dest_path}")

        return SaveToDownloadsResponse(
            success=True,
            path=str(dest_path),
            filename=dest_path.name
        )
    except Exception as e:
        logger.error(f"Failed in save-as: {e}", exc_info=True)
        return SaveToDownloadsResponse(success=False, error=str(e))


@router.post("/download/open-folder", response_model=PathActionResponse)
async def open_folder(payload: PathActionRequest):
    path = payload.path.strip()
    if not path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path cannot be empty")

    ok = open_in_file_explorer(path)
    if not ok:
        return PathActionResponse(success=False, error="Could not locate or open file path in explorer")
    return PathActionResponse(success=True)

@router.post("/download/open-file", response_model=PathActionResponse)
async def open_file(payload: PathActionRequest):
    path = payload.path.strip()
    if not path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path cannot be empty")

    ok = open_file_native(path)
    if not ok:
        return PathActionResponse(success=False, error="Could not open file in system player")
    return PathActionResponse(success=True)

