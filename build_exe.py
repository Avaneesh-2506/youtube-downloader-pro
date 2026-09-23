import os
import sys
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run(cmd, cwd=None):
    print(f"==> Running: {cmd} (cwd={cwd or BASE_DIR})")
    res = subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR)
    if res.returncode != 0:
        print(f"Error: Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def main():
    print("==================================================")
    print("Building YouTube Downloader Pro Standalone Desktop (.exe)")
    print("==================================================")

    # 1. Build frontend bundle
    frontend_dir = BASE_DIR / "frontend"
    print("\n[Step 1/4] Compiling React Frontend Assets...")
    run("npm run build", cwd=frontend_dir)

    dist_dir = frontend_dir / "dist"
    if not (dist_dir / "index.html").is_file():
        print("Error: frontend/dist/index.html was not generated!")
        sys.exit(1)
    print("Frontend build verified.")

    # 2. Verify FFmpeg binary in bin/
    bin_ffmpeg = BASE_DIR / "bin" / "ffmpeg.exe"
    if not bin_ffmpeg.is_file():
        print("\n[Step 2/4] Locating and staging FFmpeg binary...")
        import imageio_ffmpeg
        src_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        (BASE_DIR / "bin").mkdir(exist_ok=True)
        shutil.copy2(src_ffmpeg, bin_ffmpeg)
    print(f"FFmpeg binary staged: {bin_ffmpeg} ({round(bin_ffmpeg.stat().st_size / (1024*1024), 1)} MB)")

    # 3. Clean prior build artifacts
    for d in [BASE_DIR / "build", BASE_DIR / "dist"]:
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)

    # 4. Obfuscate backend logic with PyArmor
    print("\n[Step 3/5] Obfuscating backend core logic with PyArmor...")
    obf_dir = BASE_DIR / "build" / "obfuscated"
    obf_dir.mkdir(parents=True, exist_ok=True)
    run(f'pyarmor gen -O "{obf_dir}" -r "{BASE_DIR / "backend" / "app"}"')
    
    pyarmor_runtime_dir = obf_dir / "pyarmor_runtime_000000"

    # 5. Invoke PyInstaller
    print("\n[Step 4/5] Running PyInstaller standalone compiler...")
    
    hidden_imports = [
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespans",
        "uvicorn.lifespans.on",
        "uvicorn.lifespans.off",
        "fastapi",
        "starlette",
        "starlette.routing",
        "starlette.staticfiles",
        "sse_starlette",
        "yt_dlp",
        "yt_dlp.extractor",
        "yt_dlp.postprocessor",
        "webview",
        "clr_loader",
        "pythonnet",
        "imageio_ffmpeg",
        "pydantic",
        "anyio",
        "anyio._backends._asyncio",
        "pyarmor_runtime_000000",
    ]

    hidden_flags = " ".join([f'--hidden-import "{h}"' for h in hidden_imports])

    app_icon = BASE_DIR / "app_icon.ico"
    add_data = [
        f'--add-data "{BASE_DIR / "frontend" / "dist"};frontend/dist"',
        f'--add-data "{obf_dir / "app"};app"',
        f'--add-data "{pyarmor_runtime_dir};pyarmor_runtime_000000"',
        f'--add-data "{bin_ffmpeg};bin"',
        f'--add-data "{bin_ffmpeg};."',
        f'--add-data "{app_icon};."',
    ]
    data_flags = " ".join(add_data)

    icon_flag = f'--icon "{app_icon}"' if app_icon.is_file() else ""

    pyinstaller_cmd = (
        f'pyinstaller --noconfirm --onefile '
        f'--name "YouTubeDownloaderPro" '
        f'--windowed '
        f'{icon_flag} '
        f'--paths "{obf_dir}" '
        f'--paths "{pyarmor_runtime_dir}" '
        f'{data_flags} '
        f'{hidden_flags} '
        f'"{BASE_DIR / "desktop_app.py"}"'
    )

    run(pyinstaller_cmd)

    print("\n[Step 5/5] Verifying built output...")
    # Also test creating a single file or onedir
    exe_path = BASE_DIR / "dist" / "YouTubeDownloaderPro.exe"
    if not exe_path.is_file():
        exe_path = BASE_DIR / "dist" / "YouTubeDownloaderPro" / "YouTubeDownloaderPro.exe"

    if exe_path.is_file():
        size_mb = round(exe_path.stat().st_size / (1024 * 1024), 2)
        print("==================================================")
        print(f"SUCCESS! Application packaged at: {exe_path}")
        print(f"File Size: {size_mb} MB")
        print("==================================================")
    else:
        print("Error: Could not locate compiled executable in dist/.")
        sys.exit(1)

if __name__ == "__main__":
    main()
