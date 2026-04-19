# CreditSense — Setup & Deployment Guide

> **Local development, environment configuration, and deployment instructions**

---

## 1. Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| **Python** | ≥ 3.10 | Runtime |
| **pip** | Latest | Package management |
| **Git** | Latest | Version control |
| **Groq API Key(s)** | 1-5 keys | LLM inference (guardrail, extraction, report, translation) |

### Optional

| Requirement | Purpose |
|---|---|
| **NotoSansDevanagari-Regular.ttf** | Hindi PDF rendering with Devanagari script |
| **Milestone 1 model.pkl** | Trained ML risk model (heuristic fallback is available) |

---

## 2. Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd JAIN_AI/MILESTONE\ 2/creditsense

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your Groq API key(s):
#   GROQ_KEY_1=gsk_...
#   GROQ_KEY_2=gsk_...  (optional)

# 5. Ingest RAG documents (one-time)
python scripts/ingest.py --source-dir "../../RAG files"

# 6. Start the backend (Terminal 1)
uvicorn api:app --host 0.0.0.0 --port 8010

# 7. Start the frontend (Terminal 2)
streamlit run app.py --server.port 8502

# 8. Open in browser
# Frontend: http://localhost:8502
# Backend API: http://localhost:8010
# Health Check: http://localhost:8010/api/v1/health
```

---

## 3. Environment Variables

### Required

```bash
# At least ONE Groq key is required for LLM features
GROQ_KEY_1=gsk_your_key_here
```

### Optional (with defaults)

```bash
# Additional Groq keys for round-robin pool
GROQ_KEY_2=gsk_...
GROQ_KEY_3=gsk_...
GROQ_KEY_4=gsk_...
GROQ_KEY_5=gsk_...
GROQ_API_KEY=gsk_...           # Alternative single key variable

# Paths
CHROMA_PATH=./chroma_store                     # ChromaDB persistence dir
COLLECTION_NAME=creditsense_docs               # ChromaDB collection name
RAG_DOCS_PATH=../../RAG files                  # Source regulatory documents
ML_MODEL_PATH=./ml_model/model.pkl             # Trained ML model
ML_MODEL_FALLBACK_PATH=../../MILESTONE 1/models/logistic_regression.pkl
HINDI_FONT_PATH=./assets/fonts/NotoSansDevanagari-Regular.ttf

# Server Configuration
BACKEND_API_BASE_URL=http://localhost:8010      # Backend URL for Streamlit
BACKEND_CORS_ORIGINS=http://localhost:8501,http://localhost:8502,http://localhost:3000

# RAG Parameters
RAG_TOP_K=8                                     # Number of chunks to retrieve
DEFAULT_ANNUAL_INTEREST_RATE=0.15               # 15% annual interest for EMI calc
```

---

## 4. Dependency Manifest

### Python Packages (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32.0 | Frontend UI framework |
| `fastapi` | ≥ 0.111.0 | Backend API framework |
| `uvicorn` | ≥ 0.30.0 | ASGI server |
| `langgraph` | ≥ 0.1.0 | Agent graph orchestration |
| `chromadb` | ≥ 0.4.0 | Vector database |
| `sentence-transformers` | Latest | Embedding model |
| `pdfplumber` | Latest | PDF text extraction |
| `python-docx` | Latest | DOCX text extraction |
| `fpdf2` | Latest | PDF generation |
| `reportlab` | Latest | Alternative PDF library |
| `httpx` | Latest | HTTP client (Groq API, backend) |
| `pydantic` | ≥ 2.0 | Data validation |
| `python-dotenv` | Latest | Environment variable loading |
| `scikit-learn` | Latest | ML model framework |
| `joblib` | Latest | Model serialization |
| `typing-extensions` | Latest | Type hint support |
| `numpy` | Latest | Numerical computing |
| `pandas` | Latest | DataFrame operations |

---

## 5. Running Individual Components

### 5.1 Backend Only

```bash
cd creditsense
uvicorn api:app --host 0.0.0.0 --port 8010 --reload
```

### 5.2 Frontend Only (requires backend running)

```bash
cd creditsense
streamlit run app.py --server.port 8502
```

### 5.3 RAG Ingestion

```bash
# Default source (auto-discovers ../../RAG files/)
python scripts/ingest.py

