# PowerShell Launcher for Exam Timetable Generator
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "      The Exam Timetable from Hell - University Scheduler           " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
}

# Check Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not installed or not in PATH."
}

# Backend Venv
$VenvPython = Join-Path $ScriptDir "backend\venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $SharedVenv = "Z:\semester 5\host antigravity\Clg_Time_Table_Generator-main\Clg_Time_Table_Generator-main\backend\venv\Scripts\python.exe"
    if (Test-Path $SharedVenv) {
        $VenvPython = $SharedVenv
        Write-Host "[1/3] Using existing verified Python virtual environment." -ForegroundColor Green
    } else {
        Write-Host "[1/3] Setting up Python virtual environment..." -ForegroundColor Yellow
        python -m venv backend\venv
        & $VenvPython -m pip install -r backend\requirements.txt
    }
}

# Database Migration
Write-Host "[2/3] Checking database schema & migrations..." -ForegroundColor Yellow
Push-Location (Join-Path $ScriptDir "backend")
& $VenvPython -m alembic upgrade head
Pop-Location

# Build Frontend if needed
$DistIndex = Join-Path $ScriptDir "frontend\dist\index.html"
if (-not (Test-Path $DistIndex)) {
    Write-Host "[3/3] Building frontend production bundle..." -ForegroundColor Yellow
    Push-Location (Join-Path $ScriptDir "frontend")
    npm run build
    Pop-Location
} else {
    Write-Host "[3/3] Frontend production build verified." -ForegroundColor Green
}

Write-Host ""
Write-Host "Choose Launch Mode:" -ForegroundColor Cyan
Write-Host "  1) Unified Production Server (Port 8000 - UI + API together)"
Write-Host "  2) Development Mode (Vite Port 5173 + FastAPI Port 8000)"
$Choice = Read-Host "Enter option [1 or 2, default: 1]"
if ([string]::IsNullOrWhiteSpace($Choice)) { $Choice = "1" }

if ($Choice -eq "2") {
    Write-Host "Starting Backend on http://localhost:8000 and Frontend on http://localhost:5173..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptDir\backend'; .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptDir\frontend'; npm run dev"
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5173"
} else {
    Write-Host "Starting Unified Server on http://localhost:8000..." -ForegroundColor Green
    Write-Host "Access locally: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Access across LAN: http://0.0.0.0:8000" -ForegroundColor Cyan
    Start-Process "http://localhost:8000"
    Push-Location (Join-Path $ScriptDir "backend")
    & $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    Pop-Location
}
