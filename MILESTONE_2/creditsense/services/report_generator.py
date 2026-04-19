from __future__ import annotations

import re
from datetime import date
from typing import Any

from agent.prompts import REPORT_PROMPT
from .groq_client import chat_completion
from .groq_pool import groq_pool


def _rupee(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"₹{value:,.0f}"


def _fmt_ratio(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def _status_icon(status: str) -> str:
    mapping = {
        "PASS": "✅ PASS",
        "WATCH": "⚠️ WATCH",
        "FAIL": "❌ FAIL",
        "N/A": "✅ N/A",
    }
    return mapping.get(status, status)


def _deterministic_report(
    profile: dict[str, Any],
    ratios: dict[str, Any],
    checks: list[dict[str, Any]],
    decision: str,
    decision_score: float,
    risk_flags: list[str],
    citations: list[dict[str, Any]],
    conversation_context: str,
) -> str:
    conditions: list[str] = []
    if any("Post-loan DTI" in flag for flag in risk_flags):
        conditions.append("Reduce loan amount or extend tenure to improve post-loan DTI.")
    if any("Credit Score" in flag for flag in risk_flags):
        conditions.append("Collect additional bureau verification and latest statement evidence.")
    if any("Payment History" in flag for flag in risk_flags):
        conditions.append("Request delinquency explanation and repayment behavior validation.")
    if not conditions and decision != "APPROVE":
        conditions.append("Underwriter review required before final disbursement.")

    metrics_rows: list[str] = []
    for check in checks:
        value = check["value"]
        if isinstance(value, float):
            value_text = f"{value:.2f}" if value <= 2 else f"{value:.0f}"
        else:
            value_text = str(value)
        metrics_rows.append(
            f"| {check['metric']} | {value_text} | {check['threshold']} | {_status_icon(check['status'])} |"
        )

    citation_lines: list[str] = []
    for item in citations[:3]:
        citation_lines.append(
            f"**[{item['title']}]:** {item['snippet']}"
        )

    condition_section = "\n".join(f"{idx + 1}. {value}" for idx, value in enumerate(conditions))
    citation_section = "\n\n".join(citation_lines) or "No regulatory citations retrieved."
    context_line = conversation_context.strip()[:260] or "Not provided"

    return f"""## Credit Assessment Report
**Borrower:** {profile.get('name', 'Unknown')} | Age: {profile.get('age', 'N/A')} | City: {profile.get('city', 'N/A')}
**Employment:** {profile.get('employment_type', 'N/A')} - {profile.get('employment_years', 'N/A')} years | Monthly Income: {_rupee(float(profile.get('monthly_income') or 0))}
**Loan Request:** {_rupee(float(profile.get('loan_amount_requested') or 0))} | Purpose: {profile.get('loan_purpose', 'N/A')} | Tenure: {profile.get('loan_tenure_months', 'N/A')} months
**Generated On:** {date.today().isoformat()}

---

### Computed Metrics
| Metric | Value | Threshold | Status |
|---|---|---|---|
{chr(10).join(metrics_rows)}

---

### Financial Ratios
- Projected EMI: {_rupee(ratios.get('projected_emi'))}
- Current DTI: {_fmt_ratio(ratios.get('current_dti'))}
- Post-loan DTI: {_fmt_ratio(ratios.get('post_loan_dti'))}
- LTV Ratio: {_fmt_ratio(ratios.get('ltv_ratio'))}

---

### Regulatory Context
{citation_section}

---

### Conversation Context
- {context_line}

---

### Decision: {decision} (Score: {decision_score:.0f}/100)

**Conditions:**
{condition_section if condition_section else 'None'}

---

### Fairness Note
Assessment uses borrower financial variables and repayment indicators only.
No protected personal attributes are used in final decisioning.

---

*Disclaimer: This is an AI-assisted assessment tool. It does not constitute a legally binding credit decision. Final approval requires authorized officer review per RBI guidelines.*
"""


def _llm_report(
    profile: dict[str, Any],
    ratios: dict[str, Any],
    checks: list[dict[str, Any]],
    decision: str,
    decision_score: float,
    risk_flags: list[str],
    citations: list[dict[str, Any]],
    conversation_context: str,
) -> str:
    payload = {
        "borrower_profile": profile,
        "computed_ratios": ratios,
        "policy_checks": checks,
        "decision": decision,
        "decision_score": decision_score,
        "risk_flags": risk_flags,
        "citations": citations[:6],
        "conversation_context": conversation_context,
    }
    return chat_completion(
        model="llama-3.3-70b-versatile",
        system_prompt=REPORT_PROMPT,
        user_prompt=str(payload),
        temperature=0.2,
        max_tokens=1200,
    )


def _normalize_digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


def _report_consistent_with_profile(report_text: str, profile: dict[str, Any]) -> bool:
    if not report_text.strip():
        return False

    expected_loan_amount = float(profile.get("loan_amount_requested") or 0)
    expected_score = int(profile.get("credit_score") or 0)

    if expected_loan_amount > 0:
        expected_loan_digits = str(int(round(expected_loan_amount)))
        line_match = re.search(r"loan\s*request[^\n\r]*", report_text, flags=re.IGNORECASE)
        scope = line_match.group(0) if line_match else report_text
        if expected_loan_digits not in _normalize_digits(scope):
            return False

    if expected_score > 0 and str(expected_score) not in _normalize_digits(report_text):
        return False

    return True


def generate_report(
    profile: dict[str, Any],
    ratios: dict[str, Any],
    checks: list[dict[str, Any]],
    decision: str,
    decision_score: float,
    risk_flags: list[str],
    citations: list[dict[str, Any]],
    conversation_context: str = "",
) -> str:
    if groq_pool.has_keys():
        try:
            llm_output = _llm_report(
                profile,
                ratios,
                checks,
                decision,
                decision_score,
                risk_flags,
                citations,
                conversation_context,
            )
            if _report_consistent_with_profile(llm_output, profile):
                return llm_output
        except Exception:
            pass

    return _deterministic_report(
        profile,
        ratios,
        checks,
        decision,
        decision_score,
        risk_flags,
        citations,
        conversation_context,
    )
