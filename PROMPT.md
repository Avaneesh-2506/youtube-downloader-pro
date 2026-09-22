# MASTER SPECIFICATION PROMPT: PRODUCTION-READY YOUTUBE VIDEO DOWNLOADER (240p - 1080p)

> **Role & Persona:** You are a Principal Full-Stack Engineer and Media Streaming Systems Specialist. Your mission is to build a rock-solid, production-ready, high-performance YouTube Video Downloader web application supporting video resolutions from 240p up to 1080p (Full HD with integrated audio), audio extraction (MP3/M4A), real-time download progress tracking, and resilient error recovery.
>
> There must be **zero glitches, zero silent failures, and zero half-baked audio/video stream bugs**. Every edge case must be accounted for.

---

## 1. TECH STACK SELECTION & JUSTIFICATION

To guarantee 100% reliability, prevent bot-detection blocking, handle separate DASH stream muxing, and achieve low-latency streaming:

| Layer | Chosen Technology | Justification |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.11+ with FastAPI** | High performance async I/O; native non-blocking SSE/WebSocket support; seamless integration with Python's streaming toolchains. |
| **Extraction Engine** | **yt-dlp (Native Python API)** | The undisputed industry standard for YouTube scraping. Node-based libraries (`ytdl-core`, `play-dl`) frequently break and get throttled. `yt-dlp` has daily upstream updates, cipher solvers, PO-token support, and cookie handling. |
| **Media Processing** | **FFmpeg (via static binary / `ffmpeg-python`)** | **Mandatory requirement:** YouTube *never* provides pre-muxed 1080p video with audio (progressive MP4 maxes out at 720p or 360p). To deliver 1080p with audio, the server must merge DASH adaptive video + audio streams via FFmpeg. |
| **Frontend Framework** | **Next.js 14+ (App Router) or React + Vite** with **TypeScript** | Type-safe, ultra-responsive UI, optimal client-side state handling. |
| **Styling & Icons** | **Tailwind CSS + Lucide Icons + Framer Motion** | Modern, premium dark/light glassmorphic UI, responsive layouts, animated loading states. |
| **Real-time Pipeline** | **Server-Sent Events (SSE)** or **WebSockets** | Live progress updates (fetching metadata -> downloading video -> downloading audio -> muxing -> ready for browser save). |
| **Task & Temp Storage** | **Async In-Memory Queue (or Celery/Redis) + Tempfile Lifecycle Manager** | Thread-safe temporary file storage with automatic garbage collection to prevent disk leaks. |

---

## 2. CORE ARCHITECTURAL REQUIREMENTS & PITFALL MITIGATION

### A. The 1080p DASH Muxing Requirement (Crucial)
1. **The Trap:** YouTube serves 1080p, 1440p, and 4K as separate video-only streams (adaptive streams). Naive downloaders downloading a 1080p stream directly produce a silent video.
2. **The Solution:** The backend must:
   - Identify the best audio stream (`ba[ext=m4a]` or `bestaudio`).
   - Identify the user-selected video format (e.g., `bestvideo[height=1080][ext=mp4]`).
   - Download both streams into an isolated temporary working directory.
   - Execute FFmpeg with `-c:v copy -c:a aac` (fast stream-copy muxing without re-encoding to preserve 100% quality and finish in seconds).
   - Output a clean, standards-compliant MP4 file ready for streaming/download.

### B. Anti-Bot & Throttling Mitigation
1. Use `yt-dlp` format extractors with rotating Android/iOS/Web client user-agents (`extractor_args={'youtube': {'player_client': ['android', 'web']}}`).
2. Implement cookie support: Allow passing a `cookies.txt` file mounted in the backend to bypass "Sign in to confirm you're not a bot" or age verification.
3. Socket timeout and chunked streaming with custom HTTP headers.

### C. Transient Storage & Memory Leak Protection
1. Every download session gets a unique UUID-based temp folder inside `tempfile.gettempdir()`.
2. As soon as the file is streamed to the client (or if the client disconnects, or on error), an async cleanup background task immediately deletes the temporary directory.
3. A scheduled housekeeping cron (running every 15 minutes) sweeps and purges any orphaned files older than 30 minutes.

### D. Concurrency & Resource Guardrails
1. Set an async concurrency semaphore (e.g., maximum 5 concurrent downloads per worker) to prevent CPU and network starvation.
2. IP-based rate limiting (e.g., max 10 requests per minute using `slowapi`).

---

## 3. COMPREHENSIVE FEATURE SPECIFICATIONS

### 3.1 Frontend User Experience (UI/UX)
1. **Hero Input Section:**
   - Single clean input bar with automatic clipboard paste detection and YouTube URL regex validation (`youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/shorts/...`).
   - Instant "Fetch Details" trigger upon valid URL input.
2. **Metadata Preview Card:**
   - High-res thumbnail preview with duration badge overlay.
   - Video Title, Channel Name with avatar, View Count, and Upload Date.
