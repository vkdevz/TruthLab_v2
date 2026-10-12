#!/bin/bash
# ==============================================================================
# TruthLab: Unified Local Launcher (Backend Port 8000 + Frontend Port 1234)
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "  🚀 Starting TruthLab Multimodal Verification System"
echo "======================================================================"

# Check if ports 8000 or 1234 are in use and kill if necessary
for PORT in 8000 1234; do
  PID=$(lsof -ti :$PORT)
  if [ -n "$PID" ]; then
    echo "⚠️  Port $PORT is already in use by PID $PID. Terminating existing process..."
    kill -9 $PID 2>/dev/null
  fi
done

# Activate virtualenv if present
if [ -d "$PROJECT_DIR/.venv" ]; then
  PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python"
  UVICORN_EXEC="$PROJECT_DIR/.venv/bin/uvicorn"
else
  PYTHON_EXEC="python3"
  UVICORN_EXEC="uvicorn"
fi

echo "▶ 1. Starting Backend API Server on http://127.0.0.1:8000..."
"$UVICORN_EXEC" backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "▶ 2. Starting Frontend Dev Server on http://localhost:1234..."
cd "$PROJECT_DIR/frontend"
npm run dev -- --port 1234 --host &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

# Trap CTRL+C and termination signals
cleanup() {
  echo ""
  echo "🛑 Shutting down TruthLab services (PID $BACKEND_PID, $FRONTEND_PID)..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "======================================================================"
echo "  ✨ TruthLab is LIVE!"
echo "  🌐 Web Dashboard:    http://localhost:1234"
echo "  📚 API Docs:         http://localhost:1234/api/v1/docs"
echo "  ❤️  Health Check:     http://localhost:1234/api/v1/health"
echo "======================================================================"
echo "  Press [CTRL+C] at any time to stop both servers."
echo "======================================================================"

# Keep alive and monitor child processes
wait
