# CreditSense — Documentation Index

> **📚 Complete documentation suite for the CreditSense AI-Powered Loan Underwriting Agent**

---

## Documentation Map

| # | Document | Description | Audience |
|---|---|---|---|
| **01** | [Project Overview](./01_PROJECT_OVERVIEW.md) | Problem statement, solution summary, milestone progression, tech stack, key differentiators | Everyone |
| **02** | [Architecture](./02_ARCHITECTURE.md) | High-level system diagram, LangGraph pipeline, AgentState schema, data flow, deployment topology | Developers, Evaluators |
| **03** | [Agent Nodes & Services](./03_AGENT_NODES_AND_SERVICES.md) | Deep-dive into all 6 LangGraph nodes, guardrail layers, policy engine, scoring logic | Developers |
| **04** | [RAG Pipeline](./04_RAG_PIPELINE.md) | Document ingestion, chunking, embedding, ChromaDB storage, retrieval architecture | Developers, Evaluators |
| **05** | [Codebase File Map](./05_CODEBASE_FILE_MAP.md) | Complete file inventory with purpose, dependencies, line counts, dependency graph | Developers |
| **06** | [Model & ML](./06_MODEL_AND_ML.md) | ML model documentation, LLM assignments, heuristic scoring, embedding model, combined scoring flow | Developers, Evaluators |
| **07** | [Gaps & Future Work](./07_GAPS_AND_FUTURE_WORK.md) | Known limitations, technical debt, PRD vs. implementation comparison, improvement roadmap | Evaluators, Project Leads |
| **08** | [Setup & Deployment](./08_SETUP_AND_DEPLOYMENT.md) | Local development setup, environment config, troubleshooting, production deployment guide | Developers |
| **09** | [API Reference](./09_API_REFERENCE.md) | REST API specification — all endpoints, request/response schemas, cURL examples | Developers |
| **—** | [Product Requirements (PRD)](./CREDITSENSE_V2_PRD.md) | Original v2.0 product requirements document — user journey, build plan, rubric alignment | Project Leads, Evaluators |

---

## Quick Navigation

### 🎯 "What does this project do?"
→ Start with [01 — Project Overview](./01_PROJECT_OVERVIEW.md)

### 🏗️ "How is it architected?"
→ Read [02 — Architecture](./02_ARCHITECTURE.md) and [03 — Agent Nodes](./03_AGENT_NODES_AND_SERVICES.md)

### 🤖 "How does the AI/ML work?"
→ Read [06 — Model & ML](./06_MODEL_AND_ML.md) and [04 — RAG Pipeline](./04_RAG_PIPELINE.md)

### 💻 "How do I run it?"
→ Follow [08 — Setup & Deployment](./08_SETUP_AND_DEPLOYMENT.md)

### 🔌 "What APIs are available?"
→ Check [09 — API Reference](./09_API_REFERENCE.md)

### ⚠️ "What are the limitations?"
→ Read [07 — Gaps & Future Work](./07_GAPS_AND_FUTURE_WORK.md)

### 📂 "What file does what?"
→ Browse [05 — Codebase File Map](./05_CODEBASE_FILE_MAP.md)

---

## Project Stats

| Metric | Value |
|---|---|
| **Total Source Files** | 23 |
| **Total Lines of Code** | ~3,845 |
| **LangGraph Nodes** | 6 |
| **Services** | 13 |
| **RAG Documents** | 57 |
| **RAG Chunks** | 8,452 |
| **API Endpoints** | 5 |
| **LLM Models Used** | 2 (llama-3.1-8b, llama-3.3-70b) |
| **Output Languages** | 2 (English, Hindi) |
| **Policy Checks** | 6 |
| **Test Scenarios** | 5 |

---

## Repository Structure

```
JAIN_AI/
├── MILESTONE 1/          # Classical ML pipeline (data, models, notebooks)
├── MILESTONE 2/          # Agentic AI + RAG system
│   └── creditsense/      # Main application
│       ├── agent/        # LangGraph orchestrator
│       ├── services/     # Business logic services
│       ├── scripts/      # Ingestion + testing
│       ├── app.py        # Streamlit frontend
│       ├── api.py        # FastAPI backend
│       └── ...
├── RAG files/            # 57 RBI regulatory documents
└── docs/                 # 📍 You are here
    ├── README.md                    # This index
    ├── 01_PROJECT_OVERVIEW.md
    ├── 02_ARCHITECTURE.md
    ├── 03_AGENT_NODES_AND_SERVICES.md
    ├── 04_RAG_PIPELINE.md
    ├── 05_CODEBASE_FILE_MAP.md
    ├── 06_MODEL_AND_ML.md
    ├── 07_GAPS_AND_FUTURE_WORK.md
    ├── 08_SETUP_AND_DEPLOYMENT.md
    ├── 09_API_REFERENCE.md
    └── CREDITSENSE_V2_PRD.md
```

---

*CreditSense v2.0 Documentation Suite | Generated: April 2026*