# Custom source
python scripts/ingest.py --source-dir ./rag_docs --chunk-size 1200 --overlap 150

# Full options
python scripts/ingest.py \
  --source-dir "../../RAG files" \
  --chroma-path ./chroma_store \
  --collection creditsense_docs \
  --chunk-size 1200 \
  --overlap 150 \
  --embedding-model all-MiniLM-L6-v2
```

### 5.4 End-to-End Testing

```bash
# Start backend first, then run:
python scripts/e2e_scenarios.py --base-url http://localhost:8010 --pretty
```

This runs 5 borrower scenarios and validates:
- Report generation
- RAG chunk retrieval
- Citation presence
- Decision scoring

---

## 6. Verification Checklist

After setup, verify the system is working:

| Check | Command/URL | Expected |
|---|---|---|
| Backend health | `GET http://localhost:8010/api/v1/health` | `{"status": "ok", ...}` |
| Initial state | `GET http://localhost:8010/api/v1/agent/state/initial` | `{"state": {...}}` |
| Streamlit UI | `http://localhost:8502` | CreditSense Agent page loads |
| Backend connection | Check "Backend Connected" badge in UI | Green success badge |
| Groq API | Fill form + send chat message | Agent responds (not error) |
| RAG retrieval | Complete profile + "generate report" | Report includes regulatory citations |
| PDF download | Click download buttons after report | PDF files download |

---

## 7. Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---|---|---|
| "Backend Offline" in UI | Backend not running or wrong port | Start `uvicorn api:app --port 8010` |
| "No Groq API keys configured" | Missing `.env` file or empty keys | Add `GROQ_KEY_1=gsk_...` to `.env` |
| Empty RAG results | ChromaDB not indexed | Run `python scripts/ingest.py --source-dir "../../RAG files"` |
| Hindi PDF shows Latin text | Missing Devanagari font | Place `NotoSansDevanagari-Regular.ttf` in `assets/fonts/` |
| ModuleNotFoundError | Dependencies not installed | Run `pip install -r requirements.txt` |
| "Agent execution failed" | LLM rate limit or timeout | Check Groq API status; add more keys |
| Streamlit port conflict | Port 8502 in use | Use `streamlit run app.py --server.port 8503` |

---

## 8. Production Deployment (Planned)

### 8.1 Streamlit Community Cloud

```bash
# 1. Push chroma_store/ to repo (pre-indexed)
# 2. Create secrets.toml in Streamlit Cloud dashboard:
#    [secrets]
#    GROQ_KEY_1 = "gsk_..."
#    BACKEND_API_BASE_URL = "https://your-render-backend.onrender.com"
```

### 8.2 Render Backend

```bash
# Use infra/render.yaml blueprint:
# - Web Service: FastAPI backend (Python runtime)
# - Private Service: ChromaDB with persistent disk at /data/chroma
```

### 8.3 Deployment Architecture

```
┌────────────────────┐          ┌─────────────────────────┐
│  Streamlit Cloud   │──HTTPS──▸│  Render Web Service     │
│  (Frontend)        │          │  (FastAPI Backend)       │
│                    │          │                          │
│  secrets.toml      │          │  .env from Render        │
│  for API keys      │          │  dashboard               │
└────────────────────┘          └──────────┬──────────────┘
                                           │ internal
                                           ▼
                                ┌─────────────────────────┐
                                │  Render Private Service  │
                                │  (ChromaDB)              │
                                │  Persistent Disk: /data  │
                                └─────────────────────────┘
```

---

*CreditSense v2.0 — Setup & Deployment Guide | Last Updated: April 2026*
