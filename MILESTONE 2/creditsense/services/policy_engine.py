from __future__ import annotations

from typing import Any


BANK_CUTOFFS = {
    "credit_score_pass": 750,
    "credit_score_watch": 680,
    "credit_score_fail": 600,
    "post_loan_dti_pass": 0.45,
    "post_loan_dti_watch": 0.60,
    "post_loan_dti_fail": 0.75,
    "employment_years_pass": 2.0,
    "employment_years_watch": 1.0,
    "ltv_property_max": 0.80,
    "ltv_gold_max": 0.75,
    "ltv_fd_max": 0.90,
    "ltv_vehicle_max": 0.85,
}


def _status_from_threshold(value: float, pass_th: float, watch_th: float, fail_th: float, inverse: bool = False) -> str:
    if value is None:
        return "N/A"
    if not inverse:
        if value >= pass_th:
            return "PASS"
        if value >= watch_th:
            return "WATCH"
        if value >= fail_th:
            return "FAIL"
        return "FAIL"

    if value <= pass_th:
        return "PASS"
    if value <= watch_th:
        return "WATCH"
    if value <= fail_th:
        return "FAIL"
    return "FAIL"


def _ltv_status(collateral_type: str, ltv_ratio: float | None) -> tuple[str, str]:
    if collateral_type.lower() in {"none", "", "na", "n/a"}:
        return "N/A", "Unsecured"
    if ltv_ratio is None:
        return "FAIL", "Collateral value missing"

    ctype = collateral_type.lower()
    if "property" in ctype:
        threshold = BANK_CUTOFFS["ltv_property_max"]
    elif "gold" in ctype:
        threshold = BANK_CUTOFFS["ltv_gold_max"]
    elif "fixed" in ctype:
        threshold = BANK_CUTOFFS["ltv_fd_max"]
    else:
        threshold = BANK_CUTOFFS["ltv_vehicle_max"]

    if ltv_ratio <= threshold:
        return "PASS", f"<= {threshold:.2f}"
    if ltv_ratio <= threshold + 0.05:
        return "WATCH", f"~ {threshold:.2f}"
    return "FAIL", f"> {threshold:.2f}"


def evaluate_policy(
    profile: dict[str, Any],
    ratios: dict[str, Any],
    ml_risk_score: float,
) -> tuple[list[dict[str, Any]], list[str], str, float]:
    checks: list[dict[str, Any]] = []
    risk_flags: list[str] = []

    credit_score = float(profile.get("credit_score") or 0)
    post_loan_dti = ratios.get("post_loan_dti")
    employment_years = float(profile.get("employment_years") or 0)
    payment_history = str(profile.get("payment_history") or "")
    collateral_type = str(profile.get("collateral_type") or "None")
    ltv_ratio = ratios.get("ltv_ratio")

    credit_status = _status_from_threshold(
        credit_score,
        BANK_CUTOFFS["credit_score_pass"],
        BANK_CUTOFFS["credit_score_watch"],
        BANK_CUTOFFS["credit_score_fail"],
    )
    checks.append(
        {
            "metric": "Credit Score",
            "value": credit_score,
            "threshold": f">= {BANK_CUTOFFS['credit_score_watch']}",
            "status": credit_status,
        }
    )

    dti_status = _status_from_threshold(
        float(post_loan_dti) if post_loan_dti is not None else None,
        BANK_CUTOFFS["post_loan_dti_pass"],
        BANK_CUTOFFS["post_loan_dti_watch"],
        BANK_CUTOFFS["post_loan_dti_fail"],
        inverse=True,
    )
    checks.append(
        {
            "metric": "Post-loan DTI",
            "value": post_loan_dti,
            "threshold": f"<= {BANK_CUTOFFS['post_loan_dti_watch']:.2f}",
            "status": dti_status,
        }
    )

    tenure_status = "PASS"
    if employment_years < BANK_CUTOFFS["employment_years_watch"]:
        tenure_status = "FAIL"
    elif employment_years < BANK_CUTOFFS["employment_years_pass"]:
        tenure_status = "WATCH"

    checks.append(
        {
            "metric": "Employment Tenure",
            "value": employment_years,
            "threshold": f">= {BANK_CUTOFFS['employment_years_pass']:.1f} years",
            "status": tenure_status,
        }
    )

    ltv_status, ltv_threshold_text = _ltv_status(collateral_type, ltv_ratio)
    checks.append(
        {
            "metric": "LTV Ratio",
            "value": ltv_ratio,
            "threshold": ltv_threshold_text,
            "status": ltv_status,
        }
    )

    history_status = "PASS"
    low = payment_history.lower()
    if "2+" in low or "multiple" in low:
        history_status = "FAIL"
    elif "1" in low:
        history_status = "WATCH"
    checks.append(
        {
            "metric": "Payment History",
            "value": payment_history,
            "threshold": "Clean preferred",
            "status": history_status,
        }
    )

    ml_status = "PASS" if ml_risk_score >= 70 else "WATCH" if ml_risk_score >= 55 else "FAIL"
    checks.append(
        {
            "metric": "ML Risk Score",
            "value": round(ml_risk_score, 2),
            "threshold": ">= 70",
            "status": ml_status,
        }
    )

    score = 100.0
    for check in checks:
        status = check["status"]
        if status == "FAIL":
            score -= 18
            risk_flags.append(f"{check['metric']} failed")
        elif status == "WATCH":
            score -= 10
            risk_flags.append(f"{check['metric']} needs review")

    score = max(0.0, min(100.0, score))

    if score >= 80:
        decision = "APPROVE"
    elif score >= 60:
        decision = "CONDITIONAL"
    else:
        decision = "ESCALATE"

    return checks, risk_flags, decision, round(score, 2)
