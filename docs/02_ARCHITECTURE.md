# CreditSense Milestone 2 Architecture

> Refreshed from current code scan on 2026-04-19.

## 1. System Architecture (As Built)

```text
+-----------------------+        HTTP         +-----------------------+
| Streamlit Frontend    |  ---------------->  | FastAPI Backend       |
| app.py                |                     | api.py                |
| - Sidebar form        |                     | - /health             |
| - Chat interface      |                     | - /agent/state/initial|
| - Report panel        |                     | - /agent/turn         |
| - PDF download        |                     | - /agent/seed-parameters
+-----------------------+                     | - /ingest             |
                                              +-----------+-----------+
                                                          |
                                                          v
                                              +-----------------------+
                                              | LangGraph Orchestrator|
                                              | agent/graph.py        |
                                              | guardrail -> conv ->  |
                                              | rag -> policy ->      |
                                              | report -> translate   |
                                              +-----------+-----------+
                                                          |
                                  +-----------------------+----------------------+
                                  |                                              |
                                  v                                              v
                      +------------------------+                     +------------------------+
                      | ChromaDB Persistent    |                     | Groq LLM APIs          |
                      | services/retriever.py  |                     | guardrail/extract/     |
                      | scripts/ingest.py      |                     | report/translate nodes |
                      +------------------------+                     +------------------------+
```

## 2. Layer Responsibilities

### 2.1 Frontend Layer (`app.py`)

- Collects borrower details from sidebar widgets
- Sends structured parameters to backend via `seed-parameters`
- Runs chat turns against backend via `agent/turn`
- Shows computed metrics, responses, and final report
- Downloads English and Hindi report PDFs

### 2.2 API Layer (`api.py`)

- Exposes REST endpoints
- Initializes or accepts current agent state
- Invokes one graph turn per request
- Normalizes seeded form parameters
- Triggers ingestion pipeline when requested
- Loads environment variables at startup via `python-dotenv`

### 2.3 Orchestration Layer (`agent/graph.py`)

- Defines six nodes and route conditions
- Enforces deterministic execution order after report trigger
- Merges graph result into original state to avoid key loss

### 2.4 Service Layer (`services/*.py`)

- Guardrails
- Profile parsing
- Financial metric computation
- ML score adaptation
- Policy threshold checks
- Retrieval and citation preparation
- Report generation
- Translation
- PDF generation

## 3. LangGraph Node Flow

```text
START
  -> guardrail
     -> END                    (if blocked)
     -> conversation           (if allowed)
        -> END                 (if profile incomplete OR report not requested)
        -> rag_retriever       (if profile complete AND report requested)
           -> policy
           -> report
           -> translate
           -> END
```

## 4. Node Routing Conditions

1. `guardrail` to `conversation` when `is_finance_query == True`
2. `guardrail` to `END` when `is_finance_query == False`
3. `conversation` to `rag_retriever` when both are true:
   - `profile_complete == True`
   - `report_requested == True`
4. Otherwise `conversation` exits current turn with follow-up or guidance

## 5. State Architecture

State type is defined in `agent/state.py` using `TypedDict`.

Major state blocks:

1. Conversation: `messages`, `assistant_reply`, `trace`
2. Intake: `collected`, `missing_fields`, `profile_complete`
3. Guardrail: `is_finance_query`, `guardrail_reason`
4. Analytics: `computed_ratios`, `ml_risk_score`, `ml_risk_class`
5. Retrieval: `rag_chunks`, `citations`, `conversation_context`
6. Decisioning: `policy_checks`, `risk_flags`, `decision`, `decision_score`
7. Output: `report_en`, `report_hi`, `report_requested`

## 6. Two Main Runtime Paths

### 6.1 Guidance Path (No final report request)

1. User asks finance question or provides partial intake details
2. Guardrail passes
3. Conversation node extracts updates and computes ratios
4. Assistant returns guidance / next questions
5. Turn ends without full report chain

### 6.2 Report Generation Path

1. Profile becomes complete
2. User asks to generate report
3. RAG retrieval node fetches regulatory context
4. Policy node computes checks and final score band
5. Report node composes English report
6. Translate node creates Hindi report
7. UI enables PDF download buttons

## 7. Retrieval Architecture

- Vector store: Chroma persistent client
- Embedding function: `chromadb.utils.embedding_functions.ONNXMiniLM_L6_V2`
- Query includes profile factors + conversation context
- Default retrieval depth: `RAG_TOP_K` (default 8)

## 8. Decisioning Architecture

Decision is deterministic in `services/policy_engine.py`:

- Base score = 100
- Each `FAIL` check: -18
- Each `WATCH` check: -10
- Score bands:
  - `>= 80`: `APPROVE`
  - `>= 60`: `CONDITIONAL`
  - `< 60`: `ESCALATE`

## 9. Reliability Patterns Implemented

1. LLM-first with deterministic fallback for:
   - conversational extraction augmentation
   - report generation
   - Hindi translation
2. Key rotation for Groq API keys (`groq_pool.py`)
3. Defensive state merge in graph runner
4. Backend/UI decoupling through HTTP client module

## 10. Configuration Surface

Primary runtime config is in `services/settings.py` and `.env`.

Important keys:

- `CHROMA_PATH`
- `COLLECTION_NAME`
- `RAG_DOCS_PATH`
- `RAG_TOP_K`
- `DEFAULT_ANNUAL_INTEREST_RATE`
- `ML_MODEL_PATH`
- optional override: `ML_MODEL_FALLBACK_PATH`
- `HINDI_FONT_PATH`
- `BACKEND_API_BASE_URL`

## 11. Deployment Shape (Current + Practical)

Current implementation is local-first:

- Backend on one process
- Streamlit frontend on another process
- Chroma persisted to local filesystem path

Practical production split:

1. API service host for FastAPI
2. Streamlit app host
3. persistent disk for Chroma store
4. environment-managed Groq secrets

Repository deployment helpers currently included:

- `Procfile`
- `render.yaml`
- `runtime.txt`
