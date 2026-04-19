# CreditSense Model and ML Documentation

> Refreshed from current code scan on 2026-04-19.

## 1. Overview

Milestone 2 uses a hybrid decision stack:

1. deterministic underwriting rules
2. ML risk score signal
3. LLM-generated narrative explanations

This design keeps decision math auditable while still enabling natural language output.

## 2. Heuristic Risk Scorer (`services/risk_scorer.py`)

A pure mathematical ruleset is used to generate the initial risk score. The score starts at 50 and adjusts by borrower profile:

### 3.1 Credit Score Contribution

- `>= 750`: +25
- `>= 680`: +12
- `>= 600`: +3
- `< 600`: -15

### 3.2 Post-Loan DTI Contribution

- `<= 0.45`: +18
- `<= 0.60`: +6
- `<= 0.75`: -8
- `> 0.75`: -18

### 3.3 Payment History Contribution

- clean: +8
- one default: -6
- two or more defaults: -14

### 3.4 Employment Years Contribution

- `>= 2 years`: +6
- `>= 1 year`: +2
- `< 1 year`: -4

Final score is clamped to [0, 100] and mapped to `LOW`/`MEDIUM`/`HIGH` using same class bands.

## 3. Policy Decision Engine (`services/policy_engine.py`)

Policy engine combines ML score with deterministic checks.

Checks applied:

1. credit score
2. post-loan DTI
3. employment tenure
4. LTV ratio by collateral type
5. payment history
6. ML risk score

Score aggregation formula:

- start score = 100
- each `FAIL`: subtract 18
- each `WATCH`: subtract 10
- clamp result to [0, 100]

Decision bands:

- `>= 80`: `APPROVE`
- `>= 60`: `CONDITIONAL`
- `< 60`: `ESCALATE`

## 4. Financial Ratio Computation (`services/borrower_metrics.py`)

Computed values:

1. `projected_emi`
2. `current_dti`
3. `post_loan_dti`
4. `ltv_ratio`

EMI formula uses annual interest rate from settings (`DEFAULT_ANNUAL_INTEREST_RATE`, default 0.15).

## 5. LLM Model Usage In Milestone 2

### 5.1 Guardrail Classification

- model: `llama-3.1-8b-instant`
- purpose: classify finance-domain relevance
- fallback: deterministic keyword classifier

### 5.2 Extraction/Conversation Assistance

- model: `llama-3.3-70b-versatile`
- purpose: augment deterministic borrower field extraction
- fallback: deterministic extraction remains primary

### 5.3 Report Generation

- model: `llama-3.3-70b-versatile`
- fallback: deterministic report template
- consistency check ensures key profile fields match report text

### 5.4 Hindi Translation

- model: `llama-3.3-70b-versatile`
- validation: Devanagari character presence
- fallback: deterministic translation mapper

## 6. Embedding Model

RAG embeddings use:

- `chromadb.utils.embedding_functions.ONNXMiniLM_L6_V2()`

Used in both ingestion and query time retrieval.

Runtime dependency notes:

- `requirements.txt` currently does not include `sentence-transformers` or `torch`; embedding runtime is provided through Chroma's ONNX embedding utility.
- `groq` package is installed, while the implementation currently calls Groq endpoints via `httpx` in `services/groq_client.py`.
- `api.py` explicitly loads `.env` using `load_dotenv()` before settings-driven imports.

## 7. Why This Hybrid Approach Works For Milestone 2

1. deterministic checks keep underwriting logic transparent
2. ML adds risk signal and continuity from Milestone 1
3. RAG grounds responses in corpus text
4. LLMs improve natural language quality
5. deterministic fallbacks preserve functionality when LLM unavailable

## 8. Practical Validation Commands

From `MILESTONE_2/creditsense`:

```bash
python3 scripts/e2e_scenarios.py --base-url http://localhost:8010 --pretty
```

Note: script default base URL is `http://localhost:8000`; pass `--base-url` when backend runs on 8010.
