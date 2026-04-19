from __future__ import annotations

from typing import Any, TypedDict


REQUIRED_FIELDS = [
    "name",
    "age",
    "employment_type",
    "monthly_income",
    "employment_years",
    "credit_score",
    "existing_loan_count",
    "existing_emi_monthly",
    "payment_history",
    "loan_amount_requested",
    "loan_purpose",
    "loan_tenure_months",
    "collateral_type",
    "collateral_value",
    "city",
]


class AgentState(TypedDict, total=False):
    messages: list[dict[str, str]]

    collected: dict[str, Any]
    missing_fields: list[str]
    profile_complete: bool

    is_finance_query: bool
    guardrail_reason: str

    borrower_profile: dict[str, Any]
    computed_ratios: dict[str, Any]
    ml_risk_score: float
    ml_risk_class: str

    rag_chunks: list[dict[str, Any]]
    citations: list[dict[str, Any]]

    policy_checks: list[dict[str, Any]]
    risk_flags: list[str]
    decision: str
    decision_score: float

    report_en: str
    report_hi: str
    conversation_context: str
    report_requested: bool

    assistant_reply: str
    trace: list[str]


def initial_collected() -> dict[str, Any]:
    return {
        "name": "",
        "age": None,
        "employment_type": "",
        "monthly_income": None,
        "employment_years": None,
        "credit_score": None,
        "existing_loan_count": None,
        "existing_emi_monthly": None,
        "payment_history": "",
        "loan_amount_requested": None,
        "loan_purpose": "",
        "loan_tenure_months": None,
        "collateral_type": "",
        "collateral_value": None,
        "city": "",
    }


def make_initial_state() -> AgentState:
    return AgentState(
        messages=[],
        collected=initial_collected(),
        missing_fields=REQUIRED_FIELDS.copy(),
        profile_complete=False,
        is_finance_query=True,
        guardrail_reason="",
        borrower_profile={},
        computed_ratios={},
        ml_risk_score=0.0,
        ml_risk_class="",
        rag_chunks=[],
        citations=[],
        policy_checks=[],
        risk_flags=[],
        decision="",
        decision_score=0.0,
        report_en="",
        report_hi="",
        conversation_context="",
        report_requested=False,
        assistant_reply="",
        trace=[],
    )
