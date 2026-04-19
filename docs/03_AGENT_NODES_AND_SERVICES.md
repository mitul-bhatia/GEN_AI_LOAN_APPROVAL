# CreditSense — Agent Nodes & Services Reference

> **Deep-dive into each LangGraph node, its service dependencies, and implementation details**

---

## 1. Node 1: Guardrail Node

**File:** `agent/nodes.py` → `guardrail_node()`
**Service:** `services/guardrail.py`
**LLM Model:** `llama-3.1-8b-instant` (fast, cheap)

### Purpose

First-pass safety and domain check on every incoming user message. Three-layer evaluation before any underwriting logic runs.

### Three-Layer Architecture

```
User Message
    │
    ▼
┌─────────────────────────────────────────┐
│ LAYER 1: Project Safety Guardrails      │
│                                         │
│ Checks for:                             │
│ • Document forgery / fake statements    │
│ • KYC/compliance bypass attempts        │
│ • Money laundering / illegal finance    │
│ • Prompt injection / jailbreak          │
│ • System prompt extraction              │
│ • Abusive / violent content             │
│                                         │
│ → If matched: BLOCK with safe reply     │
└─────────────────────┬───────────────────┘
                      │ (safe)
                      ▼
┌─────────────────────────────────────────┐
│ LAYER 2: Continuation Detection         │
│                                         │
│ If user has active finance context:     │
│ • Finance keyword match → continue      │
│ • Emotional keywords → continue         │
│ • Profile detail hints (regex) → cont.  │
│ • Short response (≤10 words) → continue │
│                                         │
│ → Avoids false-positive blocks during   │
│   active borrower intake                │
└─────────────────────┬───────────────────┘
                      │ (no continuation)
                      ▼
┌─────────────────────────────────────────┐
│ LAYER 3: Finance Domain Classification  │
│                                         │
│ 1. Keyword check (29 finance terms)     │
│ 2. If no keyword match → LLM check     │
│    • Model: llama-3.1-8b-instant        │
│    • Returns JSON: {is_finance_query,   │
│      reason}                            │
│ 3. If LLM unavailable → keyword-only   │
│                                         │
│ → PASS: route to conversation node      │
│ → BLOCK: "I only handle financial       │
│   topics" refusal                       │
└─────────────────────────────────────────┘
```

### Safety Patterns Blocked

| Pattern | Category | Response |
|---|---|---|
| Fake/forged documents | `unsafe-fraud-documents` | Redirect to legitimate eligibility improvement |
| KYC/compliance bypass | `unsafe-compliance-evasion` | Cannot assist with bypassing regulations |
| Money laundering/hawala | `unsafe-illegal-finance` | Cannot assist with illegal activity |
| System prompt bypass | `unsafe-prompt-bypass` | Cannot bypass system safeguards |
| Internal prompt reveal | `unsafe-internal-disclosure` | Cannot reveal internal logic |
| Hate/violence | `unsafe-abusive-content` | Safe financial guidance only |

---

## 2. Node 2: Conversation Node

**File:** `agent/nodes.py` → `conversation_node()`
**Service:** `services/profile_parser.py`
**LLM Model:** `llama-3.3-70b-versatile` (for field extraction)

### Purpose

Extract borrower profile fields from chat messages and progressively build a complete profile. When profile is complete, offer financial consultation or trigger report generation.

### Required Fields (15 Total)

```python
REQUIRED_FIELDS = [
    "name", "age", "city",
    "employment_type", "monthly_income", "employment_years",
    "credit_score", "existing_loan_count", "existing_emi_monthly",
    "payment_history",
    "loan_amount_requested", "loan_purpose", "loan_tenure_months",
    "collateral_type", "collateral_value",
]
```

### Extraction Pipeline (Dual Strategy)

