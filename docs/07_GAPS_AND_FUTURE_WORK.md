# CreditSense Gaps and Future Work

> Refreshed from current code scan on 2026-04-19.

## 1. Current-State Assessment

Milestone 2 is functionally complete for local conversational underwriting workflow.

Implemented and working:

1. multi-turn intake
2. guardrails
3. RAG retrieval
4. rule-based decisioning
5. report generation
6. Hindi translation
7. PDF export

Remaining gaps are primarily around production hardening, evaluation depth, and scale.

## 2. Known Gaps (As Built)

## 2.1 Product and UX Gaps

1. No multi-user authentication layer
2. No persistent conversation history store across sessions
3. UI is strong for desktop, but not deeply optimized for mobile workflows
4. No explicit admin/debug panel in UI for trace inspection

## 2.2 Evaluation and Testing Gaps

1. E2E scenario script exists, but no CI pipeline wiring
2. No unit-test suite for parser/policy/retriever modules
3. No regression benchmark set for response quality over time
4. No formal hallucination/citation quality scoring harness

## 2.3 Retrieval and Knowledge Gaps

1. Retrieval is top-k similarity based; no reranker stage
2. No periodic automatic corpus refresh scheduler
3. No metadata-level filtering UI for priority/source controls
4. No explicit citation-to-policy check linker (auditor module)

## 2.4 Security and Operations Gaps

1. No backend auth token enforcement on endpoints
2. No per-user rate limiting middleware
3. No structured external logging sink by default
4. Secrets rely on env management without dedicated secret vault integration in local setup

## 2.5 Deployment Readiness Gaps

1. Basic deployment manifests exist (`Procfile`, `render.yaml`, `runtime.txt`), but no full multi-environment release workflow yet
2. No health dashboard/alerting integration by default
3. No staged rollout/rollback playbook documented yet

## 3. Technical Debt Items

1. `app.py` contains substantial inline CSS and UI logic; could be modularized
2. Parser logic in `services/profile_parser.py` is large and can be split by field groups
3. API and orchestration are tightly coupled in same codebase; service boundary can be hardened for scale
4. Current retrieval strategy does not include hybrid lexical+dense retrieval

## 4. Risk Summary

| Area | Risk Level | Why |
|---|---|---|
| Core correctness | Medium | Deterministic checks are strong, but parser edge cases always evolve |
| Explainability | Medium-Low | Reports include checks and citations, but no formal citation auditor |
| Scalability | Medium-High | Local-first architecture and no queueing/rate control |
| Compliance ops | Medium | Guardrails exist, but no enterprise audit pipeline yet |

## 5. Prioritized Roadmap

## 5.1 Near-Term (1 to 2 weeks)

1. Add pytest unit tests for `borrower_metrics`, `policy_engine`, `profile_parser`
2. Add CI workflow for lint + tests + scenario smoke test
3. Add backend rate limiting and request logging middleware
4. Add minimal auth for write/agent endpoints

## 5.2 Mid-Term (2 to 6 weeks)

1. Add retrieval reranking and citation confidence scoring
2. Add structured trace visualization endpoint/UI panel
3. Add persistent conversation storage (SQLite/Postgres)
4. Add release checklist and environment profiles (dev/stage/prod)

## 5.3 Long-Term (6+ weeks)

1. Introduce policy versioning and explainability snapshots
2. Build reviewer workflow for human-in-the-loop overrides
3. Add multilingual expansion beyond English/Hindi
4. Add portfolio analytics and model monitoring dashboards

## 6. Suggested Next Research Topics

1. fairness stress testing on synthetic borrower cohorts
2. groundedness scoring for report text vs retrieved chunks
3. policy simulation mode for "what-if" borrower changes
4. domain-specific small model fine-tuning for parser robustness
