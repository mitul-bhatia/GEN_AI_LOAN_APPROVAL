# CreditSense Agent — Clean Rebuild PRD
## Version 2.0 | Streamlit + LangGraph + Chroma RAG

---

## 1. WHAT WE ARE BUILDING

A conversational financial agent that:
1. Chats with a loan officer / user to collect borrower details naturally
2. Once enough info is collected, retrieves relevant regulations from 57 RAG docs
3. Runs policy checks + ML risk scoring
4. Generates a structured credit report with cited regulations
5. Lets user download the report in English (PDF) and Hindi (PDF)

---

## 2. THE EXACT USER JOURNEY

```
User opens Streamlit app
        ↓
Agent: "Hello! I'm CreditSense. Tell me about the borrower."
        ↓
User: "Rajesh Kumar, 45 years old, salaried, 60k/month income"
        ↓
[GUARDRAIL CHECK] — Is this finance related? YES → continue
        ↓
Agent: "Got it. What is Rajesh's credit score and existing loan obligations?"
        ↓
User: "Credit score is 720. He has one existing loan, EMI is ₹8000/month"
        ↓
Agent: "What loan is he applying for? Amount, purpose, and tenure?"
        ↓
User: "5 lakh personal loan, 36 months"
        ↓
Agent: "Any collateral? Also his payment history — any defaults?"
        ↓
User: "No collateral. Clean payment history."
        ↓
[PROFILE COMPLETE] — Agent detects all required fields collected
        ↓
Agent: "Perfect. Analysing Rajesh's profile against RBI regulations..."
[SPINNER — RAG retrieval + policy engine + LLM synthesis running]
        ↓
Agent shows FINAL REPORT in chat:
  - Borrower summary
  - Computed metrics (DTI, LTV, EMI)
  - What passes / what is flagged (vs policy thresholds)
  - Regulations that apply (with exact citations)
  - Decision: APPROVE / CONDITIONAL / ESCALATE
  - Conditions if conditional
  - Fairness note
  - Disclaimer

[ Download English PDF ]  [ Download Hindi PDF ]
```

---

## 3. ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                   STREAMLIT FRONTEND                     │
│                                                          │
│  st.chat_message / st.chat_input                        │
│  st.spinner during analysis                             │
│  st.download_button for PDF exports                     │
└──────────────────────┬──────────────────────────────────┘
                       │ Python function call (same process)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR                      │
│                                                          │
│  Node 1: guardrail_node                                 │
│  Node 2: conversation_node   ← collects info via chat   │
│  Node 3: rag_retriever_node  ← queries Chroma           │
│  Node 4: policy_node         ← runs cutoff checks       │
│  Node 5: report_node         ← LLM generates report     │
│  Node 6: translate_node      ← Hindi via Groq           │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐     ┌──────────────────────┐
│  CHROMA (local)  │     │   GROQ API           │
│  57 RAG docs     │     │   3 keys rotating    │
│  8452 chunks     │     │   LLM calls          │
└──────────────────┘     └──────────────────────┘
```

---

## 4. LANGGRAPH STATE

```python
class AgentState(TypedDict):
    # Conversation
    messages: list[dict]          # [{role, content}] full history
    
    # Collection tracking
    collected: dict               # fields collected so far
    missing_fields: list[str]     # fields still needed
    profile_complete: bool        # True when all required fields present
    
    # Guardrail
    is_finance_query: bool
    guardrail_reason: str
    
    # After profile complete
    borrower_profile: dict        # structured borrower data
    computed_ratios: dict         # DTI, LTV, EMI, post_loan_DTI
    ml_risk_score: float
    ml_risk_class: str            # HIGH / MEDIUM / LOW
    
    # RAG
    rag_chunks: list[dict]        # [{text, source, priority}]
    
    # Policy
    policy_checks: list[dict]
    risk_flags: list[str]
    decision: str                 # approve / conditional / escalate
    decision_score: float
    
    # Final output
    report_en: str                # English markdown report
    report_hi: str                # Hindi report text
    citations: list[dict]         # [{title, snippet, source}]
