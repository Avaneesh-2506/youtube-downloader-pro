import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CACHED_FFMPEG_PATH: Optional[str] = None

def get_ffmpeg_path() -> Optional[str]:
    """
    Locates FFmpeg binary on the system.
    Searches in:
    1. System PATH
    2. Local backend/bin directory
    3. imageio-ffmpeg embedded binary
    """
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH:
        return _CACHED_FFMPEG_PATH

    # 0. PyInstaller / Bundled executable checks
    import sys
    if hasattr(sys, "_MEIPASS"):
        meipass_paths = [
            Path(sys._MEIPASS) / "ffmpeg.exe",
            Path(sys._MEIPASS) / "bin" / "ffmpeg.exe",
        ]
        for p in meipass_paths:
            if p.is_file() and _verify_ffmpeg(str(p)):
                logger.info(f"Using bundled PyInstaller FFmpeg binary at: {p}")
                _CACHED_FFMPEG_PATH = str(p)
                return str(p)

    exe_dir = Path(sys.executable).parent
    exe_bin_paths = [
        exe_dir / "ffmpeg.exe",
        exe_dir / "bin" / "ffmpeg.exe",
    ]
    for p in exe_bin_paths:
        if p.is_file() and _verify_ffmpeg(str(p)):
            logger.info(f"Using portable FFmpeg binary next to exe: {p}")
            _CACHED_FFMPEG_PATH = str(p)
            return str(p)

    # 1. System PATH check
    path = shutil.which("ffmpeg")
    if path and _verify_ffmpeg(path):
        logger.info(f"Using system FFmpeg at: {path}")
        _CACHED_FFMPEG_PATH = path
        return path

    # 2. Local bin check
    base_dir = Path(__file__).resolve().parent.parent.parent
    local_bin_paths = [
        base_dir / "bin" / "ffmpeg.exe",
        base_dir / "bin" / "ffmpeg",
        base_dir.parent / "bin" / "ffmpeg.exe",
    ]
    for local_path in local_bin_paths:
        if local_path.is_file() and _verify_ffmpeg(str(local_path)):
            logger.info(f"Using local FFmpeg binary at: {local_path}")
            _CACHED_FFMPEG_PATH = str(local_path)
            return str(local_path)

    # 3. imageio-ffmpeg package check
    try:
        import imageio_ffmpeg
        imageio_path = imageio_ffmpeg.get_ffmpeg_exe()
        if imageio_path and _verify_ffmpeg(imageio_path):
            logger.info(f"Using imageio-ffmpeg binary at: {imageio_path}")
            _CACHED_FFMPEG_PATH = imageio_path
            return imageio_path
    except Exception as e:
        logger.warning(f"imageio-ffmpeg probe failed: {e}")

    logger.warning("FFmpeg binary not found! High-res (1080p) stream muxing requires FFmpeg.")
    return None

def _verify_ffmpeg(executable: str) -> bool:
    try:
        res = subprocess.run([executable, "-version"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False
