# CreditSense — Model & ML Documentation

> **Machine learning models, LLM assignments, scoring logic, and evaluation**

---

## 1. ML Architecture Overview

CreditSense uses a **hybrid ML + deterministic** approach to credit risk assessment:

```
┌─────────────────────────────────────────────────────────────┐
│                    ML SCORING LAYER                          │
│                                                             │
│  ┌──────────────────┐     ┌──────────────────────────────┐  │
│  │  Milestone 1     │     │  Heuristic Fallback          │  │
│  │  Trained Model   │     │  (Always Available)          │  │
│  │                  │     │                              │  │
│  │  - Logistic Reg  │     │  Base: 50                    │  │
│  │  - predict_proba │     │  Credit score: +25 to -15    │  │
│  │  - 9 features    │     │  DTI: +18 to -18             │  │
│  │  - model.pkl     │     │  Payment: +8 to -14          │  │
│  │                  │     │  Employment: +6 to -4         │  │
│  │  Priority: 1st   │     │  Range: [0, 100]             │  │
│  └──────┬───────────┘     └──────────┬───────────────────┘  │
│         │                            │                      │
│         └────────────┬───────────────┘                      │
│                      ▼                                      │
│              Risk Score (0-100)                              │
│              ≥75 = LOW | ≥55 = MEDIUM | <55 = HIGH          │
│                                                             │
│              Fed into Policy Engine as one of 6 checks      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Milestone 1 Trained Model

### 2.1 Model Type

| Property | Value |
|---|---|
| **Algorithm** | Logistic Regression (primary), with other classifiers explored |
| **Framework** | scikit-learn |
| **Serialization** | `joblib` (`.pkl` format) |
| **Location** | `MILESTONE 1/models/logistic_regression.pkl` |
| **Fallback Location** | `creditsense/ml_model/model.pkl` |

### 2.2 Input Features (9 Dimensions)

```python
feature_vector = {
    "age":                    float,   # Borrower age
    "monthly_income":         float,   # Monthly income in INR
    "credit_score":           float,   # CIBIL/credit score (300-900)
    "existing_emi_monthly":   float,   # Current EMI obligations
    "loan_amount_requested":  float,   # Requested loan amount
    "loan_tenure_months":     float,   # Loan tenure in months
    "employment_years":       float,   # Years of employment
    "post_loan_dti":          float,   # Post-loan debt-to-income ratio
    "ltv_ratio":              float,   # Loan-to-value ratio
}
```

### 2.3 Scoring Logic

```python
# If model has predict_proba():
probs = model.predict_proba(features)
safe_prob = probs[0][-1]      # Probability of "safe/approved" class
score = clamp(safe_prob * 100, 0, 100)

# If model has only predict():
pred = model.predict(features)[0]
score = clamp(pred * 100, 0, 100)
```

### 2.4 Risk Classification

| Score Range | Risk Class | Meaning |
|---|---|---|
| ≥ 75 | **LOW** | Low default risk — strong candidate |
| 55 – 74 | **MEDIUM** | Moderate risk — conditional lending |
| < 55 | **HIGH** | Elevated risk — escalation recommended |

---

## 3. Heuristic Fallback Model

When the trained model is unavailable (file not found, load error, or feature mismatch), the system uses a hand-tuned heuristic:

### 3.1 Scoring Rules

```
Base Score: 50.0

Credit Score Impact:
  ≥750: +25    ≥680: +12    ≥600: +3    <600: -15

Post-loan DTI Impact:
  ≤0.45: +18   ≤0.60: +6   ≤0.75: -8   >0.75: -18

Payment History Impact:
  Clean: +8    1 default: -6    2+ defaults: -14

Employment Years:
  ≥2 years: +6    ≥1 year: +2    <1 year: -4

