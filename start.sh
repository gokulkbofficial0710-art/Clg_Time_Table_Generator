#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "      The Exam Timetable from Hell - University Scheduler           "
echo "====================================================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Please install Python 3.10+."
    exit 1
fi

# Check Node
if ! command -v node &>/dev/null; then
    echo "[ERROR] node not found. Please install Node.js 18+ & npm."
    exit 1
fi

# Setup Venv
if [ ! -f "backend/venv/bin/python" ]; then
    echo "[1/3] Setting up Python virtual environment..."
    python3 -m venv backend/venv
    backend/venv/bin/pip install -r backend/requirements.txt
fi

# Run Migrations
echo "[2/3] Checking database schema & migrations..."
(cd backend && ./venv/bin/alembic upgrade head)

# Build Frontend
if [ ! -f "frontend/dist/index.html" ]; then
    echo "[3/3] Building frontend production bundle..."
    (cd frontend && npm install && npm run build)
else
    echo "[3/3] Frontend production build verified."
fi

echo ""
echo "Choose Launch Mode:"
echo "  1) Unified Production Server (Port 8000 - UI + API together)"
echo "  2) Development Mode (Vite Port 5173 + FastAPI Port 8000)"
read -p "Enter option [1 or 2, default: 1]: " MODE
MODE=${MODE:-1}

if [ "$MODE" = "2" ]; then
    echo "Starting Backend on http://0.0.0.0:8000..."
    (cd backend && ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
    echo "Starting Frontend on http://0.0.0.0:5173..."
    (cd frontend && npm run dev)
else
    echo "Starting Unified Server on http://0.0.0.0:8000..."
    echo "Access locally: http://localhost:8000"
    echo "Access across network: http://<YOUR_IP>:8000"
    cd backend
    ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
