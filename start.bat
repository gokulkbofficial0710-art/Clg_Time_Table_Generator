@echo off
setlocal enabledelayedexpansion

title Exam Timetable Generator - Host Server

echo =====================================================================
echo       The Exam Timetable from Hell - University Scheduler
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: 2. Check Node
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not found in PATH. Please install Node.js 18+ and npm.
    pause
    exit /b 1
)

:: 3. Setup Backend Virtual Environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [1/4] Creating Python virtual environment in backend\venv...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [2/4] Installing backend dependencies...
    backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install backend requirements.
        pause
        exit /b 1
    )
) else (
    echo [OK] Backend virtual environment verified.
)

:: 4. Run database migrations
echo [3/4] Initializing / migrating SQLite database...
cd backend
venv\Scripts\alembic.exe upgrade head
cd ..

:: 5. Ensure Frontend Build exists
if not exist "frontend\dist\index.html" (
    echo [4/4] Building frontend production bundle...
    cd frontend
    call npm run build
    cd ..
) else (
    echo [OK] Frontend production build verified.
)

echo.
echo =====================================================================
echo Select launch mode:
echo   [1] Production Unified Server (Recommended: Serves UI & API on port 8000)
echo   [2] Development Mode (FastAPI on 8000 + Vite Dev on 5173)
echo =====================================================================
set /p MODE="Enter choice (1 or 2, default is 1): "
if "%MODE%"=="" set MODE=1

if "%MODE%"=="2" (
    echo.
    echo Starting Backend API server on 0.0.0.0:8000...
    start "Exam Scheduler - Backend (Port 8000)" cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    
    echo Starting Frontend Vite server on 0.0.0.0:5173...
    start "Exam Scheduler - Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"
    
    echo.
    echo -------------------------------------------------------------
    echo App is launching!
    echo Local Web UI:    http://localhost:5173
    echo Backend API:     http://localhost:8000
    echo API Docs:        http://localhost:8000/docs
    echo -------------------------------------------------------------
    timeout /t 3 >nul
    start http://localhost:5173
) else (
    echo.
    echo Starting Unified Server on 0.0.0.0:8000...
    echo.
    echo -------------------------------------------------------------
    echo Application is LIVE!
    echo Access from this machine: http://localhost:8000
    echo Access from any device on network: http://0.0.0.0:8000
    echo API Documentation:        http://localhost:8000/docs
    echo Press Ctrl+C in this window to stop the server.
    echo -------------------------------------------------------------
    echo.
    start http://localhost:8000
    cd backend
    venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
)
