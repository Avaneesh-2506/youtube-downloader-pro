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

def choose_save_file_windows(initial_dir: str, default_filename: str, ext: str) -> Optional[str]:
    """
    Invokes the native Windows Save File Dialog (GetSaveFileNameW).
    Returns the selected file path string or None if cancelled.
    """
    if sys.platform != "win32":
        return None

    try:
        import ctypes
        from ctypes import wintypes

        class OPENFILENAMEW(ctypes.Structure):
            _fields_ = [
                ("lStructSize", wintypes.DWORD),
                ("hwndOwner", wintypes.HWND),
                ("hInstance", wintypes.HINSTANCE),
                ("lpstrFilter", wintypes.LPCWSTR),
                ("lpstrCustomFilter", wintypes.LPWSTR),
                ("nMaxCustFilter", wintypes.DWORD),
                ("nFilterIndex", wintypes.DWORD),
                ("lpstrFile", wintypes.LPWSTR),
                ("nMaxFile", wintypes.DWORD),
                ("lpstrFileTitle", wintypes.LPWSTR),
                ("nMaxFileTitle", wintypes.DWORD),
                ("lpstrInitialDir", wintypes.LPCWSTR),
                ("lpstrTitle", wintypes.LPCWSTR),
                ("Flags", wintypes.DWORD),
                ("nFileOffset", wintypes.WORD),
                ("nFileExtension", wintypes.WORD),
                ("lpstrDefExt", wintypes.LPCWSTR),
                ("lCustData", wintypes.LPARAM),
                ("lpfnHook", wintypes.LPARAM),
                ("lpTemplateName", wintypes.LPCWSTR),
                ("pvReserved", wintypes.LPVOID),
                ("dwReserved", wintypes.DWORD),
                ("FlagsEx", wintypes.DWORD)
            ]

        OFN_OVERWRITEPROMPT = 0x00000002
        OFN_PATHMUSTEXIST = 0x00000800
        OFN_NOCHANGEDIR = 0x00000008
        OFN_EXPLORER = 0x00080000

        ext_clean = ext.lstrip(".").lower()
        filter_str = f"{ext_clean.upper()} Files (*.{ext_clean})\0*.{ext_clean}\0All Files (*.*)\0*.*\0\0"

        buf = ctypes.create_unicode_buffer(1024)
        buf.value = default_filename

        ofn = OPENFILENAMEW()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
        ofn.lpstrFilter = filter_str
        ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
        ofn.nMaxFile = 1024
        ofn.lpstrInitialDir = initial_dir
        ofn.lpstrTitle = "Save Video As"
        ofn.Flags = OFN_OVERWRITEPROMPT | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR | OFN_EXPLORER
        ofn.lpstrDefExt = ext_clean

        if ctypes.windll.comdlg32.GetSaveFileNameW(ctypes.byref(ofn)):
            return buf.value
        return None
    except Exception as e:
        logger.error(f"Error invoking Windows Save Dialog: {e}")
        return None

