# CreditSense — Project Overview

> **AI-Powered NBFC Loan Underwriting & Regulatory Compliance Agent**

---

## 1. Project Identity

| Field | Detail |
|---|---|
| **Project Name** | CreditSense |
| **Current Version** | v2.0 (Milestone 2 — Clean Rebuild) |
| **Domain** | FinTech / Regulatory Technology (RegTech) |
| **Target Users** | Loan Officers, NBFC Underwriters, Credit Risk Analysts |
| **Academic Context** | End-Semester AI/ML Project — Jain University |
| **Repository Structure** | Multi-milestone monorepo (`MILESTONE 1/`, `MILESTONE 2/`, `RAG files/`, `docs/`) |

---

## 2. Problem Statement

Non-Banking Financial Companies (NBFCs) in India operate under a complex and evolving regulatory framework issued by the Reserve Bank of India (RBI). Loan underwriting decisions require:

1. **Manual cross-referencing** of 50+ regulatory circulars, master directions, and prudential norms
2. **Subjective judgment** on borrower risk profiles with inconsistent application of policy cutoffs
3. **No audit trail** linking decisions back to specific regulations
4. **Language barriers** — regulators publish in English, but many stakeholders operate in Hindi

These gaps introduce compliance risk, slow down decisioning, and create inconsistent borrower experiences.

---

## 3. Solution — CreditSense Agent

CreditSense is a **conversational AI agent** that automates the end-to-end loan underwriting workflow:

```
Borrower Input → Profile Extraction → Metric Computation → RAG Retrieval →
Policy Checks → ML Risk Scoring → Report Generation → Hindi Translation → PDF Export
```

### Core Capabilities

| Capability | Implementation |
|---|---|
| **Conversational Intake** | Chat-based borrower detail collection with grouped question flow |
| **Guardrail System** | Multi-layer safety: keyword, LLM, continuation-aware, content abuse filters |
| **RAG-Grounded Decisions** | 57 RBI documents → 8,452 chunks in ChromaDB → semantic retrieval at decision time |
| **Deterministic Policy Engine** | NBFC-aligned cutoff checks (credit score, DTI, LTV, employment, history) |
| **ML Risk Scoring** | Milestone 1 trained model with heuristic fallback |
| **Structured Report Generation** | LLM-synthesized credit reports with deterministic fallback |
| **Bilingual Output** | English + Hindi (Devanagari) report generation |
| **PDF Export** | Downloadable English & Hindi PDFs with proper font rendering |

---

## 4. Milestone Progression

### Milestone 1 — Classical ML Foundation

Built the foundational ML pipeline for credit risk classification:

- **Data pipeline**: Cleaned and preprocessed borrower datasets
- **Feature engineering**: Age, income, credit score, DTI, LTV, employment tenure
- **Models trained**: Logistic Regression, Random Forest, and other classifiers
- **Output**: Serialized `model.pkl` used as the ML signal in Milestone 2
- **Stack**: Python, scikit-learn, pandas, Streamlit

### Milestone 2 — Agentic AI + RAG (Current)

Complete rebuild as a **LangGraph-orchestrated multi-node agent** with:

- **LangGraph StateGraph**: 6-node directed acyclic graph for conversation → decision pipeline
- **ChromaDB RAG**: 57 regulatory documents indexed with `all-MiniLM-L6-v2` embeddings
- **Groq LLM API**: `llama-3.1-8b-instant` (guardrails) + `llama-3.3-70b-versatile` (conversation, report, translation)
- **FastAPI Backend**: RESTful API serving agent turns, parameter seeding, and ingestion
- **Streamlit Frontend**: Professional chat UI with parameter form, report panel, and PDF downloads

---

## 5. Key Differentiators

| Feature | Why It Matters |
|---|---|
| **Deterministic + LLM Hybrid** | Policy engine guarantees consistency; LLM adds natural language and nuance |
| **Citation Grounding** | Every decision links back to specific regulatory documents |
| **Fairness-Aware** | No protected attributes in decisioning; explicit fairness note in reports |
| **Dual Fallback Architecture** | Every LLM call has a deterministic fallback — system works even without API keys |
| **Audit Trail** | Full state trace logged across all 6 nodes for compliance review |

---

## 6. Regulatory Corpus

The system ingests **57 official RBI documents** covering:

| Priority | Category | Examples |
|---|---|---|
| **P0 — Critical** | Core NBFC regulations | IRACP Master Circular, Fair Practices Code, Digital Lending Guidelines |
| **P1 — Important** | Basel & prudential norms | Basel III data, Capital adequacy, Master Directions |
| **P2 — Reference** | Supporting documents | Ombudsman schemes, FAME reports, demographic studies |

All documents are stored in `RAG files/` and indexed via the ingestion pipeline into ChromaDB.

---

## 7. Technology Stack Summary

| Layer | Technology |
|---|---|
| **Orchestration** | LangGraph (StateGraph) |
| **LLM Provider** | Groq API (Llama 3.1 / 3.3) |
| **Vector Database** | ChromaDB (persistent, local) |
| **Embeddings** | `all-MiniLM-L6-v2` (Sentence Transformers) |
| **Backend API** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **ML Framework** | scikit-learn + joblib |
| **PDF Generation** | fpdf2 (with Noto Sans Devanagari for Hindi) |
| **HTTP Client** | httpx |
| **Environment** | python-dotenv |

---

*CreditSense v2.0 — Project Overview | Last Updated: April 2026*
