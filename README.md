# YouTube Downloader Pro (144p to 4K Ultra HD & MP3)

<div align="center">

[![Download Windows Executable](https://img.shields.io/badge/Download-YouTubeDownloaderPro.exe-e11d48?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Avaneesh-2506/youtube-downloader-pro/releases/download/v1.0.0/YouTubeDownloaderPro.exe)
[![Releases](https://img.shields.io/badge/GitHub-Releases-blue?style=for-the-badge&logo=github)](https://github.com/Avaneesh-2506/youtube-downloader-pro/releases/latest)

A high-performance, standalone Windows desktop and full-stack application designed to download YouTube videos in resolutions from **144p up to 4K Ultra HD (with audio)**, and extract high-bitrate **MP3 audio (up to 320 kbps)**.

</div>

---

## 💾 Direct Download (Windows Desktop App)

No installation required! Just download the standalone `.exe` and double-click to run:

👉 **[Download Latest `YouTubeDownloaderPro.exe`](https://github.com/Avaneesh-2506/youtube-downloader-pro/releases/download/v1.0.0/YouTubeDownloaderPro.exe)** *(from GitHub Releases)*

* **Zero Dependencies**: Bundles Python 3.12, React dark UI, and embedded FFmpeg.
* **No Bot Walls**: Runs locally on your home internet without datacenter CAPTCHAs or login walls.
* **Instant Lossless Muxing**: Fast local DASH stream merging for 1080p, 2K, and 4K videos.

---

## 🌟 Key Features

- **4K UHD & 1080p Lossless Muxing**: Automatically downloads separate DASH video and audio streams and merges them using FFmpeg in seconds.
- **Resolutions Supported**: 2160p (4K UHD), 1440p (2K QHD), 1080p (Full HD), 720p (HD), 480p, 360p, 240p, 144p (Data Saver).
- **Audio Extraction**: 320 kbps, 256 kbps, and 128 kbps stereo MP3.
- **Real-Time Live Progress**: Tracks speed (MB/s), ETA, and stage status (`analyzing` -> `downloading video` -> `downloading audio` -> `muxing` -> `completed`) via Server-Sent Events (SSE).
- **Ephemeral Storage**: Files are streamed to the client and immediately scheduled for automatic disk cleanup. Abandoned files older than 30 minutes are purged by an automatic background janitor.
- **Anti-Bot Resilient**: Configured with `yt-dlp` rotating player clients (`web`, `android`), JavaScript runtime support (`Node.js`), and optional `cookies.txt` support for age-restricted content.
- **Local History**: Download history is saved locally in the browser's `localStorage` for privacy.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend API** | Python 3.11+ / 3.12, FastAPI, Uvicorn |
| **Extraction Engine** | `yt-dlp` (Native Python API) |
| **Muxer / Codec** | `FFmpeg` (auto-detected from system or `imageio-ffmpeg`) |
| **Real-time Pipeline**| Server-Sent Events (`sse-starlette`) |
| **Frontend UI** | React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons |
| **Containerization** | Docker, Docker Compose, Nginx |

---

## 🚀 Quick Start (Local)

### Option 1: 1-Click Launch (Windows)
Double-click `start-all.bat`. It will launch both the FastAPI backend on port 8000 and the Vite frontend on port 5173.

### Option 2: Manual Start

#### 1. Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```
- API is running at: `http://localhost:8000`
- Interactive API documentation: `http://localhost:8000/docs`

#### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
- Web App is running at: `http://localhost:5173`

---

## 🐳 Docker Deployment

To deploy both backend and frontend via Docker Compose:

```bash
docker-compose up --build -d
```
- Web Application: `http://localhost:5173`
- Backend API: `http://localhost:8000`

---

## 🔐 Age-Restricted Videos & Cookies (Optional)

If you need to download age-restricted or members-only videos:
1. Export your YouTube cookies using the browser extension **"Get cookies.txt LOCALLY"** (Netscape format).
2. Place the file as `cookies.txt` inside the `backend/` directory (or root directory for Docker).
3. The backend will automatically detect and load `cookies.txt`.
