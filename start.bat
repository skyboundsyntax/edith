@echo off
setlocal
title EDITH - Autonomous AI Job Intelligence Platform
echo ==========================================================
echo  Launching EDITH Platform (FastAPI Backend + React Frontend)...
echo ==========================================================

cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend on port 8000...
start "EDITH Backend" cmd /k "py -3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Vite Frontend on port 5173...
cd frontend
start "EDITH Frontend" cmd /k "npm run dev"

ping 127.0.0.1 -n 3 >nul

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo Launching in Google Chrome...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://localhost:5173"
    goto :done
)

if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo Launching in Microsoft Edge...
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "http://localhost:5173"
    goto :done
)

echo Launching in default browser...
start "" "http://localhost:5173"

:done
echo ==========================================================
echo  EDITH Platform launched successfully!
echo  Backend:  http://localhost:8000 (Docs: http://localhost:8000/docs)
echo  Frontend: http://localhost:5173
echo ==========================================================
exit /b 0
