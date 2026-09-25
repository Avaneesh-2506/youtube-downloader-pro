import os
import sys
import uuid
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def get_user_downloads_dir() -> Path:
    """
    Returns the user's Downloads directory.
    Uses Windows SHGetKnownFolderPath to properly resolve redirected Downloads folders.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            # FOLDERID_Downloads = {374DE290-123F-4565-9164-39C4925E467B}
            FOLDERID_Downloads = uuid.UUID("{374DE290-123F-4565-9164-39C4925E467B}")
            
            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", ctypes.c_ulong),
                    ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8)
                ]

            guid = GUID(
                FOLDERID_Downloads.time_low,
                FOLDERID_Downloads.time_mid,
                FOLDERID_Downloads.time_hi_version,
                (ctypes.c_ubyte * 8)(*FOLDERID_Downloads.bytes[8:])
            )
            path_ptr = ctypes.c_wchar_p()
            res = ctypes.windll.shell32.SHGetKnownFolderPath(
                ctypes.byref(guid), 0, None, ctypes.byref(path_ptr)
            )
            if res == 0 and path_ptr.value:
                downloads = Path(path_ptr.value)
                if downloads.is_dir():
                    return downloads
        except Exception as e:
            logger.warning(f"Could not query SHGetKnownFolderPath: {e}")

    # Fallback to standard user home / Downloads
    home_downloads = Path.home() / "Downloads"
    home_downloads.mkdir(parents=True, exist_ok=True)
    return home_downloads

def get_unique_filename(folder: Path, filename: str) -> Path:
    """
    Returns a unique file path inside `folder`.
    If `video.mp4` exists, generates `video (1).mp4`, `video (2).mp4`, etc.
    """
    target = folder / filename
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while target.exists():
        target = folder / f"{stem} ({counter}){suffix}"
        counter += 1
    return target

def open_in_file_explorer(path: Path | str) -> bool:
    """
    Opens Windows File Explorer with the target file highlighted.
    """
    try:
        p = Path(path).resolve()
        if not p.exists():
            # If the file doesn't exist, try its parent folder
            p = p.parent
            if not p.exists():
                return False

        if sys.platform == "win32":
            if p.is_file():
                subprocess.Popen(f'explorer.exe /select,"{p}"', shell=True)
            else:
                subprocess.Popen(f'explorer.exe "{p}"', shell=True)
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(p)])
            return True
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
            return True
    except Exception as e:
        logger.error(f"Failed to open file explorer: {e}")
        return False

def open_file_native(path: Path | str) -> bool:
    """
    Opens the file in the default associated media player / application.
    """
    try:
        p = Path(path).resolve()
        if not p.exists():
            return False

        if sys.platform == "win32":
            os.startfile(str(p))
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
            return True
        else:
            subprocess.Popen(["xdg-open", str(p)])
            return True
    except Exception as e:
        logger.error(f"Failed to open file natively: {e}")
        return False
