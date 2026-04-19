# CreditSense Milestone 2 Project Overview

> Refreshed from current code scan on 2026-04-19.

## 1. Project Context

CreditSense is an AI-assisted credit risk assessment system for NBFC-style loan underwriting workflows.

Milestone 1 delivered classic ML groundwork.
Milestone 2 delivers the conversational, retrieval-grounded, report-generating agentic system.

Milestone 2 codebase used for this documentation:

- `MILESTONE 2/creditsense/`

## 2. Problem Statement

Loan decisioning teams face repeated operational pain points:

1. Borrower intake data is often incomplete and gathered manually.
2. Regulatory context is scattered across many RBI/NBFC documents.
3. Decision explanations are inconsistent and hard to audit.
4. Teams need both technical and business-readable output.
5. Hindi output is often required for wider stakeholder communication.

## 3. Milestone 2 Solution Summary

Milestone 2 implements an end-to-end conversational pipeline:

1. User submits borrower details through sidebar form and/or chat.
2. Agent guardrails validate domain and safety.
3. Parser builds a structured borrower profile over turns.
4. Financial ratios are computed.
5. RAG retrieves relevant regulatory chunks from Chroma.
6. Policy checks and ML-based risk scoring are executed.
7. A structured report is generated in English.
8. Hindi translation is generated.
9. English and Hindi PDFs are downloadable.

## 4. What Is Implemented In Milestone 2

### 4.1 Application Layers

- Streamlit frontend: `app.py`
- FastAPI backend: `api.py`
- LangGraph orchestrator: `agent/graph.py`
- Node logic: `agent/nodes.py`
- Service layer: `services/*.py`
- Ingestion and runtime scripts: `scripts/*.py`
- Deployment manifests: `Procfile`, `render.yaml`, `runtime.txt`

### 4.2 Core Features

- Multi-turn borrower intake with 15 required fields
- Guardrail pipeline for unsafe or out-of-domain prompts
- RAG retrieval from ChromaDB using sentence-transformer embeddings
- Deterministic policy checks with cutoff thresholds
- ML risk score adapter with heuristic fallback
- English report generation (LLM-first with deterministic fallback)
- Hindi translation (LLM-first with deterministic fallback)
- PDF export for both languages

### 4.3 API Surface

Implemented FastAPI endpoints:

- `GET /api/v1/health`
- `GET /api/v1/agent/state/initial`
- `POST /api/v1/agent/turn`
- `POST /api/v1/agent/seed-parameters`
- `POST /api/v1/ingest`

## 5. Milestone 1 vs Milestone 2

| Dimension | Milestone 1 | Milestone 2 |
|---|---|---|
| Primary Mode | Classical ML workflow | Conversational AI agent workflow |
| User Interaction | Static forms/notebooks | Chat + dynamic intake + report generation |
| Retrieval | Not central | Chroma-based RAG |
| Orchestration | Script-level flow | LangGraph node graph |
| Output | Model predictions | Full decision report + citations + translation + PDF |

## 6. Target Use Cases

1. Rapid borrower pre-screening
2. Assistant support for loan officers
3. Explainable risk narratives for stakeholder review
4. RBI/NBFC regulation-aware advisory responses
5. Bilingual report generation (English/Hindi)

## 7. End-to-End User Flow (Implemented)

1. Start backend + Streamlit app
2. Save borrower data from sidebar
3. Ask underwriting-related questions in chat
4. Ask to "generate report"
5. Agent performs retrieval + policy + report generation
6. Read report in app
7. Download English and Hindi PDFs

## 8. Key Technical Stack

- Python
- Streamlit
- FastAPI + Uvicorn
- LangGraph
- ChromaDB
- Sentence Transformers (`all-MiniLM-L6-v2`)
- Groq-hosted Llama models
- scikit-learn/joblib model adapter
- fpdf2 for PDF generation

## 9. Deliverables Produced By Milestone 2

1. Runnable frontend and backend
2. Agentic graph orchestration
3. Retrieval and ingestion pipeline
4. Underwriting policy engine
5. Bilingual structured report generation
6. API contracts for integration
7. Reusable scripts for runtime and testing
8. Full documentation set (this folder)

## 10. What This Documentation Is Intended For

This docs set is written to be enough for:

- PPT creation without reading code deeply
- final written report drafting
- viva defense and architectural explanation
- implementation walkthrough and handover
