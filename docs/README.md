# CreditSense Milestone 2 Documentation

> Refreshed from current code scan on 2026-04-19.

This folder is the Milestone 2 submission documentation pack for CreditSense.
It is written as an "as-built" reference based on the current code in:

- `MILESTONE_2/creditsense/`

Use these docs as the single source for:

- project understanding
- viva and demo prep
- PPT creation
- final written report
- implementation handoff

## Document Index

| File | What It Covers |
| --- | --- |
| `01_PROJECT_OVERVIEW.md` | Problem, solution, implemented scope, and milestone summary |
| `02_ARCHITECTURE.md` | End-to-end architecture, data flow, state flow, and routing |
| `03_AGENT_NODES_AND_SERVICES.md` | All LangGraph nodes and all service modules |
| `04_RAG_PIPELINE.md` | Ingestion, chunking, embeddings, Chroma storage, retrieval |
| `05_CODEBASE_FILE_MAP.md` | File-by-file map of Milestone 2 codebase |
| `06_MODEL_AND_ML.md` | ML adapter, heuristic fallback, policy scoring, LLM model usage |
| `07_GAPS_AND_FUTURE_WORK.md` | Current limitations, technical debt, and roadmap |
| `08_SETUP_AND_DEPLOYMENT.md` | Exact run commands, env setup, validation, deployment notes |
| `09_API_REFERENCE.md` | FastAPI endpoint contracts and request/response examples |
| `CREDITSENSE_V2_PRD.md` | Milestone 2 PRD (as-built + requirement traceability) |
| `CreditSense_M2_Professional_Report.tex` | Full professional LaTeX report for final submission and viva |
| `CreditSense_M2_Professional_Report.pdf` | Compiled submission-ready PDF of the professional report |
| `diagrams/README.md` | Mermaid diagram pack and export instructions for upload-ready images |
| `MILESTONE2_MASTER_DOCS_PROMPT.md` | Detailed master prompt for exhaustive, code-grounded docs regeneration |

## Milestone 2 At A Glance

| Topic | Current Implementation |
| --- | --- |
| Frontend | Streamlit app (`app.py`) |
| Backend | FastAPI (`api.py`) |
| Agent Orchestration | LangGraph StateGraph with 6 nodes |
| Retrieval | ChromaDB persistent store + MiniLM embeddings |
| Required Intake Fields | 15 borrower fields |
| Decision Output | `APPROVE`, `CONDITIONAL`, `ESCALATE` |
| Report Output | English + Hindi report, both downloadable as PDF |
| Scripted Runtime | `scripts/run_backend.sh`, `scripts/run_streamlit.sh` |
| Ingestion | `scripts/ingest.py` |
| Scenario Validation | `scripts/e2e_scenarios.py` |
| Deploy Manifests | `Procfile`, `render.yaml`, `runtime.txt` |

## Fastest Local Start

From `MILESTONE_2/creditsense`:

```bash
bash scripts/run_backend.sh
```

In a second terminal:

```bash
bash scripts/run_streamlit.sh
```

Optional one-time ingestion:

```bash
python3 scripts/ingest.py --source-dir "../../RAG files"
```

## Suggested Reading Order

1. `01_PROJECT_OVERVIEW.md`
2. `02_ARCHITECTURE.md`
3. `03_AGENT_NODES_AND_SERVICES.md`
4. `04_RAG_PIPELINE.md`
5. `06_MODEL_AND_ML.md`
6. `08_SETUP_AND_DEPLOYMENT.md`
7. `09_API_REFERENCE.md`
8. `07_GAPS_AND_FUTURE_WORK.md`

## PPT / Report Shortcut

If you only need material for presentation quickly, use this order:

1. `01_PROJECT_OVERVIEW.md` for narrative and business framing
2. `02_ARCHITECTURE.md` for diagrams and component flow
3. `04_RAG_PIPELINE.md` for GenAI/RAG methodology
4. `06_MODEL_AND_ML.md` for scoring logic and model story
5. `07_GAPS_AND_FUTURE_WORK.md` for honest evaluation and future scope

## Viva Upload Assets (Image Requirement)

For form fields like "Project Architecture Diagram (Upload image)":

1. Use Mermaid source: `diagrams/system-architecture.mmd`
2. Export PNG using instructions in `diagrams/README.md`
3. Upload the generated image from `diagrams/exports/system-architecture.png` (keep file size under your portal limit)
