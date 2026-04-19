# CreditSense — System Architecture

> **Complete technical architecture of the LangGraph agent, RAG pipeline, and service topology**

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      STREAMLIT FRONTEND (app.py)                    │
│                                                                     │
│   🧾 Borrower Parameter Form  ←→  💬 Chat Interface                │
│   📊 Report Panel (EN/HI tabs) ←→  📄 PDF Download Buttons         │
│                                                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  HTTP (httpx)
                            │  POST /api/v1/agent/turn
                            │  POST /api/v1/agent/seed-parameters
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (api.py)                          │
│                                                                     │
│   /api/v1/health          → System health check                     │
│   /api/v1/agent/state/initial → Fresh AgentState                    │
│   /api/v1/agent/turn      → Execute one LangGraph agent turn        │
│   /api/v1/agent/seed-parameters → Form parameter injection          │
│   /api/v1/ingest          → Trigger RAG document ingestion          │
│                                                                     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  Python function call (in-process)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│               LANGGRAPH ORCHESTRATOR (agent/graph.py)                │
│                                                                     │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────┐             │
│   │ guardrail│───▸│ conversation │───▸│ rag_retriever │             │
│   │   node   │    │    node      │    │     node      │             │
│   └──────────┘    └──────────────┘    └───────┬───────┘             │
│        │                 │                    │                      │
│        │ (block)         │ (ask next Q)       ▼                     │
│        ▼                 ▼              ┌──────────┐                │
│       END               END             │  policy  │                │
│                                         │   node   │                │
│                                         └────┬─────┘                │
│                                              ▼                      │
│                                        ┌──────────┐                 │
│                                        │  report  │                 │
│                                        │   node   │                 │
│                                        └────┬─────┘                 │
│                                              ▼                      │
│                                        ┌───────────┐                │
│                                        │ translate  │                │
│                                        │   node     │                │
│                                        └────┬──────┘                │
│                                              ▼                      │
│                                             END                     │
└─────────────────────────────────────────────────────────────────────┘
         │                                      │
         ▼                                      ▼
┌──────────────────┐                  ┌──────────────────────┐
│  CHROMADB        │                  │   GROQ API           │
│  (Local Persist) │                  │   llama-3.1-8b       │
│  57 docs         │                  │   llama-3.3-70b      │
│  8,452 chunks    │                  │   3-key rotation     │
│  MiniLM-L6-v2   │                  │   Round-robin pool   │
└──────────────────┘                  └──────────────────────┘
```

---

## 2. LangGraph Agent Pipeline

The agent is implemented as a **LangGraph `StateGraph`** with 6 nodes connected by conditional edges. Every user message triggers a single graph invocation.

### 2.1 Graph Definition (`agent/graph.py`)

```python
graph = StateGraph(AgentState)

# Nodes
graph.add_node("guardrail",     guardrail_node)
graph.add_node("conversation",  conversation_node)
graph.add_node("rag_retriever", rag_retriever_node)
graph.add_node("policy",        policy_node)
graph.add_node("report",        report_node)
graph.add_node("translate",     translate_node)

# Entry
graph.set_entry_point("guardrail")

# Conditional routing
guardrail  →  conversation  (if finance query)
guardrail  →  END           (if blocked)
conversation → rag_retriever (if profile complete AND report requested)
conversation → END           (otherwise — ask next question)

# Linear chain after RAG
rag_retriever → policy → report → translate → END
```

### 2.2 Routing Logic

| From Node | Condition | Next Node |
|---|---|---|
| `guardrail` | `is_finance_query = True` | `conversation` |
| `guardrail` | `is_finance_query = False` | `END` (refusal reply) |
| `conversation` | `profile_complete = True` AND `report_requested = True` | `rag_retriever` |
| `conversation` | Otherwise | `END` (follow-up question or consultation) |
| `rag_retriever` | Always | `policy` |
| `policy` | Always | `report` |
| `report` | Always | `translate` |
| `translate` | Always | `END` |

### 2.3 State Merging Strategy

LangGraph may return partial state when using `TypedDict` without reducers. The `run_turn()` function manually merges:

```python
merged = dict(original_state)
for key, value in result.items():
    if value is not None:
        merged[key] = value
