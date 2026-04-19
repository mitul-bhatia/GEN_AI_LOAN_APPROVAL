# CreditSense Milestone 2 Codebase File Map

> Refreshed from current code scan on 2026-04-19.

## 1. Scope Covered

This map covers the runnable Milestone 2 app in:

- `MILESTONE 2/creditsense/`

## 2. Top-Level Structure

```text
creditsense/
  .env.example
  .gitignore
  Procfile
  README.md
  api.py
  app.py
  render.yaml
  requirements.txt
  runtime.txt
  agent/
  services/
  scripts/
  assets/
  chroma_store/
  rag_docs/
```

## 3. Core Entry Files

| File | Line Count | Responsibility |
|---|---:|---|
| `api.py` | 248 | FastAPI backend endpoints and graph invocation |
| `app.py` | 956 | Streamlit frontend UI and interaction loop |
| `requirements.txt` | 18 | Python dependency manifest |
| `.env.example` | 11 | Environment variable template |
| `Procfile` | 1 | Process declaration for hosted runtime |
| `render.yaml` | 24 | Render service blueprint |
| `runtime.txt` | 1 | Python runtime pin for deployment |

## 4. Agent Package

| File | Line Count | Responsibility |
|---|---:|---|
| `agent/graph.py` | 81 | Graph wiring, route conditions, state merge |
| `agent/nodes.py` | 493 | All six node implementations |
| `agent/state.py` | 101 | State schema, required fields, initial state |
| `agent/prompts.py` | 87 | Prompt templates for guardrail/extraction/report/translation |
| `agent/__init__.py` | 1 | Package marker |

## 5. Services Package

| File | Line Count | Responsibility |
|---|---:|---|
| `services/settings.py` | 38 | Config defaults and env mapping |
| `services/backend_client.py` | 63 | Frontend HTTP client for backend APIs |
| `services/borrower_metrics.py` | 36 | EMI/DTI/LTV computations |
| `services/groq_pool.py` | 47 | Groq key rotation pool |
| `services/groq_client.py` | 81 | Groq chat completion HTTP wrapper |
| `services/guardrail.py` | 179 | Guardrail and continuation classification |
| `services/ml_adapter.py` | 123 | Model loading and risk scoring fallback |
| `services/policy_engine.py` | 181 | Deterministic underwriting checks |
| `services/profile_parser.py` | 587 | Intake extraction and follow-up orchestration |
| `services/retriever.py` | 103 | Chroma retrieval and citation building |
| `services/report_generator.py` | 214 | English report generation logic |
| `services/translator.py` | 83 | Hindi translation logic |
| `services/pdf_exporter.py` | 169 | PDF export bytes generation |
| `services/__init__.py` | 1 | Package marker |

## 6. Scripts

| File | Line Count | Responsibility |
|---|---:|---|
| `scripts/ingest.py` | 217 | Corpus ingestion and indexing into Chroma |
| `scripts/e2e_scenarios.py` | 139 | Multi-scenario API smoke test |
| `scripts/run_backend.sh` | 76 | Backend startup helper |
| `scripts/run_streamlit.sh` | 79 | Streamlit startup helper |

## 7. Assets and Runtime Data

| Path | Purpose |
|---|---|
| `assets/fonts/NotoSansDevanagari-Regular.ttf` | Hindi PDF font support |
| `chroma_store/` | Local persistent vector database files |
| `rag_docs/` | Local optional corpus directory (fallback source) |

## 8. Dependency Flow Summary

```text
app.py
  -> services/backend_client.py
     -> api.py
        -> agent/graph.py
           -> agent/nodes.py
              -> services/* modules

scripts/ingest.py
  -> chromadb + sentence-transformers
  -> writes to chroma_store/

services/retriever.py
  -> reads from chroma_store/
```

## 9. Module Groups By Concern

### 9.1 Orchestration

- `agent/graph.py`
- `agent/nodes.py`
- `agent/state.py`

### 9.2 Intelligence and Reasoning

- `services/guardrail.py`
- `services/profile_parser.py`
- `services/ml_adapter.py`
- `services/policy_engine.py`
- `services/retriever.py`
- `services/report_generator.py`
- `services/translator.py`

### 9.3 Runtime and Integration

- `api.py`
- `app.py`
- `services/backend_client.py`
- `services/settings.py`
- `scripts/*.py`
- `scripts/*.sh`

## 10. Quick Orientation For New Reviewers

If you have limited time, read in this order:

1. `api.py`
2. `agent/graph.py`
3. `agent/nodes.py`
4. `services/profile_parser.py`
5. `services/policy_engine.py`
6. `services/retriever.py`
7. `services/report_generator.py`
8. `app.py`