```

---

## 5. REQUIRED BORROWER FIELDS

```python
REQUIRED_FIELDS = [
    "name",
    "age",
    "employment_type",       # Salaried | Self-Employed | Contract | Gig
    "monthly_income",
    "employment_years",
    "credit_score",
    "existing_loan_count",
    "existing_emi_monthly",
    "payment_history",       # Clean | 1 Default | 2+ Defaults
    "loan_amount_requested",
    "loan_purpose",          # Home | Business | Personal | Education | Vehicle
    "loan_tenure_months",
    "collateral_type",       # None | Property | Gold | Fixed Deposit | Vehicle
    "collateral_value",      # 0 if None
    "city",
]
```

---

## 6. GROQ MODEL ASSIGNMENTS

```python
GUARDRAIL_MODEL    = "llama-3.1-8b-instant"        # fast, cheap
CONVERSATION_MODEL = "llama-3.3-70b-versatile"     # collects info naturally
REPORT_MODEL       = "llama-3.3-70b-versatile"     # generates the credit report
TRANSLATE_MODEL    = "llama-3.3-70b-versatile"     # Hindi translation
```

All use Groq API. 3 keys in round-robin rotation.

---

## 7. FOLDER STRUCTURE

```
creditsense/
├── app.py                        # Streamlit entry point
├── agent/
│   ├── __init__.py
│   ├── graph.py                  # LangGraph StateGraph definition
│   ├── nodes.py                  # All node implementations
│   ├── state.py                  # AgentState TypedDict
│   └── prompts.py                # All LLM system prompts
├── services/
│   ├── __init__.py
│   ├── guardrail.py              # Finance domain check
│   ├── profile_parser.py         # Extract borrower fields from chat
│   ├── borrower_metrics.py       # Compute DTI, LTV, EMI
│   ├── ml_adapter.py             # Risk score (M1 model or heuristic)
│   ├── policy_engine.py          # Bank cutoff checks
│   ├── retriever.py              # Chroma RAG query
│   ├── report_generator.py       # LLM report generation
│   ├── translator.py             # Hindi translation via Groq
│   ├── pdf_exporter.py           # English + Hindi PDF generation
│   └── groq_pool.py              # Key rotation
├── chroma_store/                 # Chroma persisted DB (gitignored)
├── scripts/
│   └── ingest.py                 # One-time: index 57 docs into Chroma
├── rag_docs/                     # Your 57 regulatory PDFs
├── ml_model/
│   └── model.pkl                 # Milestone 1 trained model
├── .env                          # GROQ_KEY_1, GROQ_KEY_2, GROQ_KEY_3
├── requirements.txt
└── README.md
```

---

## 8. NODE DEFINITIONS

### Node 1: guardrail_node
```
Input:  latest user message
Model:  llama-3.1-8b-instant (fast)
Task:   Is this message related to banking, finance, credit, loans, RBI?
Output: {is_finance_query: bool, reason: str}
If NO: agent replies "I only handle financial topics" and stops
```

### Node 2: conversation_node
```
Input:  full message history + collected fields so far
Model:  llama-3.3-70b-versatile
Task:   Two sub-tasks in ONE LLM call:
        1. Extract any borrower fields from the latest message
           and merge into `collected` dict
        2. If fields still missing: generate a natural follow-up question
           asking for the next missing field(s)
        3. If all fields present: set profile_complete = True
Output: {collected, missing_fields, profile_complete, next_question}

NOTE: This node runs on EVERY message until profile_complete = True
      It asks for 2-3 fields at a time (not one by one — too slow)
```

### Node 3: rag_retriever_node
```
Input:  borrower_profile dict
Task:   Build a rich query string from the profile
        e.g. "personal loan DTI 0.61 credit score 720 unsecured NBFC"
        Query Chroma top_k=8
        Return chunks with source filename + priority label
Output: {rag_chunks, citations}
Runs:   Only once, when profile_complete = True
```

### Node 4: policy_node
```
Input:  borrower_profile + computed_ratios + ml_risk_score
Task:   Run all cutoff checks (same policy_engine.py logic)
        credit_score vs threshold
        post_loan_dti vs max
        employment_years vs minimum
        ltv vs cap (if collateral present)
        payment_history check
Output: {policy_checks, risk_flags, decision, decision_score}
No LLM needed — pure Python deterministic
```

### Node 5: report_node
```
Input:  everything — profile, ratios, policy checks, rag_chunks, citations
Model:  llama-3.3-70b-versatile
Task:   Generate the structured credit report (see Section 9)
Output: {report_en, citations}
```

### Node 6: translate_node
```
Input:  report_en
Model:  llama-3.3-70b-versatile
Task:   Translate to Hindi (Devanagari)
        Keep numbers, financial terms, names in English