```
User Message
    │
    ├──▸ Deterministic Extraction (regex-based)
    │    • Name: "name is X" / "borrower is X" / capitalized pattern
    │    • Age: "X years old" / "age is X"
    │    • City: "city is X" / "from X"
    │    • Employment Type: keyword match (salaried/self-employed/contract/gig)
    │    • Credit Score: "credit score X" / "CIBIL X"
    │    • Amounts: ₹/Rs/INR prefix + lakh/crore scaling
    │    • Loan purpose: keyword mapping (home/business/personal/education/vehicle)
    │    • Collateral: type + value extraction
    │    • Payment history: clean / 1 default / 2+ defaults
    │
    ├──▸ LLM Extraction (Groq API)
    │    • Model: llama-3.3-70b-versatile
    │    • System prompt: CONVERSATION_EXTRACTION_PROMPT
    │    • Returns strict JSON of detected fields
    │    • Critical rule: "Do NOT map existing EMI to loan_amount_requested"
    │
    └──▸ Merge Strategy
         • Deterministic results take priority
         • LLM fills gaps not found by regex
         • Normalize all values (int/float/string)
```

### Grouped Question Flow

Fields are asked in groups (not one-by-one) for faster intake:

| Group | Fields |
|---|---|
| 1 | Name, Age, City |
| 2 | Employment Type, Employment Years, Monthly Income |
| 3 | Credit Score, Existing Loan Count, Existing EMI |
| 4 | Payment History |
| 5 | Loan Amount Requested, Loan Purpose, Loan Tenure |
| 6 | Collateral Type, Collateral Value |

### Response Modes

| Condition | Behavior |
|---|---|
| `profile_complete = False` | Acknowledge received fields → ask next group |
| `profile_complete = True` + no report request | **5-point financial consultation** with PASS/WATCH/FAIL assessment |
| `profile_complete = True` + report requested | "Generating the borrower report now" → trigger RAG pipeline |
| Emotional message detected | Prepend empathy line ("I understand this can feel stressful...") |

### 5-Point Consultation (Pre-Report)

When the profile is complete but no report is requested yet, the agent provides real-time financial guidance covering:

1. **Income Strength** — Income-to-EMI coverage ratio (≥3.0x = PASS, ≥2.0x = WATCH, <2.0x = FAIL)
2. **Debt Burden** — Post-loan DTI (≤0.45 = PASS, ≤0.60 = WATCH, >0.60 = FAIL)
3. **Credit Quality** — Credit score bands (≥720 = PASS, ≥650 = WATCH, <650 = FAIL)
4. **Repayment Behavior** — Payment history + existing EMI load
5. **Collateral Support** — LTV ratio (≤0.80 = PASS, ≤1.00 = WATCH, >1.00 = FAIL)

---

## 3. Node 3: RAG Retriever Node

**File:** `agent/nodes.py` → `rag_retriever_node()`
**Service:** `services/retriever.py`
**Embedding Model:** `all-MiniLM-L6-v2`

### Purpose

Retrieve the most relevant regulatory document chunks from ChromaDB based on the borrower's profile and computed ratios.

### Query Construction

The retriever builds a composite semantic query from the borrower profile:

```python
query = " ".join([
    f"loan purpose {profile['loan_purpose']}",
    f"loan amount {profile['loan_amount_requested']}",
    f"credit score {profile['credit_score']}",
    f"post loan dti {ratios['post_loan_dti']}",
    f"employment type {profile['employment_type']}",
    f"collateral {profile['collateral_type']}",
    f"borrower conversation context {context[:400]}",
    "RBI NBFC underwriting fair practices",
])
```

### Retrieval Pipeline

```
1. Build query string from profile + ratios + conversation context
2. Encode query with all-MiniLM-L6-v2 (normalized embeddings)
3. Query ChromaDB collection (top_k=8 by default)
4. For each retrieved chunk:
   • Extract document text
   • Extract metadata (source_file, priority, chunk_index)
   • Compute distance score
5. Return: (rag_chunks, citations)
```

### Output Format

```python
rag_chunk = {
    "text": "Full chunk text...",
    "source": "3.Fair-Practice-Code-English-16-May-24",
    "priority": "P0",
    "distance": 0.4231,
}

citation = {
    "title": "3.Fair-Practice-Code-English-16-May-24",
    "snippet": "First 300 chars of chunk...",
    "source": "3.Fair-Practice-Code-English-16-May-24",
}
```