3. **Format & Resolution Selector:**
   - Clean tabs: **Video with Audio** vs **Audio Only (MP3)**.
   - Resolution cards/pills: **1080p (Full HD)**, **720p (HD)**, **480p**, **360p**, **240p**.
   - Show estimated file size per resolution (dynamically computed from bitrate and duration).
   - Audio quality selector: **320 kbps**, **256 kbps**, **128 kbps**.
4. **Real-time Download Pipeline Modal / Card:**
   - Animated step-by-step progress bar showing:
     - `[0-10%]` Fetching stream manifest & analyzing formats.
     - `[10-60%]` Downloading video stream (with live speed: MB/s & percentage).
     - `[60-80%]` Downloading audio stream.
     - `[80-95%]` Fast muxing audio & video via FFmpeg.
     - `[100%]` Preparing file stream to browser.
   - Native browser download auto-triggers via Blob or direct file download link.
5. **Polished State Handling:**
   - Graceful inline error alerts (e.g., "Video is private", "Geographically restricted", "Live streams not supported").
   - Cancel button to abort in-flight downloads.
   - Recent downloads history list (stored in client `localStorage` for privacy).

---

## 4. API SPECIFICATION (BACKEND)

### Endpoint 1: Parse & Fetch Metadata
- **Route:** `POST /api/v1/info`
- **Request Body:**
  ```json
  {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }
  ```
- **Validation:** Strict regex matching YouTube video IDs and shorts. Reject playlists and channels with explicit messages.
- **Response:**
  ```json
  {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "author": "Rick Astley",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "duration_seconds": 213,
    "duration_formatted": "03:33",
    "available_resolutions": [
      { "height": 1080, "fps": 60, "format_note": "1080p60", "ext": "mp4", "filesize_est": 48200000, "has_audio": false, "requires_mux": true },
      { "height": 720, "fps": 30, "format_note": "720p", "ext": "mp4", "filesize_est": 22100000, "has_audio": true, "requires_mux": false },
      { "height": 480, "fps": 30, "format_note": "480p", "ext": "mp4", "filesize_est": 14000000, "has_audio": false, "requires_mux": true },
      { "height": 360, "fps": 30, "format_note": "360p", "ext": "mp4", "filesize_est": 8500000, "has_audio": true, "requires_mux": false },
      { "height": 240, "fps": 30, "format_note": "240p", "ext": "mp4", "filesize_est": 4200000, "has_audio": false, "requires_mux": true }
    ],
    "audio_formats": [
      { "ext": "mp3", "quality": "320kbps", "filesize_est": 8500000 },
      { "ext": "mp3", "quality": "128kbps", "filesize_est": 3400000 }
    ]
  }
  ```

### Endpoint 2: Start Download / Prepare Task
- **Route:** `POST /api/v1/download/start`
- **Request Body:**
  ```json
  {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "format_type": "video",
    "quality": "1080",
    "ext": "mp4"
  }
  ```
- **Response:**
  ```json
  {
    "task_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "queued"
  }
  ```

### Endpoint 3: Real-Time Progress Stream (SSE)
- **Route:** `GET /api/v1/download/progress/{task_id}`
- **Response Protocol:** `text/event-stream`
- **Events Emitted:**
  ```json
  // Event: progress
  { "stage": "downloading_video", "progress": 45.2, "speed": "4.2 MB/s", "eta": "12s" }
  // Event: progress
  { "stage": "downloading_audio", "progress": 75.0, "speed": "5.1 MB/s", "eta": "3s" }
  // Event: progress
  { "stage": "muxing", "progress": 90.0, "message": "Merging video and audio with FFmpeg..." }
  // Event: complete
  { "stage": "completed", "progress": 100, "download_url": "/api/v1/download/file/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" }
  // Event: error
  { "stage": "failed", "error": "Video is age restricted. Cookie authentication required." }
  ```

### Endpoint 4: File Stream Download
- **Route:** `GET /api/v1/download/file/{task_id}`
- **Headers:**
  - `Content-Disposition: attachment; filename="Rick Astley - Never Gonna Give You Up [1080p].mp4"`
  - `Content-Type: video/mp4`
  - `Content-Length: <filesize>`
- **Response:** Chunked `StreamingResponse` from FastAPI with a `BackgroundTask` to unlink/delete the temp directory when streaming completes.

---

## 5. ROBUST YT-DLP & FFMPEG CONFIGURATION BLUEPRINT

The backend MUST use this battle-tested `yt-dlp` configuration:

```python
import os
import uuid
import tempfile
import yt_dlp
from pathlib import Path

def build_ydl_opts(
    task_id: str, 
    quality: str, 
    media_type: str, 
    output_dir: str, 
    progress_callback
) -> dict:
    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_callback],
        # Anti-bot extractor configuration
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["js", "configs", "webpage"],
            }
        },
        # Network resilience
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
    }

    # Optional: load cookies if file exists
    cookie_path = os.getenv("YOUTUBE_COOKIES_PATH", "cookies.txt")
    if os.path.exists(cookie_path):
        opts["cookiefile"] = cookie_path

    if media_type == "audio":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality.replace("k", ""),
            }],
        })
    else:
        # Video format logic
        height = int(quality)
        # Format string selects exact height or best fallback, pairing with best audio
        opts.update({
            "format": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }],
        })

    return opts
```

