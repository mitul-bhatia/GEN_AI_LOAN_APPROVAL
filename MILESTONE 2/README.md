# Milestone 2: NBFC Regulatory RAG

## New Build (CreditSense v2)

A fresh implementation based on the Streamlit + LangGraph + Chroma PRD is now available in:

- `creditsense/`

Run it with:

- `cd creditsense`
- `pip install -r requirements.txt`
- `python scripts/ingest.py --source-dir ./rag_docs` (or point to `../RAG files`)
- `streamlit run app.py`

This preserves the older notes below for reference, while making the new runnable path explicit.

This folder contains the independent Milestone 2 implementation for the NBFC regulatory retrieval and reasoning system.

Milestone 1 remains unchanged in `../MILESTONE 1`.

## Stack

- Backend: FastAPI
- Frontend: React (Vite)
- Vector DB: ChromaDB
- Deployment: Render (backend + Chroma), Vercel (frontend)

## Current Focus

- Workspace-first flow only: borrower input -> computed ratios -> light-RAG evidence -> knowledge graph.
- UI intentionally hides ingest and architecture controls while this phase is stabilized.
- Active corpus for this phase: 57 usable files from `RAG files/`.

## Folder Map

- `backend/`: API and orchestration services
- `frontend/`: workspace-first React user interface
- `infra/`: Render blueprint and Chroma service requirements

## Local Run

1. Copy env templates.

- `cp backend/.env.example backend/.env`
- `cp frontend/.env.example frontend/.env`

1. Start Chroma in terminal 1.

- `cd backend`
- `source .venv/bin/activate` (or create one: `python3 -m venv .venv`)
- `pip install -r requirements.txt`
- `chroma run --host 0.0.0.0 --port 8001 --path ../storage/chroma`

1. Start backend in terminal 2.

- `cd backend`
- `source .venv/bin/activate`
- `uvicorn app.main:app --host 0.0.0.0 --port 8000`

1. Start frontend in terminal 3.

- `cd frontend`
- `npm install`
- `npm run dev`

1. Open services.

- Frontend: <http://localhost:5173>
- Backend: <http://localhost:8000>
- Health: <http://localhost:8000/api/v1/health>

## API Endpoints

- `GET /api/v1/health`
- `GET /api/v1/documents?priority=P0`
- `POST /api/v1/query`
- `GET /api/v1/knowledge-graph/latest`
- `GET /api/v1/knowledge-graph/{trace_id}`

Sample query payload:

{
  "question": "Should this borrower be approved for an NBFC business loan?",
  "mode": "mixed",
  "borrower_profile": {
    "name": "Amit Sharma",
    "age": 32,
    "city": "Pune",
    "monthly_income": 120000,
    "employment_type": "Salaried",
    "employment_years": 4,
    "credit_score": 742,
    "existing_loan_count": 1,
    "existing_emi_monthly": 18000,
    "payment_history": "Clean",
    "loan_amount_requested": 650000,
    "loan_purpose": "Business",
    "loan_tenure_months": 60,
    "collateral_type": "Property",
    "collateral_value": 1000000
  }
}

## Deploy Plan

### Backend and Chroma on Render

- Use `infra/render.yaml` blueprint.
- Chroma runs as private service (native Python runtime) with persistent disk mounted at `/data/chroma`.
- Backend connects to Chroma over Render internal network.

### Frontend on Vercel

- Set root to `MILESTONE 2/frontend`.
- Set env var `VITE_API_BASE_URL` to Render backend URL.

## Completion Status (April 16, 2026)

- Milestone 2 functional scope is complete for borrower-profile-driven decisioning.
- End-to-end validation is green for ingest, query, guardrail, and graph retrieval flows.
- Active corpus in current workspace is 57 usable files (excluding `.DS_Store`).
- Chroma collection `nbfc_regulatory_docs` is fully populated from this corpus.

Latest validation snapshot:

- Health: `200` (`api=ok`, `chroma=ok`)
- Ingest: `total=57`, `indexed=57`, `failed=0`, `chunks=8452`
- Chroma coverage: `8452` chunks, `57` unique `source_file` entries
- Query: `decision=approve`, `score=90.0`, `retrieved_count=8`, P0-P4 covered
- Guardrail: out-of-scope prompt blocked with `decision=escalate`
- Graph APIs: both `/knowledge-graph/{trace_id}` and `/knowledge-graph/latest` return `200`

## Optional Enhancements

- Increase use of Groq reasoning for deeper narrative responses.
- Add a stricter citation auditor for policy-check-to-evidence alignment checks.
- Add an automated regression suite for grounding and fairness consistency.

## What Has Been Implemented

- Created an isolated Milestone 2 codebase under this folder.
- Added FastAPI backend with three initial endpoints (`health`, `documents`, `query`).
- Added retrieval/orchestrator service skeleton with P0+P4 baseline policy.
- Added Chroma connectivity and fallback behavior when vector data is not ingested yet.
- Added complete ingestion pipeline from raw RAG files to Chroma with file-level telemetry.
- Added Groq key-pool utility skeleton for multi-key rotation.
- Added exact borrower-profile-driven decisioning flow (profile -> computed ratios -> cutoff checks -> decision score).
- Added P0-P4 complete-coverage retrieval strategy with explicit coverage reporting.
- Added guardrail-first evaluator to block out-of-scope/unsafe prompts before decision execution.
- Added persistent knowledge graph store (SQLite) plus API retrieval by trace id/latest.
- Added knowledge graph extraction payload in backend and rendered graph visualization in workspace UI.
- Added React frontend in workspace-first mode for borrower input, light-RAG output, and graph visualization.
- Added Render blueprint and Vercel config for deployable topology without Docker.
- Added explanatory comments in editable source/config files.

