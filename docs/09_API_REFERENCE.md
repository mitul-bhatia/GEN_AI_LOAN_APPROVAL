# CreditSense API Reference

> Refreshed from current code scan on 2026-04-19.

## 1. Service

- Framework: FastAPI
- Entry file: `MILESTONE_2/creditsense/api.py`
- Local base URL: `http://localhost:8010`
- Environment bootstrap: `.env` is loaded via `python-dotenv` during API startup

## 2. Endpoint Summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | health and runtime metadata |
| GET | `/api/v1/agent/state/initial` | fresh initial agent state |
| POST | `/api/v1/agent/turn` | run one conversational graph turn |
| POST | `/api/v1/agent/seed-parameters` | inject form fields into state |
| POST | `/api/v1/ingest` | trigger corpus ingestion into Chroma |

## 3. Schemas

## 3.1 AgentTurnRequest

```json
{
  "user_message": "string (required)",
  "state": { "optional": "AgentState object" }
}
```

## 3.2 SeedParametersRequest

```json
{
  "parameters": {
    "name": "Rahul Sharma",
    "age": 32,
    "city": "Pune",
    "employment_type": "Salaried",
    "employment_years": 4,
    "monthly_income": 120000,
    "credit_score": 742,
    "existing_loan_count": 1,
    "existing_emi_monthly": 18000,
    "payment_history": "Clean",
    "loan_amount_requested": 650000,
    "loan_purpose": "Business",
    "loan_tenure_months": 60,
    "collateral_type": "Property",
    "collateral_value": 1000000
  },
  "state": { "optional": "AgentState object" }
}
```

## 3.3 IngestRequest

```json
{
  "source_dir": "optional string",
  "chroma_path": "optional string",
  "collection": "optional string",
  "chunk_size": 1200,
  "overlap": 150,
  "embedding_model": "all-MiniLM-L6-v2"
}
```

Note: `embedding_model` is currently retained for request compatibility; ingestion implementation uses Chroma's ONNX MiniLM embedding utility.

## 4. Endpoint Details

## 4.1 GET /api/v1/health

Returns service status plus configured Chroma path and collection.

Example response:

```json
{
  "status": "ok",
  "service": "CreditSense Backend API",
  "chroma_path": "./chroma_store",
  "collection": "creditsense_docs"
}
```

## 4.2 GET /api/v1/agent/state/initial

Returns a new empty state from `make_initial_state()`.

Useful when starting a fresh chat session from external clients.

## 4.3 POST /api/v1/agent/turn

Runs one complete graph turn.

Behavior summary:

1. backend appends incoming user message into `state.messages`
2. invokes `run_turn(state)` from graph
3. if assistant reply exists, appends assistant message to history
4. returns updated state and summary counters

Example request:

```bash
curl -X POST http://localhost:8010/api/v1/agent/turn \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Can you assess whether I am eligible for a business loan?"
  }'
```

Response fields:

- `assistant_reply`
- `state`
- `report_ready`
- `decision`
- `decision_score`
- `citations_count`
- `retrieved_count`

## 4.4 POST /api/v1/agent/seed-parameters

Used by frontend sidebar to inject structured borrower fields quickly.

Normalization behavior implemented by backend:

1. int fields converted via `int(float(value))`
2. float fields converted via `float(value)`
3. blank/invalid values skipped
4. if `collateral_type` is `none` then `collateral_value` forced to `0.0`
5. if `existing_loan_count == 0` and EMI missing, EMI forced to `0.0`

Returns:

- `assistant_reply`
- `state`
- `profile_complete`
- `missing_fields`
- `applied_fields`

## 4.5 POST /api/v1/ingest

Triggers script ingestion in-process.

Example request:

```bash
curl -X POST http://localhost:8010/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_dir": "../../RAG files",
    "chunk_size": 1200,
    "overlap": 150
  }'
```

Example success response:

```json
{
  "status": "ok",
  "source_dir": "...",
  "chroma_path": "...",
  "collection": "creditsense_docs"
}
```

## 5. Error Behavior

1. invalid or missing source directory for ingestion -> HTTP 400
2. graph execution failure -> HTTP 500 with `Agent execution failed: ...`
3. ingestion failure -> HTTP 500 with `Ingestion failed: ...`

## 6. CORS

CORS origins are controlled by `BACKEND_CORS_ORIGINS` env, defaulting to common local frontend ports.

## 7. Integration Notes

1. if no state is sent to turn/seed endpoints, backend starts from initial state
2. clients should persist and send `state` between turns for continuity
3. recommended client timeout for `/agent/turn` should allow longer report generation turns
