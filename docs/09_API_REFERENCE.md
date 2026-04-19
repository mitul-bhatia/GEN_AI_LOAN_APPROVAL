# CreditSense — API Reference

> **Complete REST API specification for the FastAPI backend**

---

## 1. Base URL

| Environment | URL |
|---|---|
| **Local Development** | `http://localhost:8010` |
| **Production (Render)** | `https://your-backend.onrender.com` |

---

## 2. Endpoints

### 2.1 Health Check

```
GET /api/v1/health
```

**Purpose:** System liveness and dependency reachability check.

**Response:**

```json
{
  "status": "ok",
  "service": "CreditSense Backend API",
  "chroma_path": "./chroma_store",
  "collection": "creditsense_docs"
}
```

---

### 2.2 Initial Agent State

```
GET /api/v1/agent/state/initial
```

**Purpose:** Returns a fresh empty `AgentState` to start a new conversation.

**Response:**

```json
{
  "state": {
    "messages": [],
    "collected": {
      "name": "", "age": null, "city": "", "employment_type": "",
      "monthly_income": null, "employment_years": null,
      "credit_score": null, "existing_loan_count": null,
      "existing_emi_monthly": null, "payment_history": "",
      "loan_amount_requested": null, "loan_purpose": "",
      "loan_tenure_months": null, "collateral_type": "",
      "collateral_value": null
    },
    "missing_fields": ["name", "age", "employment_type", ...],
    "profile_complete": false,
    "is_finance_query": true,
    "guardrail_reason": "",
    "borrower_profile": {},
    "computed_ratios": {},
    "ml_risk_score": 0.0,
    "ml_risk_class": "",
    "rag_chunks": [],
    "citations": [],
    "policy_checks": [],
    "risk_flags": [],
    "decision": "",
    "decision_score": 0.0,
    "report_en": "",
    "report_hi": "",
    "conversation_context": "",
    "report_requested": false,
    "assistant_reply": "",
    "trace": []
  }
}
```

---

### 2.3 Agent Turn

```
POST /api/v1/agent/turn
```

**Purpose:** Execute one full LangGraph agent turn with a user message.

**Request Body:**

```json
{
  "user_message": "Rajesh Kumar age 45 from Mumbai, salaried, monthly income Rs 60000",
  "state": { ... }  // Current AgentState (optional — defaults to initial state)
}
```

**Response:**

```json
{
  "assistant_reply": "I have noted your name, age, and city. Next, please share your employment type, employment years, and monthly income.",
  "state": { ... },           // Full updated AgentState
  "report_ready": false,      // Whether report_en is populated
  "decision": null,           // APPROVE / CONDITIONAL / ESCALATE (if report generated)
  "decision_score": null,     // 0-100 (if report generated)
  "citations_count": 0,       // Number of RAG citations
  "retrieved_count": 0        // Number of retrieved chunks
}
```

**Error Response (500):**

```json
{
  "detail": "Agent execution failed: <error message>"
}
```

---

### 2.4 Seed Parameters

```
POST /api/v1/agent/seed-parameters
```

**Purpose:** Inject structured form parameters into agent state without running the full graph. Used by the Streamlit parameter form.

**Request Body:**

```json
{
  "parameters": {
    "name": "Rajesh Kumar",
    "age": 45,
    "city": "Mumbai",
    "employment_type": "Salaried",
    "monthly_income": 60000,
    "credit_score": 720,
    "existing_loan_count": 1,
    "existing_emi_monthly": 8000,
    "payment_history": "Clean",
    "loan_amount_requested": 500000,
    "loan_purpose": "Personal",
    "loan_tenure_months": 36,
    "collateral_type": "None",
    "collateral_value": 0
  },
  "state": { ... }  // Current AgentState (optional)
}
```

**Response:**

```json
{
  "assistant_reply": "Parameters saved. Borrower profile is complete. You can ask me to generate the report now.",
  "state": { ... },
  "profile_complete": true,
  "missing_fields": [],
  "applied_fields": ["name", "age", "city", "employment_type", ...]
}
```

**Parameter Normalization Rules:**

| Field Type | Normalization |
|---|---|
| Integer fields (`age`, `credit_score`, `existing_loan_count`, `loan_tenure_months`) | `int(float(value))` |
| Float fields (`monthly_income`, `employment_years`, `existing_emi_monthly`, `loan_amount_requested`, `collateral_value`) | `float(value)` |
| String fields | `str(value).strip()` |
| Collateral type = "None" | Automatically sets `collateral_value = 0.0` |
| Existing loan count = 0 | Automatically sets `existing_emi_monthly = 0.0` |

---

### 2.5 Ingest Documents

```
POST /api/v1/ingest
```

**Purpose:** Trigger regulatory document ingestion into ChromaDB.

**Request Body:**

```json
{
  "source_dir": "../../RAG files",       // Optional — defaults to settings
  "chroma_path": "./chroma_store",       // Optional
  "collection": "creditsense_docs",      // Optional
  "chunk_size": 1200,                    // Optional
  "overlap": 150,                        // Optional
  "embedding_model": "all-MiniLM-L6-v2"  // Optional
}
```

**Response:**

```json
{
  "status": "ok",
  "source_dir": "/absolute/path/to/RAG files",
  "chroma_path": "/absolute/path/to/chroma_store",
  "collection": "creditsense_docs"
}
```

**Error Response:**

```json
{
  "detail": "Source directory does not exist: /path/to/dir"
}
```

---

## 3. CORS Configuration

Default allowed origins:
```
http://localhost:8501
http://localhost:8502
http://localhost:8503
http://localhost:8504
http://localhost:8505
http://localhost:3000
```

Override via `BACKEND_CORS_ORIGINS` environment variable (comma-separated).

---

## 4. Testing with cURL

### Health Check

```bash
curl http://localhost:8010/api/v1/health
```

### Start Conversation

```bash
curl -X POST http://localhost:8010/api/v1/agent/turn \
  -H "Content-Type: application/json" \
  -d '{"user_message": "Rajesh Kumar age 45 from Mumbai, salaried for 6 years, monthly income 60000"}'
```

### Seed Parameters

```bash
curl -X POST http://localhost:8010/api/v1/agent/seed-parameters \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "name": "Rajesh Kumar",
      "age": 45,
      "city": "Mumbai",
      "employment_type": "Salaried",
      "monthly_income": 60000
    }
  }'
```

### Trigger Ingestion

```bash
curl -X POST http://localhost:8010/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_dir": "../../RAG files"}'
```

---

*CreditSense v2.0 — API Reference | Last Updated: April 2026*