Output: {report_hi}
```

---

## 9. FINAL REPORT FORMAT

```markdown
## Credit Assessment Report
**Borrower:** Rajesh Kumar | Age: 45 | City: Mumbai
**Employment:** Salaried — 6 years | Monthly Income: ₹60,000
**Loan Request:** ₹5,00,000 | Purpose: Personal | Tenure: 36 months

---

### Computed Metrics
| Metric | Value | Threshold | Status |
|---|---|---|---|
| Credit Score | 720 | ≥ 680 | ✅ PASS |
| Post-loan DTI | 0.61 | ≤ 0.60 | ⚠️ WATCH |
| Employment Tenure | 6 years | ≥ 2 years | ✅ PASS |
| LTV Ratio | N/A | Unsecured | ✅ N/A |
| Payment History | Clean | No defaults | ✅ PASS |

---

### Regulatory Context
**[RBI Fair Practices Code — NBFC]:** Lenders must disclose all terms
and charges clearly before loan disbursement.

**[RBI Credit Risk Guidelines]:** DTI ratio above 0.60 requires
additional income verification and board-level risk approval.

**[RBI IRACP Master Circular]:** Accounts with 90+ day overdue
payments must be classified as NPA with 15% provisioning.

---

### Decision: ⚠️ CONDITIONAL APPROVE (Score: 74/100)

**Conditions:**
1. Reduce loan amount to ₹4,20,000 to bring post-loan DTI below 0.60
2. Submit last 6 months salary slips for income verification
3. No new credit facilities for 90 days post-disbursement

---

### Fairness Note
No discriminatory signals detected. Gig/contract employment flag
not triggered. City tier adjustment not applied.

---

*Disclaimer: This is an AI-assisted assessment tool. It does not
constitute a legally binding credit decision. Final approval requires
authorised officer review per RBI guidelines.*
```

---

## 10. STREAMLIT APP STRUCTURE (`app.py`)

```python
# Session state keys:
#   st.session_state.messages     → chat history for display
#   st.session_state.agent_state  → LangGraph agent state
#   st.session_state.report_ready → bool
#   st.session_state.report_en    → English report text
#   st.session_state.report_hi    → Hindi report text

# Layout:
#   Left column (60%): chat interface
#     st.chat_message for each message
#     st.chat_input at bottom
#   Right column (40%): report panel
#     Hidden until report_ready = True
#     Shows report + download buttons

# On each user message:
#   1. Append to messages
#   2. Call agent graph with current state
#   3. If agent returns next_question → show in chat
#   4. If agent returns report → show in right panel
#   5. Show download buttons

# Streamlit Community Cloud deployment:
#   secrets.toml for API keys (not .env)
#   chroma_store/ committed to repo (pre-indexed)
```

---

## 11. PDF EXPORT (`pdf_exporter.py`)

```python
# Use: reportlab or fpdf2 (both pip installable, no system deps)
# 
# English PDF:
#   - Header: CreditSense logo text + report date
#   - Body: render the markdown report_en as formatted PDF
#   - Footer: disclaimer + generated timestamp
#
# Hindi PDF:
#   - Same structure
#   - Font: Noto Sans Devanagari (embed .ttf in repo)
#   - Body: report_hi text
#
# Both returned as bytes → st.download_button(data=bytes)
```

---

## 12. INGEST SCRIPT (`scripts/ingest.py`)

```python
# Run ONCE before deployment:
#
# 1. Read all files from rag_docs/ (PDF, DOCX, TXT)
# 2. Extract text
# 3. Chunk: 1200 chars, 150 char overlap
# 4. For each chunk: embed using sentence-transformers
#    (all-MiniLM-L6-v2 — small, fast, free)
# 5. Upsert into Chroma collection "creditsense_docs"
#    Metadata: {source_file, priority, chunk_index}
# 6. Commit chroma_store/ to repo
#    (Streamlit Cloud will use the committed DB)
#
# Priority mapping (hardcoded dict):
#   "RBI_IRACP" → P0
#   "Fair_Practices" → P0
#   "Digital_Lending" → P0
#   "Basel_III" → P1
#   etc.
```

---

## 13. POLICY ENGINE CUTOFFS

```python
BANK_CUTOFFS = {
    "credit_score_pass":       750,
    "credit_score_watch":      680,
    "credit_score_fail":       600,
    "post_loan_dti_pass":      0.45,
    "post_loan_dti_watch":     0.60,
    "post_loan_dti_fail":      0.75,
    "employment_years_pass":   2.0,
    "employment_years_watch":  1.0,
    "ltv_property_max":        0.80,
    "ltv_gold_max":            0.75,
    "ltv_fd_max":              0.90,
    "ltv_vehicle_max":         0.85,
}
# Score:  100 base
# -18 pts per FAIL cutoff
# -10 pts per WATCH cutoff
# ≥80 → approve | 60-79 → conditional | <60 → escalate
```

---

## 14. ENVIRONMENT VARIABLES

```bash
# .env (local) / secrets.toml (Streamlit Cloud)
GROQ_KEY_1=gsk_...
GROQ_KEY_2=gsk_...
GROQ_KEY_3=gsk_...
CHROMA_PATH=./chroma_store
COLLECTION_NAME=creditsense_docs
```

---

## 15. REQUIREMENTS

```txt
streamlit>=1.32.0
langgraph>=0.1.0
langchain-groq
chromadb>=0.4.0
sentence-transformers
pdfplumber
python-docx
fpdf2
reportlab
httpx
pydantic>=2.0
python-dotenv
scikit-learn
joblib
```

---

## 16. BUILD ORDER

```
Phase 1 — Foundation (2 hrs)
  □ Create folder structure
  □ .env + groq_pool.py
  □ borrower_metrics.py (DTI/LTV/EMI math)
  □ policy_engine.py (cutoff checks)
  □ ml_adapter.py (M1 model wrapper)

