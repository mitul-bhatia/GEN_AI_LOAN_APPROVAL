"""
Heuristic Risk Scorer
---------------------
Computes a borrower risk score using rule-based weighted scoring
on credit score, DTI, payment history, and employment tenure.

This is a deterministic heuristic — not a trained ML model.
"""

from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def heuristic_risk_score(profile: dict[str, Any], ratios: dict[str, Any]) -> tuple[float, str]:
    """Score a borrower using weighted rule-based heuristics.

    Returns (score_out_of_100, risk_class) where risk_class is LOW/MEDIUM/HIGH.
    """
    score = 50.0

    credit_score = float(profile.get("credit_score") or 0)
    post_loan_dti = ratios.get("post_loan_dti")
    payment_history = str(profile.get("payment_history") or "").lower()
    employment_years = float(profile.get("employment_years") or 0)

    # --- Credit Score Band ---
    if credit_score >= 750:
        score += 25
    elif credit_score >= 680:
        score += 12
    elif credit_score >= 600:
        score += 3
    else:
        score -= 15

    # --- Post-loan DTI Band ---
    if post_loan_dti is not None:
        if post_loan_dti <= 0.45:
            score += 18
        elif post_loan_dti <= 0.60:
            score += 6
        elif post_loan_dti <= 0.75:
            score -= 8
        else:
            score -= 18

    # --- Payment History ---
    if "clean" in payment_history:
        score += 8
    elif "1" in payment_history:
        score -= 6
    elif "2+" in payment_history or "multiple" in payment_history:
        score -= 14

    # --- Employment Stability ---
    if employment_years >= 2:
        score += 6
    elif employment_years >= 1:
        score += 2
    else:
        score -= 4

    final_score = _clamp(score)
    if final_score >= 75:
        return final_score, "LOW"
    if final_score >= 55:
        return final_score, "MEDIUM"
    return final_score, "HIGH"


class RiskScorer:
    """Stateless heuristic risk scorer for borrower profiles."""

    def score(self, profile: dict[str, Any], ratios: dict[str, Any]) -> tuple[float, str]:
        return heuristic_risk_score(profile, ratios)


risk_scorer = RiskScorer()
