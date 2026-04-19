# CreditSense — Known Gaps, Limitations & Future Work

> **Honest assessment of current limitations, technical debt, and improvement roadmap**

---

## 1. Known Gaps — Current Implementation

### 1.1 RAG Pipeline Gaps

| Gap | Impact | Severity |
|---|---|---|
| **No priority-balanced retrieval** | Top-K retrieval may return all P2 chunks, missing critical P0/P1 regulations | 🔴 High |
| **No chunk re-ranking** | Raw cosine similarity may not reflect regulatory relevance accurately | 🟡 Medium |
| **No citation auditor** | Retrieved citations are not validated against the decision logic | 🟡 Medium |
| **Stale RAG corpus** | No automated pipeline to update corpus when new RBI circulars are released | 🟡 Medium |
| **No hybrid search** | Only dense vector search — no BM25/keyword search for exact regulatory references | 🟠 Low-Medium |

**Recommendations:**
- Implement P0-P4 priority-seeded retrieval ensuring at least 1 chunk per priority level
- Add a cross-encoder re-ranker (e.g., `ms-marco-MiniLM-L-6-v2`) for reranking top-K results
- Build a citation auditor node that validates each citation against the specific policy check it supports
- Create an ingestion scheduler that watches for new documents in the RAG directory

---

### 1.2 Model & Scoring Gaps

| Gap | Impact | Severity |
|---|---|---|
| **ML model not retrained on M2 data** | Milestone 1 model was trained on a different feature set | 🟡 Medium |
| **No model monitoring** | No drift detection, no performance tracking over time | 🟡 Medium |
| **Heuristic weights are hand-tuned** | Not calibrated against actual loan outcomes | 🟡 Medium |
| **No ensemble scoring** | ML score + heuristic are not blended — one replaces the other | 🟠 Low-Medium |
| **Single credit score source** | No multi-bureau support (only CIBIL-style score range) | 🟠 Low |

**Recommendations:**
- Retrain the Milestone 1 model on the full 15-field feature set used in M2
- Implement model monitoring with prediction distribution tracking
- Calibrate heuristic weights against historical approval data
- Add ensemble scoring: `final_score = α × model_score + (1-α) × heuristic_score`

---

### 1.3 Agent Pipeline Gaps

| Gap | Impact | Severity |
|---|---|---|
| **No multi-turn memory optimization** | Full state is serialized/deserialized every turn — grows with conversation | 🟡 Medium |
| **No conversation summarization** | Long conversations may exceed context limits in report generation | 🟡 Medium |
| **No structured error recovery** | If a middle node fails, the entire graph run fails | 🟡 Medium |
| **No agent evaluation framework** | No automated scoring of agent quality (correctness, helpfulness) | 🟡 Medium |
| **Guardrail LLM call on every non-keyword message** | Adds latency for every message that doesn't match finance keywords | 🟠 Low |

**Recommendations:**
- Implement conversation context windowing (last N turns only for report generation)
- Add node-level try/catch with partial state preservation
- Build an evaluation harness using the e2e scenarios with expected outputs
- Cache guardrail LLM results for similar messages

---

### 1.4 Frontend & UX Gaps

| Gap | Impact | Severity |
|---|---|---|
| **No real-time streaming** | Report generation shows a spinner — no streamed output | 🟡 Medium |
| **No knowledge graph visualization** | M2 removed the graph rendering from M1's React frontend | 🟡 Medium |
| **No mobile responsiveness** | CSS is desktop-first, limited mobile breakpoints | 🟠 Low |
| **No user authentication** | No login — anyone with the URL can use the system | 🟠 Low |
| **Hindi PDF font may be missing** | If NotoSansDevanagari TTF is not present, Hindi PDF degrades to Latin text | 🟠 Low |

**Recommendations:**
- Add Streamlit streaming for report generation using `st.write_stream()`
- Re-add knowledge graph visualization using `streamlit-agraph` or `pyvis`
- Add `st.secrets` or environment-based API key protection for production
- Bundle the Devanagari font in the repository

---

### 1.5 Security & Compliance Gaps

| Gap | Impact | Severity |
|---|---|---|
| **API keys in .env (not encrypted)** | Groq keys stored in plaintext | 🟡 Medium |
| **No rate limiting on backend** | API endpoints are unprotected against abuse | 🟡 Medium |
| **No audit logging** | Node trace exists but isn't persisted to external storage | 🟡 Medium |
| **No data privacy controls** | Borrower PII is held in session state without encryption | 🟡 Medium |
| **CORS allows localhost:*** | Broad CORS policy for development | 🟠 Low |

**Recommendations:**
- Use `streamlit secrets` or a vault for production key management
- Add FastAPI middleware for rate limiting (e.g., `slowapi`)
- Persist trace logs to a structured audit database
- Implement PII masking in logs and stored state

---

## 2. Technical Debt

### 2.1 Architecture Debt