Phase 2 — RAG (1 hr)
  □ scripts/ingest.py
  □ Run ingest on rag_docs/ → chroma_store/ built
  □ retriever.py (query Chroma, return chunks + citations)

Phase 3 — Agent (3 hrs)
  □ state.py (AgentState TypedDict)
  □ prompts.py (all system prompts)
  □ nodes.py (all 6 nodes)
  □ graph.py (LangGraph StateGraph wiring)
  □ guardrail.py
  □ profile_parser.py

Phase 4 — Report + Export (1 hr)
  □ report_generator.py
  □ translator.py
  □ pdf_exporter.py (English + Hindi PDF)

Phase 5 — Streamlit UI (2 hrs)
  □ app.py (chat UI + report panel + download buttons)
  □ Test full end-to-end flow

Phase 6 — Deploy (1 hr)
  □ Push to GitHub (include chroma_store/)
  □ Deploy to Streamlit Community Cloud
  □ Add secrets in Streamlit dashboard
  □ Verify public URL works
```

---

## 17. CONVERSATION FLOW LOGIC

```python
# In conversation_node — the core logic:

FIELDS_TO_ASK_TOGETHER = [
    ["name", "age", "city"],
    ["employment_type", "employment_years", "monthly_income"],
    ["credit_score", "existing_loan_count", "existing_emi_monthly"],
    ["payment_history"],
    ["loan_amount_requested", "loan_purpose", "loan_tenure_months"],
    ["collateral_type", "collateral_value"],
]

# Ask fields in groups — not one by one
# After each user reply → extract what was given → move to next group
# When all 15 fields present → profile_complete = True
# Trigger: rag_retriever + policy + report + translate
```

---

## 18. GRAPH ROUTING LOGIC

```
START
  ↓
guardrail_node
  ↓ if NOT finance → END (refusal message)
  ↓ if finance →
conversation_node
  ↓ if profile NOT complete → END (ask next question, wait for user)
  ↓ if profile complete →
rag_retriever_node
  ↓
policy_node
  ↓
report_node
  ↓
translate_node
  ↓
END (report ready, show in UI)
```

---

## 19. WHAT RUBRIC CRITERIA THIS SATISFIES

| Criterion | How |
|---|---|
| Agentic AI / GenAI methods | LangGraph StateGraph with 6 nodes |
| RAG integration | Chroma with 57 docs, cited in report |
| State management | AgentState TypedDict across all nodes |
| Bias/hallucination reduction | Guardrail node + citations grounding |
| Structured output | Formatted report with metrics table |
| Deployed publicly | Streamlit Community Cloud |
| Professional UI | Chat + report panel + PDF download |
| Hindi output | Groq translation + PDF export |

---

*CreditSense v2.0 PRD | Clean rebuild | Streamlit + LangGraph + Chroma*
