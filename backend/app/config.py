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
import re
import time

logger = logging.getLogger(__name__)

def normalize_and_repair_cookies(raw: str) -> str:
    """Repairs and normalizes cookie text to strict Netscape tab-delimited format."""
    if not raw or not raw.strip():
        return ""
        
    # Unescape escaped newlines and tabs if passed from shell / web input
    if "\\n" in raw:
        raw = raw.replace("\\n", "\n")
    if "\\t" in raw:
        raw = raw.replace("\\t", "\t")

    lines = []
    has_header = False
    now = int(time.time())

    for line in raw.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith("# Netscape") or trimmed.startswith("# HTTP Cookie File"):
            has_header = True
            lines.append(trimmed)
            continue
        if trimmed.startswith("#"):
            lines.append(trimmed)
            continue

        # Try tab split first
        parts = trimmed.split("\t")
        if len(parts) < 7:
            # Try whitespace split if tabs were converted to spaces
            parts = re.split(r"\s+", trimmed, maxsplit=6)

        if len(parts) == 7:
            domain, flag, path, secure, expires_str, name, val = parts
            # Auto-bump expired timestamps to year 2038 so client-side cookiejar doesn't discard them
            try:
                exp = int(expires_str)
                if 0 < exp < now:
                    expires_str = "2147483647"
            except ValueError:
                pass
            lines.append("\t".join([domain, flag, path, secure, expires_str, name, val]))
        else:
            lines.append(trimmed)

    header = "# Netscape HTTP Cookie File\n# Auto-normalized for yt-dlp\n" if not has_header else ""
    return header + "\n".join(lines) + "\n"

# Process cookies by merging from all available sources
raw_cookie_sources = []
render_secret_cookies = Path("/etc/secrets/cookies.txt")
cookies_b64 = os.getenv("YOUTUBE_COOKIES_BASE64", "").strip()
cookies_content = os.getenv("YOUTUBE_COOKIES_CONTENT", "").strip()
local_cookie_file = BASE_DIR / "cookies.txt"

if cookies_content:
    raw_cookie_sources.append(("YOUTUBE_COOKIES_CONTENT", cookies_content))
    logger.info("Found cookies in YOUTUBE_COOKIES_CONTENT")

if cookies_b64:
    try:
        decoded = base64.b64decode(cookies_b64).decode("utf-8")
        raw_cookie_sources.append(("YOUTUBE_COOKIES_BASE64", decoded))
        logger.info("Found cookies in YOUTUBE_COOKIES_BASE64")
    except Exception as e:
        logger.error(f"Failed to decode YOUTUBE_COOKIES_BASE64: {e}")

if render_secret_cookies.is_file():
    try:
        raw_cookie_sources.append(("Render Secret Files", render_secret_cookies.read_text(encoding="utf-8")))
        logger.info(f"Found cookies in Render Secret Files: {render_secret_cookies}")
    except Exception as e:
        logger.error(f"Failed to read Render Secret Files cookies: {e}")

if local_cookie_file.is_file():
    try:
        raw_cookie_sources.append(("Local cookies.txt", local_cookie_file.read_text(encoding="utf-8")))
    except Exception as e:
        logger.error(f"Failed to read local cookies.txt: {e}")

# Merge and deduplicate all cookie sources
cookie_map = {}
now = int(time.time())

for source_name, raw in raw_cookie_sources:
    if not raw or not raw.strip():
        continue
    # Unescape literal backslashes
    if "\\n" in raw:
        raw = raw.replace("\\n", "\n")
    if "\\t" in raw:
        raw = raw.replace("\\t", "\t")
        
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            parts = re.split(r"\s+", line, maxsplit=6)
        if len(parts) == 7:
            domain, flag, path, secure, expires_str, name, val = parts
            try:
                exp = int(expires_str)
                if 0 < exp < now:
                    expires_str = "2147483647"
            except ValueError:
                pass
            # Key by (domain, path, name) so latest value wins
            cookie_map[(domain, path, name)] = (domain, flag, path, secure, expires_str, name, val)

if cookie_map:
    try:
        header = "# Netscape HTTP Cookie File\n# Merged and normalized for yt-dlp\n"
        cookie_lines = ["\t".join(parts) for parts in cookie_map.values()]
        final_cookie_text = header + "\n".join(cookie_lines) + "\n"
        local_cookie_file.write_text(final_cookie_text, encoding="utf-8")
        settings.COOKIE_PATH = str(local_cookie_file)
        logger.info(f"Successfully saved {len(cookie_map)} normalized cookies to {local_cookie_file}")
    except Exception as e:
        logger.error(f"Failed to write merged cookies: {e}")

# Ensure download directory exists
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

