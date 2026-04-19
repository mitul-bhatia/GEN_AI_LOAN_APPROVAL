from __future__ import annotations

from typing import Any


def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if principal <= 0 or annual_rate <= 0 or tenure_months <= 0:
        return 0.0
    monthly_rate = annual_rate / 12
    factor = (1 + monthly_rate) ** tenure_months
    return principal * monthly_rate * factor / (factor - 1)


def compute_ratios(profile: dict[str, Any], annual_rate: float = 0.15) -> dict[str, Any]:
    monthly_income = float(profile.get("monthly_income") or 0)
    existing_emi = float(profile.get("existing_emi_monthly") or 0)
    loan_amount = float(profile.get("loan_amount_requested") or 0)
    tenure_months = int(profile.get("loan_tenure_months") or 0)
    collateral_value = float(profile.get("collateral_value") or 0)

    projected_emi = compute_emi(loan_amount, annual_rate, tenure_months)
    total_emi = existing_emi + projected_emi

    current_dti = existing_emi / monthly_income if monthly_income > 0 else None
    post_loan_dti = total_emi / monthly_income if monthly_income > 0 else None

    ltv_ratio = None
    if collateral_value > 0:
        ltv_ratio = loan_amount / collateral_value

    return {
        "projected_emi": round(projected_emi, 2),
        "current_dti": round(current_dti, 4) if current_dti is not None else None,
        "post_loan_dti": round(post_loan_dti, 4) if post_loan_dti is not None else None,
        "ltv_ratio": round(ltv_ratio, 4) if ltv_ratio is not None else None,
    }
