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

# Support Render Secret Files mount path (/etc/secrets/cookies.txt)
render_secret_cookies = Path("/etc/secrets/cookies.txt")
if render_secret_cookies.is_file():
    settings.COOKIE_PATH = str(render_secret_cookies)

# Support raw cookies text pasted as an environment variable (YOUTUBE_COOKIES_CONTENT)
cookies_content = os.getenv("YOUTUBE_COOKIES_CONTENT", "").strip()
if cookies_content:
    cookie_file = BASE_DIR / "cookies.txt"
    try:
        cookie_file.write_text(cookies_content, encoding="utf-8")
        settings.COOKIE_PATH = str(cookie_file)
    except Exception as e:
        pass

# Ensure download directory exists
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
