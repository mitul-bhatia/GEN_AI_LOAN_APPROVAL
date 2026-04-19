# Milestone 2: CreditSense (Current Implementation)

This milestone contains the active CreditSense v2 implementation under:

- `creditsense/`

> Refreshed from current code scan on 2026-04-19.

## What Is In Scope

Milestone 2 currently implements:

1. Streamlit frontend (`creditsense/app.py`)
2. FastAPI backend (`creditsense/api.py`)
3. LangGraph multi-node orchestration (`creditsense/agent/*`)
4. Chroma-based RAG ingestion and retrieval (`creditsense/scripts/ingest.py`, `creditsense/services/retriever.py`)
5. Deterministic policy scoring + ML adapter (`creditsense/services/policy_engine.py`, `creditsense/services/ml_adapter.py`)
6. English and Hindi report generation with PDF download (`creditsense/services/report_generator.py`, `creditsense/services/translator.py`, `creditsense/services/pdf_exporter.py`)

## Quick Start

From this folder:

```bash
cd creditsense
pip install -r requirements.txt
python3 scripts/ingest.py --source-dir "../../RAG files"
bash scripts/run_backend.sh
```

In a second terminal:

```bash
cd creditsense
bash scripts/run_streamlit.sh
```

## Default Local Ports

- Backend: `8010`
- Streamlit: `8502`

## Key Endpoints

- `GET /api/v1/health`
- `GET /api/v1/agent/state/initial`
- `POST /api/v1/agent/turn`
- `POST /api/v1/agent/seed-parameters`
- `POST /api/v1/ingest`

## Deployment Files Present

Inside `creditsense/`:

- `Procfile`
- `render.yaml`
- `runtime.txt`

## Documentation

Full project documentation is available in:

- `../docs/README.md`