Final: clamp(score, 0, 100)
```

### 3.2 Design Rationale

- Mirrors the policy engine's cutoff thresholds
- Credit score and DTI carry the highest weight (aligned with RBI guidelines)
- Always produces a numeric score even without external dependencies
- Acts as a safety net for deployments where the trained model is missing

---

## 4. LLM Model Assignments

CreditSense uses **Groq API** to access Llama 3 family models:

### 4.1 Model-to-Task Mapping

| Task | Model | Why This Model | Temperature | Max Tokens |
|---|---|---|---|---|
| **Guardrail Classification** | `llama-3.1-8b-instant` | Fast, cheap, binary classification | 0.0 | 120 |
| **Profile Field Extraction** | `llama-3.3-70b-versatile` | Complex entity extraction requires reasoning | 0.0 | 350 |
| **Report Generation** | `llama-3.3-70b-versatile` | Structured, audit-quality output | 0.2 | 1,200 |
| **Hindi Translation** | `llama-3.3-70b-versatile` | Script conversion + financial terminology | 0.1 | 1,600 |

### 4.2 Groq API Configuration

| Property | Value |
|---|---|
| **API Endpoint** | `https://api.groq.com/openai/v1/chat/completions` |
| **Key Management** | Round-robin pool of up to 5 keys |
| **Rate Limit Handling** | 429 → rotate key and retry |
| **Timeout** | 45 seconds per request |
| **Retry Strategy** | One attempt per key in the pool |
| **Response Format** | JSON mode for guardrail and extraction; text mode for report and translation |

### 4.3 LLM Prompt Architecture

All prompts are centralized in `agent/prompts.py`:

| Prompt | Purpose | Key Instructions |
|---|---|---|
| `GUARDRAIL_PROMPT` | Finance domain classification | Return strict JSON `{is_finance_query, reason}` |
| `CONVERSATION_EXTRACTION_PROMPT` | Borrower field extraction | "Do NOT map existing EMI to loan_amount_requested" |
| `REPORT_PROMPT` | Credit report synthesis | "Concise, factual, and audit-friendly" |
| `TRANSLATE_PROMPT` | Hindi translation | "Keep names, numbers, abbreviations in English" |

---

## 5. Embedding Model

| Property | Value |
|---|---|
| **Model** | `all-MiniLM-L6-v2` |
| **Source** | Sentence Transformers (Hugging Face) |
| **Dimensions** | 384 |
| **Normalization** | L2-normalized (cosine similarity) |
| **Size** | ~80 MB |
| **Inference** | CPU-only, ~14K sentences/sec |
| **Used For** | Document chunk embedding + query embedding |
| **Loaded Once** | `@lru_cache(maxsize=1)` — singleton pattern |

---

## 6. Combined Scoring Flow

```
Borrower Profile + Computed Ratios
        │
        ├──▸ ML Model Score (0-100)
        │    └── Converted to policy check: ≥70 PASS, ≥55 WATCH, <55 FAIL
        │
        ├──▸ Credit Score Check
        │    └── ≥750 PASS, ≥680 WATCH, ≥600 FAIL
        │
        ├──▸ Post-loan DTI Check
        │    └── ≤0.45 PASS, ≤0.60 WATCH, ≤0.75 FAIL
        │
        ├──▸ Employment Tenure Check
        │    └── ≥2yr PASS, ≥1yr WATCH, <1yr FAIL
        │
        ├──▸ LTV Ratio Check (collateral-specific)
        │    └── Property ≤0.80, Gold ≤0.75, FD ≤0.90, Vehicle ≤0.85
        │
        └──▸ Payment History Check
             └── Clean PASS, 1 default WATCH, 2+ FAIL

Combined Score = 100 - (18 × FAIL_count) - (10 × WATCH_count)
Clamped to [0, 100]

≥80 → APPROVE    60-79 → CONDITIONAL    <60 → ESCALATE
```

---

## 7. Model Evaluation Considerations

### 7.1 What Is Tested

The `scripts/e2e_scenarios.py` provides 5 automated end-to-end test scenarios:

| Scenario | Expected Decision | Tests |
|---|---|---|
| Salaried Personal Loan (strong profile) | Likely APPROVE | Standard case with clean history and good score |
| Self-Employed Secured (strong + collateral) | Likely APPROVE | Collateral-backed, high income, good score |
| Borderline Credit Watch (mixed signals) | Likely CONDITIONAL | Score near threshold, 1 default, vehicle loan |
| High Risk Escalate (weak profile) | Likely ESCALATE | Low score, gig worker, 2+ defaults |
| Education Loan Conditional (moderate) | Likely CONDITIONAL | FD-backed, moderate score, 1 existing loan |

### 7.2 Validation Checks

- **Report consistency:** Generated report must contain correct loan amount and credit score
- **Devanagari validation:** Hindi translation must contain Unicode Devanagari characters
- **RAG coverage:** At least 1 citation must be present in the final report
- **End-to-end flow:** API health → state init → multi-turn turns → report generation

---

*CreditSense v2.0 — Model & ML Documentation | Last Updated: April 2026*
