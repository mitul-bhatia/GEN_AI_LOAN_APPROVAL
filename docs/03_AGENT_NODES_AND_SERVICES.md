# CreditSense Agent Nodes and Services

> Refreshed from current code scan on 2026-04-19.

## 1. LangGraph Nodes Overview

All nodes are implemented in `agent/nodes.py` and wired in `agent/graph.py`.

| Node | Primary Purpose | Main Outputs |
|---|---|---|
| `guardrail_node` | Safety and domain gating | `is_finance_query`, `assistant_reply`, `guardrail_reason` |
| `conversation_node` | Intake extraction and response handling | `collected`, `missing_fields`, `profile_complete`, `assistant_reply` |
| `rag_retriever_node` | Regulatory retrieval | `rag_chunks`, `citations`, `conversation_context` |
| `policy_node` | Risk scoring and policy checks | `policy_checks`, `risk_flags`, `decision`, `decision_score` |
| `report_node` | Report generation | `report_en`, `assistant_reply` |
| `translate_node` | Hindi translation | `report_hi` |

## 2. Node 1: Guardrail Node

### 2.1 What It Does

1. Friendly greeting detection (special welcome path)
2. Safety policy block checks (fraud, evasion, abuse, jailbreak attempts)
3. Continuation detection during active intake
4. Finance-domain classification

### 2.2 Important Behaviors

- Unsafe content returns immediate safe refusal response
- Non-finance prompts return domain-limited guidance message
- Finance prompts proceed to conversation node

### 2.3 Implementation Details

Guardrail service: `services/guardrail.py`

- Deterministic safety regex checks
- Keyword finance classifier fallback
- Groq LLM classifier for finance domain when keys are present

## 3. Node 2: Conversation Node

### 3.1 What It Does

1. Reads latest user message
2. Extracts borrower updates
3. Merges into collected profile
4. Computes missing fields
5. Computes ratios immediately
6. Chooses reply strategy:
   - report trigger acknowledgement
   - missing fields prompt
   - financial Q/A using RAG-backed chat response

### 3.2 Extraction Strategy

Implemented in `services/profile_parser.py`:

- deterministic regex extraction first
- LLM extraction second for missing detections
- normalization of all numeric/string fields

### 3.3 Report Trigger Detection

Report intent is pattern-based (`is_report_request`).
Report chain runs only when profile complete and report requested.

## 4. Node 3: RAG Retriever Node

### 4.1 What It Does

- Builds profile-aware retrieval query
- Retrieves top chunks from Chroma
- Creates citation list from retrieved chunks

### 4.2 Source Modules

- `services/retriever.py`
- `services/settings.py`

## 5. Node 4: Policy Node

### 5.1 What It Does

1. Generates ML risk score (`services/ml_adapter.py`)
2. Runs deterministic policy checks (`services/policy_engine.py`)
3. Produces decision class and score

### 5.2 Decision Classes

- `APPROVE`
- `CONDITIONAL`
- `ESCALATE`

## 6. Node 5: Report Node

### 6.1 What It Does

- Creates English credit assessment report
- Uses LLM report generation when available
- Validates consistency with borrower profile
- Falls back to deterministic template if needed

### 6.2 Source Module

- `services/report_generator.py`

## 7. Node 6: Translate Node

### 7.1 What It Does

- Translates `report_en` into Hindi
- Verifies Devanagari presence for LLM output
- Uses deterministic mapper fallback when LLM unavailable/fails

### 7.2 Source Module

- `services/translator.py`

## 8. Service Layer Inventory

| Service | Role |
|---|---|
| `settings.py` | Central configuration resolution |
| `backend_client.py` | Streamlit to FastAPI HTTP integration |
| `borrower_metrics.py` | EMI, DTI, LTV calculations |
| `groq_pool.py` | Thread-safe key rotation |
| `groq_client.py` | Groq API wrapper with retries |
| `guardrail.py` | Safety/domain checks and continuation logic |
| `profile_parser.py` | Intake field extraction and questioning logic |
| `ml_adapter.py` | Trained model loading + fallback heuristic score |
| `policy_engine.py` | Rule-based underwriting checks and score bands |
| `retriever.py` | Embedding-based retrieval from Chroma |
| `report_generator.py` | English report generation |
| `translator.py` | Hindi translation engine |
| `pdf_exporter.py` | English/Hindi PDF bytes generation |

## 9. Financial Metrics Logic (`borrower_metrics.py`)

Computed values:

1. `projected_emi`
2. `current_dti`
3. `post_loan_dti`
4. `ltv_ratio`

EMI uses standard amortization formula with configurable annual rate.

## 10. ML Adapter Logic (`ml_adapter.py`)

Runtime order:

1. Try model at `ML_MODEL_PATH`
2. Fallback to `ML_MODEL_FALLBACK_PATH`
3. If loading/scoring fails, use heuristic score

Risk class mapping:

- `>= 75`: `LOW`
- `>= 55`: `MEDIUM`
- `< 55`: `HIGH`

## 11. Policy Engine Logic (`policy_engine.py`)

Checks include:

1. credit score
2. post-loan DTI
3. employment tenure
4. collateral-specific LTV
5. payment history
6. ML risk score

Score aggregation:

- start at 100
- `FAIL`: -18
- `WATCH`: -10
- clamp to [0, 100]

Decision bands:

- `>= 80`: `APPROVE`
- `>= 60`: `CONDITIONAL`
- `< 60`: `ESCALATE`

## 12. Report and Translation Fallback Guarantees

Implemented fallback guarantees ensure output availability:

1. report generation falls back to deterministic markdown
2. translation falls back to deterministic Hindi mapping
3. UI can still export PDF from fallback content

## 13. Execution Trace

State carries `trace` entries (rolling window) to provide node-level execution breadcrumbs for debugging and explainability.

## 14. Runtime Bootstrap Note

`api.py` calls `load_dotenv()` before importing settings-dependent modules so `.env` values are available during service initialization.