---

## 4. Node 4: Policy Node

**File:** `agent/nodes.py` → `policy_node()`
**Services:** `services/policy_engine.py`, `services/ml_adapter.py`, `services/borrower_metrics.py`
**LLM:** None — fully deterministic

### Purpose

Execute deterministic NBFC policy checks and ML risk scoring to produce a quantitative underwriting decision.

### 4.1 Financial Metric Computation (`borrower_metrics.py`)

```python
EMI = P × r × (1+r)^n / ((1+r)^n - 1)
# Default annual_rate = 15% (configurable via env)

Ratios computed:
• projected_emi    — EMI for the requested loan
• current_dti      — existing_emi / monthly_income
• post_loan_dti    — (existing_emi + projected_emi) / monthly_income
• ltv_ratio        — loan_amount / collateral_value (if collateral exists)
```

### 4.2 ML Risk Scoring (`ml_adapter.py`)

**Priority:** Trained model → Heuristic fallback

```
1. Attempt to load Milestone 1 model (model.pkl or logistic_regression.pkl)
2. If model found:
   • Build feature DataFrame (9 features)
   • predict_proba → safe_prob × 100 = score
   • Classify: ≥75 = LOW, ≥55 = MEDIUM, <55 = HIGH
3. If model not found → heuristic scoring:
   • Base: 50
   • Credit score: +25 (≥750), +12 (≥680), +3 (≥600), -15 (<600)
   • DTI: +18 (≤0.45), +6 (≤0.60), -8 (≤0.75), -18 (>0.75)
   • Payment: +8 (clean), -6 (1 default), -14 (2+ defaults)
   • Employment: +6 (≥2yr), +2 (≥1yr), -4 (<1yr)
   • Clamp to [0, 100]
```

### 4.3 Policy Engine (`policy_engine.py`)

Six deterministic policy checks against NBFC-aligned cutoffs:

| Check | Pass | Watch | Fail |
|---|---|---|---|
| **Credit Score** | ≥ 750 | ≥ 680 | ≥ 600 |
| **Post-loan DTI** | ≤ 0.45 | ≤ 0.60 | ≤ 0.75 |
| **Employment Tenure** | ≥ 2.0 years | ≥ 1.0 year | < 1.0 year |
| **LTV Ratio** | Varies by collateral type | +5% above max | Beyond |
| **Payment History** | Clean | 1 default | 2+ defaults |
| **ML Risk Score** | ≥ 70 | ≥ 55 | < 55 |

**LTV Thresholds by Collateral Type:**

| Type | Max LTV |
|---|---|
| Property | 0.80 |
| Gold | 0.75 |
| Fixed Deposit | 0.90 |
| Vehicle | 0.85 |

### 4.4 Decision Scoring

```
Base Score: 100
- Each FAIL: -18 points
- Each WATCH: -10 points

Decision Bands:
• ≥ 80 → APPROVE
• 60–79 → CONDITIONAL
• < 60 → ESCALATE
```

---

## 5. Node 5: Report Node

**File:** `agent/nodes.py` → `report_node()`
**Service:** `services/report_generator.py`
**LLM Model:** `llama-3.3-70b-versatile`

### Purpose

Generate a structured credit assessment report combining all collected data, policy results, and regulatory citations.

### Dual Generation Strategy

```
1. If Groq API keys available:
   a. Generate LLM-powered report (llama-3.3-70b-versatile)
   b. Validate: report must contain correct loan amount and credit score
   c. If validation passes → use LLM report
   d. If validation fails → fall back to deterministic

2. If no API keys or LLM fails:
   → Generate deterministic report (template-based)
```

### Report Structure

```markdown
## Credit Assessment Report
**Borrower:** Name | Age | City
**Employment:** Type - Years | Monthly Income
**Loan Request:** Amount | Purpose | Tenure
**Generated On:** Date

### Computed Metrics
| Metric | Value | Threshold | Status |
(6 rows: credit score, DTI, employment, LTV, history, ML score)

### Financial Ratios
- Projected EMI, Current DTI, Post-loan DTI, LTV Ratio

### Regulatory Context
(Top 3 citations from RAG with source and snippet)

### Conversation Context
(Concatenated user intent summary)

### Decision: APPROVE/CONDITIONAL/ESCALATE (Score: X/100)
**Conditions:** (auto-generated based on risk flags)

### Fairness Note
No protected attributes used in decisioning.

*Disclaimer: AI-assisted assessment, not legally binding.*
```

