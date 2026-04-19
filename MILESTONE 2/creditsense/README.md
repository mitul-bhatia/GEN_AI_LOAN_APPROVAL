# CreditSense v2

Clean rebuild of the CreditSense conversational credit-assessment agent using:

- FastAPI backend API
- Streamlit UI (frontend-only caller)
- LangGraph orchestration
- Chroma local RAG store
- Groq LLM APIs (with key rotation)

## Quick Start

1. Create and activate a virtual environment.
1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Configure environment variables:

```bash
cp .env.example .env
```

1. Set `RAG_DOCS_PATH` to your corpus directory. In this workspace, default is `../../RAG files`.

1. Build Chroma index:

```bash
python scripts/ingest.py --source-dir "../../RAG files"
```

1. Run backend API:

```bash
uvicorn api:app --host 0.0.0.0 --port 8010
```

1. Run Streamlit frontend:

```bash
streamlit run app.py
```

## Easy Run Scripts (Recommended)

Run backend and frontend in separate terminals:

```bash
bash scripts/run_backend.sh
```

```bash
bash scripts/run_streamlit.sh
```

If `8501` is busy, `run_streamlit.sh` automatically picks the next free port (`8502`-`8505`).

Optional env overrides:

- `BACKEND_PORT` (default `8010`)
- `STREAMLIT_PORT` (default `8501`)
- `BACKEND_API_BASE_URL` (frontend target)
- `PYTHON_BIN` (if you want a different Python executable)

## Architecture Note

- FastAPI (`api.py`) contains the backend orchestration endpoints and is the deployable server on Render.
- Streamlit (`app.py`) is strictly the frontend layer that calls backend endpoints.
- Frontend uses `BACKEND_API_BASE_URL` (default: `http://localhost:8010`).

## Render Start Command

Use this start command for backend service:

```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```

## Reusing Milestone 1 Model

The app attempts to load `ml_model/model.pkl` first. If not found, it falls back to
`../../MILESTONE 1/models/logistic_regression.pkl` when available.

## Hindi PDF Font

Place `NotoSansDevanagari-Regular.ttf` in `assets/fonts/` for proper Hindi PDF rendering.