```

This ensures **no field loss** across turns.

---

## 3. AgentState Schema

The `AgentState` is a `TypedDict` with `total=False` (all fields optional), enabling incremental population across turns.

```
AgentState
├── messages: list[dict]            # Full conversation history [{role, content}]
├── collected: dict[str, Any]       # 15 borrower fields being accumulated
├── missing_fields: list[str]       # Fields still needed
├── profile_complete: bool          # True when all 15 fields present
│
├── is_finance_query: bool          # Guardrail verdict
├── guardrail_reason: str           # Guardrail explanation
│
├── borrower_profile: dict          # Finalized profile (= collected when complete)
├── computed_ratios: dict            # DTI, LTV, EMI, post_loan_DTI
├── ml_risk_score: float            # 0-100 risk score from ML model
├── ml_risk_class: str              # HIGH / MEDIUM / LOW
│
├── rag_chunks: list[dict]          # Retrieved regulatory text chunks
├── citations: list[dict]           # Formatted citation objects
│
├── policy_checks: list[dict]       # 6 policy check results
├── risk_flags: list[str]           # Flags raised by policy engine
├── decision: str                   # APPROVE / CONDITIONAL / ESCALATE
├── decision_score: float           # 0-100 composite score
│
├── report_en: str                  # English credit report (markdown)
├── report_hi: str                  # Hindi credit report (Devanagari)
├── conversation_context: str       # Concatenated user turns for RAG query
├── report_requested: bool          # Whether user asked for report
│
├── assistant_reply: str            # Latest agent response
└── trace: list[str]                # Execution trace log (last 30 entries)
```

---

## 4. Frontend ↔ Backend Communication

### 4.1 Communication Pattern

```
Streamlit (app.py)
   │
   ├── backend_client.py  ──HTTP──▸  api.py (FastAPI)
   │                                    │
   │                                    ├── agent/graph.py → run_turn()
   │                                    ├── services/*     (all services)
   │                                    └── returns JSON {state, assistant_reply, ...}
   │
   └── Renders: chat messages, report panel, PDF buttons
```

### 4.2 API Contract

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/health` | GET | System liveness check |
| `/api/v1/agent/state/initial` | GET | Returns fresh `AgentState` |
| `/api/v1/agent/turn` | POST | Executes one agent turn with user message + state |
| `/api/v1/agent/seed-parameters` | POST | Injects form parameters into state (no graph run) |
| `/api/v1/ingest` | POST | Triggers RAG document ingestion pipeline |

### 4.3 Request/Response Flow

```
POST /api/v1/agent/turn
Request:  { user_message: str, state: AgentState }
Response: {
    assistant_reply: str,
    state: AgentState,          # Full updated state
    report_ready: bool,
    decision: str | null,
    decision_score: float | null,
    citations_count: int,
    retrieved_count: int,
}
```

---

## 5. Data Flow — Complete Pipeline

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│ User Message │────▸│ Guardrail     │────▸│ Safety Check  │
│              │     │ (3 layers)    │     │ Pass / Block  │
└─────────────┘     └───────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                     ┌───────────────────────────────────────────┐
                     │           Conversation Node               │
                     │                                           │
                     │  1. Deterministic regex extraction         │
                     │  2. LLM extraction (llama-3.3-70b)        │
                     │  3. Merge & normalize updates             │
                     │  4. Check missing fields                  │
                     │  5. Build follow-up or consultation reply  │
                     └───────────────────────┬───────────────────┘
                                             │
                              ┌───────────────┴───────────────┐
                              │ profile_complete              │
                              │ + report_requested?           │
                              ├──── NO ──▸ END (ask next Q)   │
                              └──── YES ─────────┐            │
                                                 ▼            │
                     ┌──────────────────────────────────────┐  │
                     │         RAG Retriever Node           │  │
                     │                                      │  │
                     │  1. Build rich query from profile     │  │
                     │  2. Encode with all-MiniLM-L6-v2     │  │
                     │  3. Query ChromaDB (top_k=8)         │  │
                     │  4. Return chunks + citations         │  │
                     └────────────────┬─────────────────────┘  │
                                      ▼                        │
                     ┌──────────────────────────────────────┐  │
                     │           Policy Node                │  │
                     │                                      │  │
                     │  1. ML risk scoring (model or heur.) │  │
                     │  2. 6 policy cutoff checks           │  │
                     │  3. Score: 100 base, -18/FAIL, -10/W │  │
                     │  4. Decision banding                 │  │
                     └────────────────┬─────────────────────┘  │
                                      ▼                        │
                     ┌──────────────────────────────────────┐  │
                     │          Report Node                 │  │
                     │                                      │  │
                     │  1. Attempt LLM report (Groq)        │  │
                     │  2. Validate consistency with profile │  │
                     │  3. Fallback to deterministic report  │  │
                     └────────────────┬─────────────────────┘  │
                                      ▼                        │
                     ┌──────────────────────────────────────┐  │
                     │         Translate Node               │  │
                     │                                      │  │
                     │  1. Attempt LLM Hindi translation     │  │
                     │  2. Validate Devanagari presence      │  │
                     │  3. Fallback to deterministic mapping │  │
                     └──────────────────────────────────────┘
```

---

## 6. Deployment Topology

### Local Development

```
Terminal 1:  uvicorn api:app --host 0.0.0.0 --port 8010
Terminal 2:  streamlit run app.py --server.port 8502
```

### Production (Planned)

| Component | Platform | Config |
|---|---|---|
| **Backend + ChromaDB** | Render | `render.yaml` blueprint; Chroma as co-located service |
| **Frontend** | Streamlit Community Cloud | `secrets.toml` for API keys |

---

## 7. Security & Configuration

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `GROQ_KEY_1` through `GROQ_KEY_5` | Groq API keys (round-robin pool) | — |
| `GROQ_API_KEY` | Alternative single key | — |
| `CHROMA_PATH` | ChromaDB persistence directory | `./chroma_store` |
| `COLLECTION_NAME` | ChromaDB collection name | `creditsense_docs` |
| `RAG_DOCS_PATH` | Source directory for regulatory docs | `../../RAG files` or `./rag_docs` |
| `RAG_TOP_K` | Number of chunks to retrieve | `8` |
| `DEFAULT_ANNUAL_INTEREST_RATE` | Interest rate for EMI calculations | `0.15` (15%) |
| `ML_MODEL_PATH` | Path to M1 model pickle | `./ml_model/model.pkl` |
| `ML_MODEL_FALLBACK_PATH` | Fallback M1 model path | `../../MILESTONE 1/models/logistic_regression.pkl` |
| `HINDI_FONT_PATH` | Noto Sans Devanagari TTF | `./assets/fonts/NotoSansDevanagari-Regular.ttf` |
| `BACKEND_API_BASE_URL` | Backend URL for Streamlit client | `http://localhost:8010` |
| `BACKEND_CORS_ORIGINS` | CORS allowed origins | localhost ports 8501-8505, 3000 |

---

*CreditSense v2.0 — Architecture Documentation | Last Updated: April 2026*
