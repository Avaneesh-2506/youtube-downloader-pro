from typing import Optional, List
from pydantic import BaseModel, Field

class InfoRequest(BaseModel):
    url: str = Field(..., description="YouTube video or Shorts URL")

class VideoResolution(BaseModel):
    height: int
    format_note: str
    fps: Optional[int] = None
    ext: str = "mp4"
    filesize_est: Optional[int] = None
    filesize_est_formatted: Optional[str] = None
    has_audio: bool = False
    requires_mux: bool = True

class AudioFormat(BaseModel):
    quality: str
    ext: str = "mp3"
    filesize_est: Optional[int] = None
    filesize_est_formatted: Optional[str] = None

class VideoInfoResponse(BaseModel):
    id: str
    url: str
    title: str
    author: str
    thumbnail: str
    duration_seconds: int
    duration_formatted: str
    views: Optional[int] = None
    views_formatted: Optional[str] = None
    available_resolutions: List[VideoResolution]
    audio_formats: List[AudioFormat]

class DownloadStartRequest(BaseModel):
    url: str
    format_type: str = Field(default="video", pattern="^(video|audio)$")
    quality: str = Field(default="1080", description="1080, 720, 480, 360, 240 or audio bitrate like 320k")
    ext: str = Field(default="mp4")

class DownloadStartResponse(BaseModel):
    task_id: str
    status: str
    message: str

class ProgressUpdate(BaseModel):
    task_id: str
    stage: str
    progress: float = 0.0
    speed: Optional[str] = None
    eta: Optional[str] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    message: Optional[str] = None
    file_url: Optional[str] = None
    error: Optional[str] = None