| Item | Description |
|---|---|
| **Mixed async/sync** | FastAPI is async-capable but all services are synchronous |
| **No dependency injection** | Services are imported directly — no container or factory pattern |
| **Shared module imports** | `agent` ↔ `services` have circular import potential (managed via lazy imports) |
| **No database for conversations** | All state is held in Streamlit `session_state` — lost on refresh |

### 2.2 Testing Debt

| Item | Description |
|---|---|
| **No unit tests** | Individual service functions are untested |
| **No mock LLM tests** | LLM-dependent code has no mocked test coverage |
| **E2E tests require running backend** | `e2e_scenarios.py` needs live API — no containerized test env |
| **No CI/CD pipeline** | No automated testing on push/merge |

---

## 3. Comparison: What Was Planned vs. What Was Built

### From the PRD (CREDITSENSE_V2_PRD.md):

| PRD Feature | Status | Notes |
|---|---|---|
| Conversational borrower intake | ✅ Fully implemented | Dual extraction (regex + LLM), grouped questions |
| Guardrail domain check | ✅ Fully implemented | 3-layer architecture exceeds PRD spec |
| RAG retrieval from 57 docs | ✅ Implemented | 8,452 chunks indexed, top-k=8 retrieval |
| Policy engine with cutoffs | ✅ Fully implemented | 6 checks with NBFC-aligned thresholds |
| ML risk scoring | ✅ Implemented with fallback | Trained model + heuristic fallback |
| Structured credit report | ✅ Implemented | LLM + deterministic fallback with validation |
| Hindi translation | ✅ Implemented | LLM + deterministic fallback |
| PDF export (EN + HI) | ✅ Implemented | fpdf2 with Devanagari font support |
| Priority-balanced P0-P4 retrieval | ❌ Not implemented | Current retrieval is pure top-k without priority seeding |
| Citation auditor | ❌ Not implemented | Planned as "next step" in PRD |
| Groq-driven node prompts (full) | ⚠️ Partially implemented | Guardrail and extraction use LLM; report uses LLM with fallback |
| Knowledge graph visualization | ❌ Removed in M2 rebuild | Was present in M1's React frontend |
| Streamlit Community Cloud deployment | ❌ Not yet deployed | Local-only currently |
| Automated regression suite | ❌ Not implemented | E2E scenarios exist but no CI integration |

---

## 4. Improvement Roadmap

### Phase 1 — Quick Wins (1-2 days)

- [ ] Add Devanagari font file to `assets/fonts/` for reliable Hindi PDFs
- [ ] Add unit tests for `borrower_metrics.py` and `policy_engine.py` (pure functions)
- [ ] Tighten CORS origins for non-development deployment
- [ ] Add `--reset` flag to ingest script for clean re-indexing

### Phase 2 — RAG Improvements (3-5 days)

- [ ] Implement priority-seeded retrieval (ensure P0/P1 representation)
- [ ] Add cross-encoder re-ranking after initial retrieval
- [ ] Build citation auditor that validates regulatory relevance
- [ ] Add BM25 hybrid search for exact term matching

### Phase 3 — Production Readiness (1-2 weeks)

- [ ] Add Streamlit Cloud deployment with `secrets.toml`
- [ ] Implement API rate limiting and request logging
- [ ] Add persistent conversation storage (SQLite or Redis)
- [ ] Implement basic authentication for the API
- [ ] Set up CI/CD with automated E2E testing

### Phase 4 — Advanced Features (2-4 weeks)

- [ ] Knowledge graph visualization in Streamlit
- [ ] Model retraining pipeline with M2 feature set
- [ ] Streaming report generation with `st.write_stream`
- [ ] Multi-bureau credit score support
- [ ] Loan comparison mode (side-by-side borrower comparison)

---

## 5. Rubric Alignment Gaps

For the academic rubric (`End-Sem_Project_Rubric`), potential scoring considerations:

| Rubric Criterion | Status | Potential Improvement |
|---|---|---|
| Agentic AI / GenAI methods | ✅ Strong — LangGraph StateGraph with 6 nodes | Document the graph routing logic more visually |
| RAG integration | ✅ Strong — 57 docs, 8452 chunks, cited in report | Add priority-balanced retrieval |
| State management | ✅ Strong — TypedDict across all nodes | Add persistence beyond session state |
| Bias/hallucination reduction | ✅ Strong — guardrails + deterministic fallbacks + citation grounding | Add explicit bias testing scenarios |
| Structured output | ✅ Strong — formatted report with metrics table | Add knowledge graph output |
| Deployed publicly | ⚠️ Gap — local only | Deploy to Streamlit Community Cloud |
| Professional UI | ✅ Good — custom CSS, chat + form + report panel | Add mobile responsiveness |
| Hindi output | ✅ Strong — LLM + deterministic translation + PDF | Verify font is bundled |

---

*CreditSense v2.0 — Known Gaps & Future Work | Last Updated: April 2026*
