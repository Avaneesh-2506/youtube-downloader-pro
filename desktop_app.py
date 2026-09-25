import os
import sys
import time
import socket
import logging
import threading
import urllib.request
from pathlib import Path

# Ensure multiprocessing support for PyInstaller
import multiprocessing
multiprocessing.freeze_support()

# Setup sys.path for backend imports
BASE_DIR = Path(__file__).resolve().parent
if hasattr(sys, "_MEIPASS"):
    meipass = Path(sys._MEIPASS)
    for p in [meipass, meipass / "backend"]:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
else:
    backend_dir = BASE_DIR / "backend"
    if backend_dir.exists() and str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("desktop_app")

# Explicit imports to ensure PyInstaller bundles all required submodules
# when backend core logic is obfuscated
import fastapi
import fastapi.middleware
import fastapi.middleware.cors
import fastapi.staticfiles
import fastapi.responses
import starlette
import starlette.middleware
import starlette.middleware.cors
import starlette.staticfiles
import starlette.responses
import starlette.routing
import sse_starlette
import sse_starlette.sse
import pydantic
import imageio_ffmpeg
import yt_dlp

from app.main import app

def is_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def get_best_port() -> int:
    # Prefer port 8000 if open
    if is_port_available(8000):
        return 8000
    # Otherwise allocate an ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def wait_for_server(port: int, timeout: float = 15.0) -> bool:
    start = time.time()
    url = f"http://127.0.0.1:{port}/health"
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    logger.info("FastAPI backend is healthy and responding.")
                    return True
        except Exception:
            time.sleep(0.15)
    return False

def get_icon_path() -> str | None:
    # 1. PyInstaller bundled path
    if hasattr(sys, "_MEIPASS"):
        meipass_icon = Path(sys._MEIPASS) / "app_icon.ico"
        if meipass_icon.is_file():
            return str(meipass_icon)
    # 2. Executable directory (for portable usage)
    exe_icon = Path(sys.executable).parent / "app_icon.ico"
    if exe_icon.is_file():
        return str(exe_icon)
    # 3. Source directory
    src_icon = BASE_DIR / "app_icon.ico"
    if src_icon.is_file():
        return str(src_icon)
    return None

class DesktopApi:
    def __init__(self):
        self.window = None

    def set_window(self, win):
        self.window = win

    def is_desktop(self) -> bool:
        return True

    def save_file_as(self, task_id: str) -> dict:
        """Opens native Windows Save File Dialog and saves the task's completed file."""
        import shutil
        import webview
        from app.services.download_manager import download_manager
        from app.services.file_service import get_user_downloads_dir

        task = download_manager.get_task(task_id)
        if not task or not task.result_filepath or not task.result_filepath.exists():
            return {"success": False, "error": "File not found or still processing"}

        if not self.window:
            return {"success": False, "error": "Window not initialized"}

        default_name = task.filename or task.result_filepath.name
        ext = task.result_filepath.suffix.lstrip(".").lower()
        file_types = [f"{ext.upper()} Files (*.{ext})", "All Files (*.*)"] if ext else ["All Files (*.*)"]
        initial_dir = str(get_user_downloads_dir())

        result = self.window.create_file_dialog(
            dialog_type=webview.FileDialog.SAVE,
            directory=initial_dir,
            save_filename=default_name,
            file_types=file_types
        )

        if not result or len(result) == 0:
            return {"success": False, "cancelled": True}

        dest_path = Path(result[0])
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(task.result_filepath, dest_path)
            logger.info(f"File successfully saved via Save As to: {dest_path}")
            return {
                "success": True,
                "path": str(dest_path),
                "filename": dest_path.name
            }
        except Exception as e:
            logger.exception(f"Failed to copy file to {dest_path}: {e}")
            return {"success": False, "error": str(e)}

    def save_to_downloads(self, task_id: str) -> dict:
        """Saves the completed file directly into the user's Downloads folder."""
        import shutil
        from app.services.download_manager import download_manager
        from app.services.file_service import get_user_downloads_dir, get_unique_filename

        task = download_manager.get_task(task_id)
        if not task or not task.result_filepath or not task.result_filepath.exists():
            return {"success": False, "error": "File not found or still processing"}

        downloads_dir = get_user_downloads_dir()
        dest_name = task.filename or task.result_filepath.name
        dest_path = get_unique_filename(downloads_dir, dest_name)

        try:
            shutil.copy2(task.result_filepath, dest_path)
            logger.info(f"File successfully saved to downloads: {dest_path}")
            return {
                "success": True,
                "path": str(dest_path),
                "filename": dest_path.name
            }
        except Exception as e:
            logger.exception(f"Failed to save to downloads: {e}")
            return {"success": False, "error": str(e)}

    def open_folder(self, file_path: str) -> dict:
        from app.services.file_service import open_in_file_explorer
        ok = open_in_file_explorer(file_path)
        return {"success": ok}

    def open_file(self, file_path: str) -> dict:
        from app.services.file_service import open_file_native
        ok = open_file_native(file_path)
        return {"success": ok}

def main():
    import uvicorn
    import webview

    # Set explicit Windows AppUserModelID so Windows taskbar groups and displays custom icon
    if sys.platform == "win32":
        try:
            import ctypes
            app_id = "avaneesh.youtubedownloaderpro.desktop.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            logger.warning(f"Could not set AppUserModelID: {e}")

    port = get_best_port()
    logger.info(f"Starting embedded backend on 127.0.0.1:{port}")

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    if not wait_for_server(port):
        logger.error("Timed out waiting for embedded server to start.")
        sys.exit(1)

    app_url = f"http://127.0.0.1:{port}"
    logger.info(f"Launching desktop window pointing to {app_url}")

    api = DesktopApi()

    window = webview.create_window(
        title="YouTube Downloader Pro",
        url=app_url,
        width=1240,
        height=820,
        min_size=(960, 640),
        background_color="#020617",
        text_select=True,
        js_api=api
    )
    api.set_window(window)

    icon_path = get_icon_path()
    if icon_path:
        logger.info(f"Setting desktop window & taskbar icon to: {icon_path}")
        webview.start(icon=icon_path)
    else:
        webview.start()

    logger.info("Window closed. Terminating application...")
    server.should_exit = True


if __name__ == "__main__":
    main()
