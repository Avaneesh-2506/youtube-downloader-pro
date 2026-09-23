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

def main():
    import uvicorn
    import webview

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

    window = webview.create_window(
        title="YouTube Downloader Pro",
        url=app_url,
        width=1240,
        height=820,
        min_size=(960, 640),
        background_color="#020617",
        text_select=True
    )

    # Starts desktop message loop (blocks until user closes window)
    webview.start()

    logger.info("Window closed. Terminating application...")
    server.should_exit = True

if __name__ == "__main__":
    main()