## GenAI Status (Current Reality)

- RAG retrieval pipeline: **implemented with decisioning traceability**.
  - Query routing works.
  - Chroma retrieval path works.
  - Priority-balanced retrieval enforces visible P0-P4 evidence coverage.
  - Fallback retrieval works when collection is empty or sparse.
- Guardrail-first pipeline: **implemented**.
  - Query is evaluated first for domain/safety constraints.
  - Non-loan or unsafe prompts are blocked before underwriting reasoning.
- Ingestion pipeline: **implemented**.
  - Maps noisy file names to canonical docs.
  - Extracts text from PDF and text-like files (`txt`, `json`, `csv`, `html`, `docx`) with binary-safe fallback.
  - Chunks and upserts to Chroma.
  - Supports priority filter, reset, dry-run, max files.
- Light-RAG retrieval path: **implemented**.
  - Priority-seeded retrieval guarantees representation across P0-P4 when evidence exists.
  - Global top-k fill from Chroma adds best additional evidence.
  - Retrieval snippets are cleaned before UI/API response output.
- Knowledge graph: **implemented with persistent graph store**.
  - Backend returns nodes and edges linking query, route, decision, policy checks, priorities, and citations.
  - Graph is persisted to SQLite and retrievable via API by trace id.
  - Frontend renders graph visualization for end-user auditability.
- LLM reasoning with Groq: **partially scaffolded**.
  - Key pool exists.
  - Full Groq-driven node prompts and citation auditor logic are next steps.

## File-By-File Comment Guide

### Backend

- `backend/app/main.py`: API bootstrap, CORS setup, route registration, and root status endpoint.
- `backend/app/config.py`: environment-driven settings for app, Chroma, CORS, and Groq keys.
- `backend/app/models.py`: request/response schemas used by FastAPI contracts.
- `backend/app/routes/health.py`: backend + Chroma health projection endpoint.
- `backend/app/routes/documents.py`: curated regulatory document listing endpoint.
- `backend/app/routes/query.py`: query endpoint that triggers orchestrator pipeline.
- `backend/app/routes/ingest.py`: ingestion endpoint for indexing corpus into Chroma.
- `backend/app/routes/knowledge_graph.py`: graph retrieval endpoints (`latest` and `trace_id`).
- `backend/app/services/chroma_client.py`: Chroma client factory, collection access, health check.
- `backend/app/services/document_registry.py`: canonical 14-document metadata registry.
- `backend/app/services/retriever.py`: Chroma retrieval + P0-P4 coverage backfill strategy.
- `backend/app/services/orchestrator.py`: routing, parameterized policy checks, decision scoring, and knowledge graph construction.
- `backend/app/services/groq_pool.py`: round-robin key selection helper for Groq API keys.
- `backend/app/services/guardrail.py`: guardrail-first request evaluator (LLM-first with deterministic fallback).
- `backend/app/services/borrower_metrics.py`: borrower metric computation (EMI, DTI, LTV, post-loan DTI) and synthetic profile generation.
- `backend/app/services/ml_adapter.py`: M1 signal adapter and fallback risk estimation.
- `backend/app/services/policy_engine.py`: exact cutoff policy interpretation and decision banding.
- `backend/app/services/knowledge_graph_store.py`: SQLite-based graph persistence and retrieval helpers.
- `backend/app/services/ingestion_registry.py`: filename alias matcher to canonical docs.
- `backend/app/services/ingestion_io.py`: raw file discovery and text extraction.
- `backend/app/services/ingestion_chunker.py`: overlapping chunk generation policy.
- `backend/app/services/ingestion_pipeline.py`: full ingest orchestration and Chroma upsert path.
- `backend/app/services/ingestion_readme_notes.py`: inline module-level guide for contributors.
- `backend/requirements.txt`: backend dependency manifest.
- `backend/.env.example`: backend environment template values.

### Frontend

- `frontend/src/main.jsx`: React root bootstrap with router wrapper.
- `frontend/src/App.jsx`: app shell and page route registration.
- `frontend/src/components/NavBar.jsx`: shared navigation with active route highlighting.
- `frontend/src/pages/OverviewPage.jsx`: milestone summary and capability cards.
- `frontend/src/pages/ArchitecturePage.jsx`: local/deploy architecture and Chroma placement explanation.
- `frontend/src/pages/WorkspacePage.jsx`: borrower parameter form, API call, decision analytics, and knowledge graph rendering.
- `frontend/src/styles.css`: theme, layout, cards, form styling, and responsive behavior.
- `frontend/index.html`: HTML shell with root mount point and font loading.
- `frontend/vite.config.js`: Vite dev server configuration.
- `frontend/.env.example`: frontend API base URL template.
- `frontend/package.json`: frontend dependency + script manifest.
- `frontend/vercel.json`: Vercel build output configuration.

### Infrastructure

- `infra/render.yaml`: Render blueprint for backend + private Chroma with disk (native runtime).
- `infra/chroma-requirements.txt`: dependencies for Chroma private service on Render.

### Product Docs

- `../docs/prd.md`: updated milestone PRD with local and deployable architecture.

## Note About Comments

Some files such as JSON (`package.json`, `vercel.json`) cannot contain inline comments by language syntax. For those files, this guide acts as the file-level explanation block.
