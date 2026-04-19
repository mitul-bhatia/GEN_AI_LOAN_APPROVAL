# CreditSense — Codebase File Map

> **Complete source file inventory with purpose, dependencies, and line counts**

---

## 1. Project Root (`MILESTONE 2/creditsense/`)

```
creditsense/
├── app.py                          # Streamlit frontend (796 lines)
├── api.py                          # FastAPI backend (241 lines)
├── requirements.txt                # Python dependencies (19 entries)
├── .env                            # Environment variables (API keys, paths)
├── .env.example                    # Template environment file
├── .gitignore                      # Git ignore rules
├── README.md                       # Project README
│
├── agent/                          # LangGraph agent core
│   ├── __init__.py                 # Package init
│   ├── graph.py                    # StateGraph definition + run_turn() (82 lines)
│   ├── nodes.py                    # All 6 node implementations (456 lines)
│   ├── state.py                    # AgentState TypedDict + initializer (102 lines)
│   └── prompts.py                  # All LLM system prompts (58 lines)
│
├── services/                       # Business logic services
│   ├── __init__.py                 # Package init
│   ├── guardrail.py                # Multi-layer safety system (181 lines)
│   ├── profile_parser.py           # Borrower field extraction (588 lines)
│   ├── borrower_metrics.py         # EMI, DTI, LTV computation (37 lines)
│   ├── ml_adapter.py               # ML model + heuristic scoring (124 lines)
│   ├── policy_engine.py            # NBFC policy cutoff checks (182 lines)
│   ├── retriever.py                # ChromaDB RAG retrieval (96 lines)
│   ├── report_generator.py         # Credit report generation (215 lines)
│   ├── translator.py               # Hindi translation service (84 lines)
│   ├── pdf_exporter.py             # PDF generation (fpdf2) (170 lines)
│   ├── groq_pool.py                # Round-robin API key manager (48 lines)
│   ├── groq_client.py              # Groq HTTP completion client (82 lines)
│   ├── backend_client.py           # Streamlit → FastAPI HTTP client (64 lines)
│   └── settings.py                 # Centralized configuration (39 lines)
│
├── scripts/                        # Utility scripts
│   ├── ingest.py                   # RAG document ingestion (218 lines)
│   ├── e2e_scenarios.py            # End-to-end test scenarios (140 lines)
│   ├── run_backend.sh              # Backend startup script
│   └── run_streamlit.sh            # Streamlit startup script
│
├── assets/
│   └── fonts/                      # Hindi PDF font directory
│       └── NotoSansDevanagari-Regular.ttf  # Devanagari font
│
├── chroma_store/                   # ChromaDB persistent storage (gitignored)
│   ├── chroma.sqlite3              # Metadata + text storage
│   └── <hash>/                     # HNSW vector index
│
└── rag_docs/                       # Local RAG docs (symlinked or copied)
```

---

## 2. File-by-File Reference

### 2.1 Entry Points

| File | Role | Key Exports |
|---|---|---|
| `app.py` | Streamlit frontend — chat UI, parameter form, report panel, PDF downloads | `main()` |
| `api.py` | FastAPI backend — RESTful API serving agent turns, parameter seeding, ingestion | `app` (FastAPI instance) |

### 2.2 Agent Module (`agent/`)

| File | Role | Key Exports |
|---|---|---|
| `graph.py` | LangGraph StateGraph definition, conditional edge routing, state merging | `get_compiled_graph()`, `run_turn()`, `make_initial_state` |
| `nodes.py` | All 6 node function implementations (guardrail, conversation, RAG, policy, report, translate) | `guardrail_node`, `conversation_node`, `rag_retriever_node`, `policy_node`, `report_node`, `translate_node` |
| `state.py` | `AgentState` TypedDict definition, 15 required fields list, initial state factory | `AgentState`, `REQUIRED_FIELDS`, `make_initial_state()`, `initial_collected()` |
| `prompts.py` | All LLM system prompts (guardrail, extraction, report, translation) | `GUARDRAIL_PROMPT`, `CONVERSATION_EXTRACTION_PROMPT`, `REPORT_PROMPT`, `TRANSLATE_PROMPT` |

