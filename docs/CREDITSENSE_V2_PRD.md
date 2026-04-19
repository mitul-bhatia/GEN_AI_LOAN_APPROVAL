# CreditSense V2 PRD (Milestone 2 As-Built)

> Refreshed from current code scan on 2026-04-19.

## 1. Document Purpose

This PRD captures Milestone 2 requirements as implemented in code, including what is complete, partial, and pending.

Implementation baseline:

- `MILESTONE_2/creditsense/`

## 2. Product Goal

Build a conversational credit assessment assistant that can:

1. collect borrower profile details naturally
2. evaluate risk using deterministic + ML logic
3. ground answers in regulatory corpus via retrieval
4. produce structured report outputs
5. provide bilingual (English/Hindi) report artifacts

## 3. Primary Users

1. loan officers
2. underwriting analysts
3. compliance and review stakeholders
4. academic evaluators for milestone demonstration

## 4. Functional Requirements and Status

| Requirement | Status | Implementation Reference |
|---|---|---|
| Conversational borrower intake | Complete | `agent/nodes.py`, `services/profile_parser.py` |
| Safety/domain guardrails | Complete | `services/guardrail.py` |
| Form-based parameter seeding | Complete | `api.py`, `app.py` |
| Financial ratio computation | Complete | `services/borrower_metrics.py` |
| Risk signal heuristic fallback | Complete | `services/risk_scorer.py` |
| Deterministic underwriting checks | Complete | `services/policy_engine.py` |
| RAG retrieval from local corpus | Complete | `scripts/ingest.py`, `services/retriever.py` |
| English report generation | Complete | `services/report_generator.py` |
| Hindi report generation | Complete | `services/translator.py` |
| English/Hindi PDF download | Complete | `services/pdf_exporter.py`, `app.py` |
| Public API for agent operations | Complete | `api.py` |
| Deployment manifest files | Complete | `Procfile`, `render.yaml`, `runtime.txt` |
| Automated CI testing workflow | Pending | not yet in milestone folder |
| Auth/rate-limited production API | Pending | not yet implemented |

## 5. Non-Functional Requirements and Status

| NFR | Status | Notes |
|---|---|---|
| Explainability | Partial-Complete | policy checks and citations are included; no formal citation auditor yet |
| Reliability under missing LLM | Complete | deterministic fallback paths implemented |
| Configurability | Complete | env-based settings for model/path/ports |
| Local reproducibility | Complete | script-based startup and ingestion flow |
| Production hardening | Partial | auth, rate limits, observability are still open |

## 6. System Workflow Requirement

Required workflow:

1. collect borrower details
2. determine profile completeness
3. process report request
4. retrieve evidence
5. score and decide
6. generate reports and downloads

Status: complete and operational through graph routing.

## 7. Data Inputs

## 7.1 Borrower Inputs (15 fields)

1. name
2. age
3. employment_type
4. monthly_income
5. employment_years
6. credit_score
7. existing_loan_count
8. existing_emi_monthly
9. payment_history
10. loan_amount_requested
11. loan_purpose
12. loan_tenure_months
13. collateral_type
14. collateral_value
15. city

## 7.2 Knowledge Inputs

- regulatory corpus from `RAG files/` (or configured docs path)

## 8. Outputs

1. conversational guidance replies
2. decision class (`APPROVE` / `CONDITIONAL` / `ESCALATE`)
3. decision score
4. policy check table data
5. citations and retrieved chunk context
6. English report markdown
7. Hindi report text
8. English and Hindi downloadable PDFs

## 9. API Contract Requirement

Required API endpoints are all implemented:

1. `GET /api/v1/health`
2. `GET /api/v1/agent/state/initial`
3. `POST /api/v1/agent/turn`
4. `POST /api/v1/agent/seed-parameters`
5. `POST /api/v1/ingest`

## 10. Runtime Requirement

Target command paths are implemented as scripts:

1. `bash scripts/run_backend.sh`
2. `bash scripts/run_streamlit.sh`
3. `python3 scripts/ingest.py --source-dir "../../RAG files"`

## 11. Acceptance Criteria (Milestone 2)

Milestone accepted when:

1. app starts with backend + frontend commands
2. borrower profile can be completed via form/chat
3. report can be generated after profile completion
4. report includes decision and policy checks
5. citations are present when corpus indexed
6. Hindi output is generated
7. both PDFs are downloadable

Status: satisfied in current implementation.

## 12. Out-of-Scope for This Milestone

1. enterprise-grade auth and IAM
2. centralized logging/monitoring stack
3. production autoscaling and queueing
4. advanced citation quality scoring framework

## 13. Post-Milestone Priorities

1. test automation and CI
2. auth + rate limiting
3. retrieval reranking and citation auditing
4. deployment hardening and observability
