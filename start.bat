@echo off
setlocal
title EDITH - Autonomous AI Job Intelligence Platform
echo ==========================================================
echo  Launching EDITH Platform (FastAPI Backend + React Frontend)...
echo ==========================================================

cd /d "%~dp0"
set "PROJECT_DIR=%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python Launcher was not found. Install Python 3 and enable the Python Launcher.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm was not found. Install Node.js 20.19+ or 22.12+ and restart this launcher.
    pause
    exit /b 1
)

where curl.exe >nul 2>&1
if errorlevel 1 (
    echo ERROR: curl.exe was not found. Install a recent Windows version with curl support.
    pause
    exit /b 1
)

echo Checking backend dependencies...
py -3 -c "import backend.main" >nul 2>&1
if errorlevel 1 (
    echo Preparing an isolated Python environment for the backend...
    if not exist ".venv\Scripts\python.exe" (
        py -3 -m venv .venv
        if errorlevel 1 (
            echo ERROR: Could not create the backend virtual environment.
            pause
            exit /b 1
        )
    )
    set "PYTHON_EXE=%PROJECT_DIR%.venv\Scripts\python.exe"
    "%PYTHON_EXE%" -c "import backend.main" >nul 2>&1
    if errorlevel 1 (
        echo Installing backend dependencies from requirements.txt...
        "%PYTHON_EXE%" -m pip install -r backend\requirements.txt
        if errorlevel 1 (
            echo ERROR: Backend dependency installation failed.
            pause
            exit /b 1
        )
    )
    "%PYTHON_EXE%" -c "import backend.main" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Backend failed to import after dependency installation.
        pause
        exit /b 1
    )
) else (
    for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%P"
)

if not exist "frontend\node_modules\.bin\vite.cmd" (
    echo Frontend dependencies are missing. Installing from package-lock.json...
    pushd frontend
    call npm ci
    if errorlevel 1 (
        popd
        echo ERROR: Frontend dependency installation failed.
        pause
        exit /b 1
    )
    popd
)

echo [1/2] Starting FastAPI Backend on port 8000...
start "EDITH Backend" /D "%PROJECT_DIR%" cmd /k ""%PYTHON_EXE%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Vite Frontend on port 5173...
start "EDITH Frontend" /D "%PROJECT_DIR%frontend" cmd /k "npm run dev"

echo Waiting for backend readiness...
for /L %%i in (1,1,30) do (
    curl.exe --silent --fail --output NUL --max-time 1 http://127.0.0.1:8000/api/health >nul 2>&1
    if not errorlevel 1 goto :backend_ready
    ping 127.0.0.1 -n 2 >nul
)
echo ERROR: Backend did not become ready. Check the EDITH Backend window for details.
pause
exit /b 1

:backend_ready
echo Waiting for frontend readiness...
for /L %%i in (1,1,30) do (
    curl.exe --silent --fail --output NUL --max-time 1 http://127.0.0.1:5173 >nul 2>&1
    if not errorlevel 1 goto :frontend_ready
    ping 127.0.0.1 -n 2 >nul
)
echo ERROR: Frontend did not become ready. Check the EDITH Frontend window for details.
pause
exit /b 1

:frontend_ready
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
