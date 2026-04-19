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

if command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"${BACKEND_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port ${BACKEND_PORT} is busy. Stopping existing listener(s) for a clean restart..."
    BUSY_PIDS="$(lsof -tiTCP:"${BACKEND_PORT}" -sTCP:LISTEN | tr '\n' ' ')"
    if [[ -n "${BUSY_PIDS// /}" ]]; then
      kill ${BUSY_PIDS}
      if lsof -nP -iTCP:"${BACKEND_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
        kill -9 ${BUSY_PIDS} >/dev/null 2>&1 || true
      fi
    fi

    if lsof -nP -iTCP:"${BACKEND_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Unable to free backend port ${BACKEND_PORT}. Stop conflicting process and retry."
      exit 1
    fi
  fi
fi

if [[ -z "${RAG_DOCS_PATH:-}" ]]; then
  DEFAULT_RAG_PATH="$ROOT_DIR/../../RAG files"
  if [[ -d "$DEFAULT_RAG_PATH" ]]; then
    export RAG_DOCS_PATH="$DEFAULT_RAG_PATH"
  fi
fi

echo "Starting CreditSense backend at http://localhost:${BACKEND_PORT}"
if [[ -n "${RAG_DOCS_PATH:-}" ]]; then
  echo "Using RAG docs path: ${RAG_DOCS_PATH}"
fi
exec "$PYTHON_BIN" -m uvicorn api:app --host 0.0.0.0 --port "$BACKEND_PORT"