### 2.3 Services Module (`services/`)

| File | Role | Dependencies |
|---|---|---|
| `guardrail.py` | 3-layer safety: project safety → continuation detection → finance domain check | `groq_client`, `groq_pool`, `agent.prompts` |
| `profile_parser.py` | Dual extraction (regex + LLM), field normalization, grouped question flow, report intent detection | `groq_client`, `groq_pool`, `agent.prompts`, `agent.state` |
| `borrower_metrics.py` | EMI formula, DTI/LTV ratio computation | None (pure math) |
| `ml_adapter.py` | Milestone 1 model loading (joblib), heuristic fallback scoring | `joblib`, `pandas`, `settings` |
| `policy_engine.py` | 6 NBFC cutoff checks, decision scoring, band classification | None (pure logic) |
| `retriever.py` | ChromaDB query, embedding, chunk + citation formatting | `chromadb`, `sentence_transformers`, `settings` |
| `report_generator.py` | LLM report with consistency validation + deterministic fallback | `groq_client`, `groq_pool`, `agent.prompts` |
| `translator.py` | LLM Hindi translation with Devanagari validation + deterministic fallback | `groq_client`, `groq_pool`, `agent.prompts` |
| `pdf_exporter.py` | fpdf2-based PDF generation (English + Hindi) with font embedding | `fpdf2`, `settings` |
| `groq_pool.py` | Thread-safe round-robin API key rotation (up to 5 keys) | `threading`, `os` |
| `groq_client.py` | Groq API HTTP client with retry + key rotation | `httpx`, `groq_pool` |
| `backend_client.py` | Streamlit → FastAPI HTTP client for all endpoints | `httpx` |
| `settings.py` | Centralized config: paths, rates, model locations | `os`, `pathlib` |

### 2.4 Scripts (`scripts/`)

| File | Role | Usage |
|---|---|---|
| `ingest.py` | RAG document ingestion: discover → extract → chunk → embed → upsert | `python scripts/ingest.py --source-dir ./rag_docs` |
| `e2e_scenarios.py` | 5 automated borrower scenarios for end-to-end API testing | `python scripts/e2e_scenarios.py --base-url http://localhost:8010` |
| `run_backend.sh` | Backend startup helper | `bash scripts/run_backend.sh` |
| `run_streamlit.sh` | Streamlit startup helper | `bash scripts/run_streamlit.sh` |

---

## 3. Dependency Graph

```
app.py (Streamlit)
├── agent.state          (AgentState, make_initial_state)
├── services.backend_client  (HTTP → api.py)
└── services.pdf_exporter    (PDF bytes)

api.py (FastAPI)
├── agent.graph          (run_turn)
├── agent.state          (AgentState, REQUIRED_FIELDS, make_initial_state)
├── scripts.ingest       (ingestion function)
├── services.profile_parser  (merge, missing fields, next question)
└── services.settings    (config)

agent/graph.py
├── agent.nodes          (all 6 node functions)
└── agent.state          (AgentState, make_initial_state)

agent/nodes.py
├── agent.state          (AgentState)
├── services.borrower_metrics
├── services.guardrail
├── services.ml_adapter
├── services.policy_engine
├── services.profile_parser
├── services.report_generator
├── services.retriever
├── services.settings
└── services.translator
```

---

## 4. Line Count Summary

| Module | Files | Lines |
|---|---|---|
| **Entry Points** (app.py, api.py) | 2 | 1,037 |
| **Agent** (graph, nodes, state, prompts) | 4 | 698 |
| **Services** (all 13 service files) | 13 | 1,750 |
| **Scripts** (ingest, e2e, shell) | 4 | ~360 |
| **Total** | **23** | **~3,845** |

---

*CreditSense v2.0 — Codebase File Map | Last Updated: April 2026*