---

## 6. Node 6: Translate Node

**File:** `agent/nodes.py` → `translate_node()`
**Service:** `services/translator.py`
**LLM Model:** `llama-3.3-70b-versatile`

### Purpose

Translate the English credit report into Hindi (Devanagari script) while preserving financial terminology.

### Translation Strategy

```
1. If Groq API keys available:
   a. Attempt LLM translation (up to 2 retries)
   b. Validate: check for presence of Devanagari characters (Unicode 0900-097F)
   c. If valid → use LLM translation

2. If no keys or LLM fails:
   → Deterministic translation using line-level and inline mapping
```

### Deterministic Translation Map (Key Terms)

| English | Hindi |
|---|---|
| Credit Assessment Report | क्रेडिट मूल्यांकन रिपोर्ट |
| Computed Metrics | गणना किए गए मानदंड |
| Financial Ratios | वित्तीय अनुपात |
| Regulatory Context | नियामकीय संदर्भ |
| Fairness Note | निष्पक्षता नोट |
| Borrower | उधारकर्ता |
| Employment | रोज़गार |
| Loan Request | ऋण अनुरोध |
| Decision: APPROVE | निर्णय: स्वीकृत |
| Decision: ESCALATE | निर्णय: एस्केलेट |
| Decision: REJECT | निर्णय: अस्वीकृत |

### Translation Rules

- **Keep in English:** Names, numbers, INR values, abbreviations (DTI, LTV, EMI, RBI)
- **Translate:** Section headings, natural language text, conditions, disclaimers
- **Preserve:** Markdown structure, table formatting, bullet points

---

## 7. Supporting Services

### 7.1 Groq Key Pool (`services/groq_pool.py`)

Thread-safe round-robin key rotation across up to 5 Groq API keys:

```python
# Loads from: GROQ_KEY_1 through GROQ_KEY_5 + GROQ_API_KEY
# Deduplicates keys
# Thread-safe with threading.Lock
# next_key() returns keys in rotating order
```

### 7.2 Groq Client (`services/groq_client.py`)

HTTP-based completion client with automatic key rotation on rate limits:

```python
# For each attempt (one per key in pool):
#   1. Build message payload {system, user}
#   2. POST to api.groq.com/openai/v1/chat/completions
#   3. If 429 (rate limit) → rotate key and retry
#   4. If error → rotate and retry
#   5. Return content.strip()
```

### 7.3 PDF Exporter (`services/pdf_exporter.py`)

Generates downloadable PDFs using `fpdf2`:

- **English PDF:** Helvetica font, green header, markdown-to-plaintext conversion
- **Hindi PDF:** Noto Sans Devanagari TTF (embedded), same structure
- **Features:** Auto page break, long-word wrapping, timestamp footer, disclaimer
- **Output:** Raw `bytes` for `st.download_button(data=...)`

### 7.4 Settings (`services/settings.py`)

Centralized configuration via `@dataclass(frozen=True)`:

- All paths support environment variable overrides
- RAG docs path auto-discovers `../../RAG files/` workspace directory
- ML model path cascades: primary → fallback (Milestone 1 model)

### 7.5 Backend Client (`services/backend_client.py`)

HTTP client used by Streamlit to communicate with the FastAPI backend:

| Method | Endpoint | Timeout |
|---|---|---|
| `health()` | `GET /api/v1/health` | 10s |
| `fetch_initial_state()` | `GET /api/v1/agent/state/initial` | 20s |
| `run_turn()` | `POST /api/v1/agent/turn` | 120s |
| `seed_parameters()` | `POST /api/v1/agent/seed-parameters` | 60s |

---

*CreditSense v2.0 — Agent Nodes & Services Reference | Last Updated: April 2026*
