# CreditSense Setup and Deployment Guide

> Refreshed from current code scan on 2026-04-19.

## 1. Scope

This guide covers runtime setup for:

- `MILESTONE_2/creditsense/`

It includes both script-based startup and manual startup commands.

## 2. Prerequisites

1. macOS/Linux shell
2. Python 3.10+
3. pip
4. network access for Groq API (optional but recommended)
5. regulatory corpus path (default `../../RAG files`)

Optional but recommended:

- working virtual environment
- Milestone 1 model file for ML adapter fallback path

Current hosted runtime pin file:

- `runtime.txt` -> `python-3.11.0`

## 3. Environment Setup

From repository root:

```bash
cd "MILESTONE_2/creditsense"
```

Create and activate venv (if needed):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Note: current embedding path uses Chroma's ONNX MiniLM utility; `requirements.txt` does not include a separate `sentence-transformers` or `torch` pin.

Create env file:

```bash
cp .env.example .env
```

Edit `.env` and set at least one Groq key:

```env
GROQ_KEY_1=your_groq_key
```

## 4. Environment Variables (Implemented)

From `.env.example` and settings:

- `GROQ_KEY_1`, `GROQ_KEY_2`, `GROQ_KEY_3`
- `CHROMA_PATH`
- `COLLECTION_NAME`
- `RAG_DOCS_PATH`
- `RAG_TOP_K`
- `DEFAULT_ANNUAL_INTEREST_RATE`
- `ML_MODEL_PATH`
- `HINDI_FONT_PATH`

Runtime helper variables used by scripts:

- `BACKEND_PORT` (default 8010)
- `STREAMLIT_PORT` (script default 8502)
- `BACKEND_API_BASE_URL`
- `PYTHON_BIN`
- `STREAMLIT_FILE_WATCHER_TYPE`

## 5. One-Time Ingestion

Run from `MILESTONE_2/creditsense`.

Default:

```bash
python3 scripts/ingest.py
```

Workspace corpus explicit path:

```bash
python3 scripts/ingest.py --source-dir "../../RAG files"
```

API-triggered ingestion option:

```bash
curl -X POST http://localhost:8010/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_dir": "../../RAG files"}'
```

## 6. Start Commands (Recommended)

Use helper scripts in two terminals.

Terminal 1:

```bash
bash scripts/run_backend.sh
```

Terminal 2:

```bash
bash scripts/run_streamlit.sh
```

Notes:

1. backend script defaults to port `8010`
2. streamlit script defaults to port `8502`
3. scripts attempt to clear stale listeners on common ports
4. backend script auto-sets `RAG_DOCS_PATH` to `../../RAG files` if present

## 7. Start Commands (Manual Alternative)

Terminal 1 (backend):

```bash
python3 -m uvicorn api:app --host 0.0.0.0 --port 8010
```

Terminal 2 (frontend):

```bash
python3 -m streamlit run app.py --server.port 8502 --server.headless true --server.fileWatcherType none
```

## 8. Health and Smoke Validation

Backend health:

```bash
curl http://localhost:8010/api/v1/health
```

Expected shape:

```json
{
  "status": "ok",
  "service": "CreditSense Backend API",
  "chroma_path": "...",
  "collection": "creditsense_docs"
}
```

Fetch initial state:

```bash
curl http://localhost:8010/api/v1/agent/state/initial
```

## 9. Scenario Test Script

Run all predefined borrower scenarios:

```bash
python3 scripts/e2e_scenarios.py --base-url http://localhost:8010 --pretty
```

Important:

- script default base URL is `http://localhost:8000`
- pass `--base-url` for port `8010`

## 10. Troubleshooting

### 10.1 Backend not reachable

1. verify backend process is running
2. verify port in use (`8010` expected)
3. check `BACKEND_API_BASE_URL` used by frontend

### 10.2 No citations in report

1. verify ingestion completed successfully
2. verify collection path and collection name match runtime settings
3. confirm corpus directory has readable files

### 10.3 Groq errors or slow responses

1. validate key values in env
2. use multiple keys for rotation
3. verify outbound network

### 10.4 Hindi PDF rendering issue

1. ensure `assets/fonts/NotoSansDevanagari-Regular.ttf` exists
2. verify `HINDI_FONT_PATH` matches actual location

## 11. Deployment Notes (Practical)

Current repo supports local-first execution directly.
For hosted deployment, maintain these principles:

1. host FastAPI separately from Streamlit
2. persist Chroma storage on durable disk
3. inject secrets through host secret manager
4. expose only required public endpoints
5. add auth/rate limits before public launch

Deployment helper files currently present in app root:

1. `Procfile`
2. `render.yaml`
3. `runtime.txt`
