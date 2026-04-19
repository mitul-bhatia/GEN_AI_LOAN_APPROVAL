#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/Users/mitulbhatia/Desktop/JAIN_AI/MILESTONE 1/.venv/bin/python3.14}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "python3 not found. Set PYTHON_BIN to a valid Python executable."
    exit 1
  fi
fi

if [[ -f ".env" ]]; then
  set -a
  source ".env"
  set +a
elif [[ -f ".env.example" ]]; then
  set -a
  source ".env.example"
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8010}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8502}"
STREAMLIT_FILE_WATCHER_TYPE="${STREAMLIT_FILE_WATCHER_TYPE:-none}"
export BACKEND_API_BASE_URL="${BACKEND_API_BASE_URL:-http://localhost:${BACKEND_PORT}}"

if command -v lsof >/dev/null 2>&1; then
  for stale_port in 8501 8503 8504 8505; do
    if [[ "$stale_port" == "$STREAMLIT_PORT" ]]; then
      continue
    fi
    if lsof -nP -iTCP:"${stale_port}" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Stopping stale Streamlit listener(s) on port ${stale_port}..."
      STALE_PIDS="$(lsof -tiTCP:"${stale_port}" -sTCP:LISTEN | tr '\n' ' ')"
      if [[ -n "${STALE_PIDS// /}" ]]; then
        kill ${STALE_PIDS}
        if lsof -nP -iTCP:"${stale_port}" -sTCP:LISTEN >/dev/null 2>&1; then
          kill -9 ${STALE_PIDS} >/dev/null 2>&1 || true
        fi
      fi
    fi
  done

  if lsof -nP -iTCP:"${STREAMLIT_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port ${STREAMLIT_PORT} is busy. Stopping existing listener(s) for a clean restart..."
    BUSY_PIDS="$(lsof -tiTCP:"${STREAMLIT_PORT}" -sTCP:LISTEN | tr '\n' ' ')"
    if [[ -n "${BUSY_PIDS// /}" ]]; then
      kill ${BUSY_PIDS}
      if lsof -nP -iTCP:"${STREAMLIT_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
        kill -9 ${BUSY_PIDS} >/dev/null 2>&1 || true
      fi
    fi

    if lsof -nP -iTCP:"${STREAMLIT_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Unable to free Streamlit port ${STREAMLIT_PORT}. Stop conflicting process and retry."
      exit 1
    fi
  fi
fi

echo "Starting CreditSense Streamlit at http://localhost:${STREAMLIT_PORT}"
echo "Using backend: ${BACKEND_API_BASE_URL}"
echo "Using file watcher type: ${STREAMLIT_FILE_WATCHER_TYPE}"
exec "$PYTHON_BIN" -m streamlit run app.py --server.port "$STREAMLIT_PORT" --server.headless true --server.fileWatcherType "$STREAMLIT_FILE_WATCHER_TYPE"
