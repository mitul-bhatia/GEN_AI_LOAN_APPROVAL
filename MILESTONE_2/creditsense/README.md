# CreditSense v2

Streamlit + FastAPI + LangGraph + Chroma implementation for conversational credit assessment.

> Refreshed from current code scan on 2026-04-19.

## Professional Report and Architecture Assets

- Full documentation hub: `../../docs/README.md`
- Professional LaTeX report: `../../docs/CreditSense_M2_Professional_Report.tex`
- Compiled professional report PDF: `../../docs/CreditSense_M2_Professional_Report.pdf`
- Mermaid diagram pack: `../../docs/diagrams/README.md`
- Primary architecture diagram source: `../../docs/diagrams/system-architecture.mmd`
- Master docs rewrite prompt: `../../docs/MILESTONE2_MASTER_DOCS_PROMPT.md`

## Stack

- Frontend: Streamlit (`app.py`)
- Backend: FastAPI (`api.py`)
- Orchestration: LangGraph
- Retrieval: ChromaDB + ONNX MiniLM embeddings (via Chroma embedding utilities)
- LLM provider: Groq API (key rotation supported)

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
```

3. Ingest corpus:

```bash
python3 scripts/ingest.py --source-dir "../../RAG files"
```

4. Start backend:

```bash
bash scripts/run_backend.sh
```

5. Start Streamlit in another terminal:

```bash
bash scripts/run_streamlit.sh
```

## Default Runtime

- Backend URL: `http://localhost:8010`
- Streamlit URL: `http://localhost:8502`

## Production Deployment

- Streamlit App (Frontend): https://genailoanapproval-fdwemcnw96p8fgwpen6xcd.streamlit.app/
- Backend Health Endpoint: https://gen-ai-loan-approval.onrender.com/api/v1/health

## Script Notes

- `run_backend.sh` defaults to `BACKEND_PORT=8010`
- `run_streamlit.sh` defaults to `STREAMLIT_PORT=8502`
- Both scripts source `.env` / `.env.example` if present
- Backend script auto-sets `RAG_DOCS_PATH` to `../../RAG files` when available

## Environment Variables

From `.env.example`:

- `GROQ_KEY_1`, `GROQ_KEY_2`, `GROQ_KEY_3`
- `CHROMA_PATH`
- `COLLECTION_NAME`
- `RAG_DOCS_PATH`
- `RAG_TOP_K`
- `DEFAULT_ANNUAL_INTEREST_RATE`
- `ML_MODEL_PATH`
- `HINDI_FONT_PATH`

## Deployment Files

- `Procfile`: `web: uvicorn api:app --host 0.0.0.0 --port $PORT`
- `render.yaml`: Render service config
- `runtime.txt`: Python runtime pin (`python-3.11.0`)

## Model Fallback

ML adapter load order:

1. `./ml_model/model.pkl`
2. `../../MILESTONE 1/models/logistic_regression.pkl`

## Hindi PDF Font

Hindi PDF rendering uses:

- `assets/fonts/NotoSansDevanagari-Regular.ttf`
