import asyncio
import os
import re
import math
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yt_dlp

from app.config import settings
from app.schemas.download import VideoInfoResponse, VideoResolution, AudioFormat
from app.services.ffmpeg_locator import get_ffmpeg_path
from app.services.download_manager import download_manager

logger = logging.getLogger(__name__)

YOUTUBE_REGEX = re.compile(
    r'^(https?://)?(www\.|m\.|music\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
)

def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_REGEX.search(url.strip()))

def strip_ansi(text: Optional[str]) -> Optional[str]:
    if not text:
        return text
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    return clean.strip()

def sanitize_filename(name: str) -> str:
    """Removes or replaces invalid filesystem characters."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.replace("\n", " ").replace("\r", " ").strip()
    return clean[:120] if len(clean) > 120 else clean

def format_duration(seconds: Optional[int]) -> str:
    if not seconds or seconds < 0:
        return "00:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_bytes(num_bytes: Optional[int]) -> str:
    if not num_bytes or num_bytes <= 0:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"

def format_views(views: Optional[int]) -> str:
    if views is None:
        return "0 views"
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B views"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    return f"{views:,} views"

class YtDlpService:
    @staticmethod
    def get_base_ydl_opts() -> dict:
        ffmpeg_bin = get_ffmpeg_path()
        opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 10,
            "fragment_retries": 10,
        }
        
        # Enable JavaScript runtime if node is present
        node_bin = shutil.which("node")
        if node_bin:
            opts["js_runtimes"] = {"node": {}}

        if ffmpeg_bin:
            opts["ffmpeg_location"] = ffmpeg_bin

        if os.path.exists(settings.COOKIE_PATH):
            opts["cookiefile"] = settings.COOKIE_PATH
            
        return opts

    @classmethod
    def fetch_video_info(cls, url: str) -> VideoInfoResponse:
        url = url.strip()
        if not is_valid_youtube_url(url):
            raise ValueError("Invalid YouTube URL. Please provide a valid video or Shorts link.")

        opts = cls.get_base_ydl_opts()
        opts.update({
            "extract_flat": False,
            "skip_download": True,
        })

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            err_msg = str(e)
            if "Sign in to confirm your age" in err_msg:
                raise PermissionError("This video is age-restricted and requires cookie authentication.")
            if "Private video" in err_msg or "Video unavailable" in err_msg:
                raise FileNotFoundError("This video is private or unavailable.")
            raise RuntimeError(f"Failed to fetch video: {err_msg}")

        if not info:
            raise RuntimeError("Could not retrieve video information.")

        if info.get("is_live"):
            raise ValueError("Live streams are currently not supported for direct download.")

        duration = info.get("duration", 0)
        formats = info.get("formats", [])

        # Map available video heights
        available_heights = set()
        for f in formats:
            h = f.get("height")
            if h and f.get("vcodec") != "none":
                available_heights.add(h)

        target_heights = [2160, 1440, 1080, 720, 480, 360, 240, 144]
        resolutions: List[VideoResolution] = []

        # Find best audio bitrate to compute muxed size estimate
        best_audio_bitrate = 128_000 # default fallback 128 kbps
        for f in formats:
            if f.get("acodec") != "none" and f.get("vcodec") == "none":
                abr = f.get("abr")
                if abr and abr > (best_audio_bitrate / 1000):
                    best_audio_bitrate = int(abr * 1000)

        for target_h in target_heights:
            # Check if this resolution or higher is available
            matching_formats = [
                f for f in formats 
                if f.get("height") == target_h and f.get("vcodec") != "none"
            ]
            if not matching_formats:
                # If exact height not found, check if a higher height exists so it can downscale/fallback
                if not any(h >= target_h for h in available_heights):
                    continue

            # Check if there is a progressive format with both audio and video
            prog_formats = [f for f in matching_formats if f.get("acodec") != "none"]
            has_progressive = len(prog_formats) > 0
            requires_mux = not has_progressive or target_h >= 1080

            # Calculate estimated size
            size_est = None
            if matching_formats:
                # pick format with highest bitrate or explicit filesize
                best_fmt = max(
                    matching_formats, 
                    key=lambda x: (x.get("filesize") or x.get("filesize_approx") or (x.get("tbr") or 0))
                )
                raw_size = best_fmt.get("filesize") or best_fmt.get("filesize_approx")
                if raw_size:
                    size_est = raw_size
                    if requires_mux and duration:
                        # add audio stream size estimate
                        size_est += int((best_audio_bitrate / 8) * duration)
                elif duration and best_fmt.get("tbr"):
                    size_est = int(((best_fmt["tbr"] * 1000) / 8) * duration)

            if target_h == 2160:
                note = "2160p 4K UHD"
            elif target_h == 1440:
                note = "1440p 2K QHD"
            elif target_h == 1080:
                note = "1080p Full HD"
            elif target_h == 720:
                note = "720p HD"
            elif target_h == 480:
                note = "480p SD"
            elif target_h == 144:
                note = "144p Data Saver"
            else:
                note = f"{target_h}p"

            resolutions.append(VideoResolution(
                height=target_h,
                format_note=note,
                fps=60 if any((f.get("fps") or 0) >= 50 for f in matching_formats) else 30,
                ext="mp4",
                filesize_est=size_est,
                filesize_est_formatted=format_bytes(size_est) if size_est else None,
                has_audio=not requires_mux,
                requires_mux=requires_mux
            ))

        # Audio presets
        audio_presets = [
            ("320kbps", 320),
            ("256kbps", 256),
            ("128kbps", 128),
        ]
        audio_formats: List[AudioFormat] = []
        for name, kbps in audio_presets:
            est_bytes = int((kbps * 1000 / 8) * duration) if duration else None
            audio_formats.append(AudioFormat(
                quality=name,
                ext="mp3",
                filesize_est=est_bytes,
                filesize_est_formatted=format_bytes(est_bytes) if est_bytes else None,
            ))

        # Select best thumbnail
        thumbnails = info.get("thumbnails", [])
        thumbnail_url = thumbnails[-1]["url"] if thumbnails else f"https://i.ytimg.com/vi/{info.get('id')}/maxresdefault.jpg"

        return VideoInfoResponse(
            id=info.get("id", ""),
            url=info.get("webpage_url", url),
            title=info.get("title", "YouTube Video"),
            author=info.get("uploader", info.get("channel", "Unknown Channel")),
            thumbnail=thumbnail_url,
            duration_seconds=duration,
            duration_formatted=format_duration(duration),
            views=info.get("view_count"),
            views_formatted=format_views(info.get("view_count")),
            available_resolutions=resolutions,
            audio_formats=audio_formats,
        )

    @classmethod
    def run_download_task(
        cls,
        task_id: str,
        url: str,
        format_type: str,
        quality: str,
        output_dir: Path
    ):
        """Synchronous worker function that executes yt-dlp download in a thread."""
        ffmpeg_bin = get_ffmpeg_path()
        current_stream = {"index": 0}

        def progress_hook(d: dict):
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                percent = 0.0
                if total > 0:
                    percent = (downloaded / total) * 100.0

                speed = strip_ansi(d.get("_speed_str")) or "Calculating..."
                eta = strip_ansi(d.get("_eta_str")) or "Calculating..."

                # Map stage & overall progress
                if format_type == "video":
                    # Video stream download is first (maps 10% -> 60%)
                    # Audio stream download is second (maps 60% -> 85%)
                    if current_stream["index"] <= 1:
                        scaled_pct = 10.0 + (percent * 0.50)
                        stage_name = "downloading_video"
                        msg = f"Downloading video stream: {round(percent)}%"
                    else:
                        scaled_pct = 60.0 + (percent * 0.25)
                        stage_name = "downloading_audio"
                        msg = f"Downloading audio stream: {round(percent)}%"
                else:
                    scaled_pct = 10.0 + (percent * 0.75)
                    stage_name = "downloading_audio"
                    msg = f"Downloading audio: {round(percent)}%"

                download_manager.update_progress(
                    task_id=task_id,
                    stage=stage_name,
                    progress=min(scaled_pct, 88.0),
                    speed=speed,
                    eta=eta,
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    message=msg,
                )

            elif status == "finished":
                current_stream["index"] += 1
                download_manager.update_progress(
                    task_id=task_id,
                    stage="muxing" if format_type == "video" else "converting",
                    progress=90.0,
                    message="Finalizing media with FFmpeg..."
                )

        opts = cls.get_base_ydl_opts()
        output_template = str(output_dir / "%(title).100s [%(id)s].%(ext)s")
        opts.update({
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "noplaylist": True,
        })

        if format_type == "audio":
            bitrate = quality.replace("kbps", "").replace("k", "")
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate or "320",
                }],
            })
        else:
            height = int(quality)
            # 1080p and adaptive DASH stream muxing format
            # Prioritizes mp4 video + m4a audio, fallback to any best video + audio
            opts.update({
                "format": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
                "merge_output_format": "mp4",
                "postprocessors": [{
                    "key": "FFmpegVideoRemuxer",
                    "preferedformat": "mp4",
                }],
            })

        download_manager.update_progress(
            task_id=task_id,
            stage="analyzing",
            progress=5.0,
            message="Connecting to YouTube and analyzing formats..."
        )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            # Locate the generated file inside output_dir
            candidates = list(output_dir.glob("*.*"))
            # Filter out temporary files like .part, .ytdl
            valid_files = [f for f in candidates if not f.name.endswith((".part", ".ytdl"))]
            
            if not valid_files:
                raise FileNotFoundError("Output media file was not generated.")

            # Pick largest/target extension file
            target_ext = ".mp3" if format_type == "audio" else ".mp4"
            matching_files = [f for f in valid_files if f.suffix.lower() == target_ext]
            final_file = matching_files[0] if matching_files else max(valid_files, key=lambda f: f.stat().st_size)

            clean_filename = sanitize_filename(final_file.name)
            if clean_filename != final_file.name:
                renamed_path = final_file.with_name(clean_filename)
                final_file.rename(renamed_path)
                final_file = renamed_path

            download_manager.complete_task(
                task_id=task_id,
                filepath=final_file,
                filename=final_file.name
            )
            logger.info(f"Task {task_id} completed successfully: {final_file.name}")

        except Exception as e:
            logger.error(f"Download failed for task {task_id}: {e}", exc_info=True)
            download_manager.fail_task(task_id, str(e))