---

## 6. COMPLETE PROJECT STRUCTURE & REPOSITORY LAYOUT

```text
youtube-downloader/
├── docker-compose.yml              # One-command full-stack containerization
├── .env.example                    # Port, rate limits, proxy settings, cookie path
├── backend/
│   ├── Dockerfile                  # Python 3.11-slim + ffmpeg installed via apt
│   ├── requirements.txt            # fastapi, uvicorn, yt-dlp, pydantic, slowapi
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application, CORS, routers
│   │   ├── config.py               # Settings (Pydantic BaseSettings)
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints.py    # /info, /download/start, /progress, /file
│   │   │       └── routes.py
│   │   ├── services/
│   │   │   ├── ytdl_service.py     # yt-dlp wrapper & metadata extractor
│   │   │   ├── download_manager.py # In-memory task tracker + SSE event broadcaster
│   │   │   └── cleanup_service.py  # Background temp file garbage collector
│   │   └── schemas/
│   │       └── download.py         # Request/response Pydantic models
│   └── tests/
│       ├── test_info.py            # Unit test for metadata retrieval
│       └── test_download.py        # Test muxing pipeline
└── frontend/
    ├── Dockerfile                  # Node multi-stage build (or Vite preview)
    ├── package.json                # React, Lucide, Tailwind, Axios / Fetch
    ├── tailwind.config.ts
    ├── src/
    │   ├── App.tsx                 # Main layout
    │   ├── components/
    │   │   ├── UrlInput.tsx        # Search bar with validation & auto-fetch
    │   │   ├── VideoCard.tsx       # Thumbnail, title, details preview
    │   │   ├── FormatSelector.tsx  # Tabs (240p, 360p, 480p, 720p, 1080p, MP3)
    │   │   ├── ProgressModal.tsx   # Live SSE animated progress tracker
    │   │   ├── HistoryList.tsx     # LocalStorage recent downloads
    │   │   └── Navbar.tsx          # Clean theme toggle & header
    │   ├── hooks/
    │   │   ├── useDownloadSSE.ts   # SSE listener hook
    │   │   └── useVideoInfo.ts     # Metadata query hook
    │   └── utils/
    │       ├── formatters.ts       # Format bytes (MB/GB) and time (mm:ss)
    │       └── validators.ts       # YouTube URL regex parser
```

---

## 7. ERROR HANDLING & ZERO-DEFECT CHECKLIST

You must handle every single one of these common pitfalls:
1. **Invalid or Malformed URL:** Return 422 with a helpful message ("Please enter a valid YouTube video or Shorts URL").
2. **Age-Restricted Video:** Catch `yt_dlp.utils.DownloadError` and specifically check for "Sign in to confirm your age". Return a descriptive HTTP 403 explaining cookie requirement.
3. **Private or Deleted Video:** Return a 404 with "This video is private, deleted, or unavailable".
4. **Live Stream / Premieres:** Live streams cannot be converted into fixed-length MP4s. Inspect `is_live` in info dict; reject with "Live streams are currently not supported".
5. **Disk Full Prevention:** Ensure temp files are deleted even if user closes the tab mid-download (use Python `finally:` block or FastAPI `BackgroundTask`).
6. **Muxing Hangs:** Ensure FFmpeg operations have a hard timeout (e.g. 5 minutes) so worker processes never deadlock.
7. **Filenames with Special Characters:** Sanitize downloaded file names using `re.sub(r'[^\w\-_\. ]', '_', filename)` to prevent HTTP header splitting and invalid filename errors on Windows/Linux.

---

## 8. INSTRUCTIONS FOR THE AGENT/DEVELOPER EXECUTING THIS PROMPT

1. **Phase 1: Environment & Tooling Verification**
   - Check that Python 3.11+ and `ffmpeg` are installed and available in the system `PATH`.
   - Install dependencies (`pip install fastapi uvicorn yt-dlp pydantic slowapi`).
2. **Phase 2: Backend Implementation**
   - Implement `ytdl_service.py` with robust extraction for 240p to 1080p.
   - Implement `download_manager.py` with thread-safe task status and SSE event queues.
   - Implement FastAPI endpoints with streaming responses and cleanup tasks.
3. **Phase 3: Frontend Implementation**
   - Build responsive, modern Tailwind UI with dark mode support.
   - Connect URL parsing, metadata card, resolution selectors, and SSE progress listeners.
4. **Phase 4: End-to-End Verification**
   - Test a real public YouTube URL at **1080p**. Confirm the downloaded file plays both video and crystal-clear audio.
   - Test a 360p download. Confirm progressive stream downloads quickly.
   - Test an audio extraction (MP3). Confirm ID3 metadata and playable audio.
   - Inspect temp directories to confirm all scratch files are 100% cleaned up after download.
