import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    APP_NAME: str = "YouTube Downloader Pro"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Storage settings
    DOWNLOAD_DIR: Path = Path(os.getenv("DOWNLOAD_DIR", str(BASE_DIR / "temp_downloads")))
    COOKIE_PATH: str = os.getenv("YOUTUBE_COOKIES_PATH", str(BASE_DIR / "cookies.txt"))
    
    # Retention / Cleanup settings
    TASK_RETENTION_SECONDS: int = 1800  # 30 minutes
    CLEANUP_INTERVAL_SECONDS: int = 600 # Run sweep every 10 minutes
    
    # Concurrency controls
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()

import base64
import logging

logger = logging.getLogger(__name__)

# Support Render Secret Files mount path (/etc/secrets/cookies.txt)
render_secret_cookies = Path("/etc/secrets/cookies.txt")
if render_secret_cookies.is_file():
    settings.COOKIE_PATH = str(render_secret_cookies)
    logger.info(f"Loaded cookies from Render Secret Files: {render_secret_cookies}")

# Support base64-encoded cookies (YOUTUBE_COOKIES_BASE64)
cookies_b64 = os.getenv("YOUTUBE_COOKIES_BASE64", "").strip()
if cookies_b64:
    try:
        decoded = base64.b64decode(cookies_b64).decode("utf-8")
        cookie_file = BASE_DIR / "cookies.txt"
        cookie_file.write_text(decoded, encoding="utf-8")
        settings.COOKIE_PATH = str(cookie_file)
        logger.info("Successfully decoded and saved YOUTUBE_COOKIES_BASE64")
    except Exception as e:
        logger.error(f"Failed to decode YOUTUBE_COOKIES_BASE64: {e}")

# Support raw cookies text pasted as an environment variable (YOUTUBE_COOKIES_CONTENT)
cookies_content = os.getenv("YOUTUBE_COOKIES_CONTENT", "").strip()
if cookies_content and not cookies_b64:
    # Unescape literal \n and \t if the web form / shell escaped them
    if "\\n" in cookies_content and "\n" not in cookies_content:
        cookies_content = cookies_content.replace("\\n", "\n")
    if "\\t" in cookies_content and "\t" not in cookies_content:
        cookies_content = cookies_content.replace("\\t", "\t")

    cookie_file = BASE_DIR / "cookies.txt"
    try:
        cookie_file.write_text(cookies_content, encoding="utf-8")
        settings.COOKIE_PATH = str(cookie_file)
        logger.info(f"Successfully wrote cookies to {cookie_file} ({len(cookies_content)} bytes)")
    except Exception as e:
        logger.error(f"Failed to write YOUTUBE_COOKIES_CONTENT: {e}")

# Ensure download directory exists
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
