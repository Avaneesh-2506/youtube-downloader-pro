@echo off
title YouTube Downloader Pro - Launcher
echo ==============================================
echo   Launching YouTube Downloader Pro (Full-Stack)
echo ==============================================
start "YouTube Downloader Backend" cmd /c "cd /d %~dp0 && start-backend.bat"
timeout /t 2 /nobreak >nul
start "YouTube Downloader Frontend" cmd /c "cd /d %~dp0 && start-frontend.bat"
echo Services launched!
echo Backend: http://localhost:8000 (Swagger docs at http://localhost:8000/docs)
echo Frontend: http://localhost:5173
echo.
pause
