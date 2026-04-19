from __future__ import annotations

import json
from typing import Any

from .state import AgentState
from .prompts import CHAT_RESPONSE_PROMPT
from services.borrower_metrics import compute_ratios
from services.groq_client import chat_completion
from services.groq_pool import groq_pool
from services.guardrail import (
    check_finance_query,
    check_project_guardrails,
    should_treat_as_continuation,
)
from services.ml_adapter import risk_model
from services.policy_engine import evaluate_policy
from services.profile_parser import (
    build_follow_up_reply,
    extract_profile_updates,
    get_missing_fields,
    is_report_request,
    merge_collected,
)
from services.report_generator import generate_report
from services.retriever import build_query_from_profile, retriever
from services.settings import settings
from services.translator import translate_to_hindi


def _latest_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def _add_trace(state: AgentState, line: str) -> list[str]:
    trace = list(state.get("trace") or [])
    trace.append(line)
    return trace[-30:]


def _has_collected_progress(collected: dict[str, Any]) -> bool:
    for value in collected.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _merge(state: AgentState, updates: dict[str, Any]) -> AgentState:
    """Return a new state dict that is the full state with updates applied."""
    out: AgentState = dict(state)  # type: ignore[assignment]
    for key, value in updates.items():
        out[key] = value  # type: ignore[literal-required]
    return out


def _conversation_context(state: AgentState, max_user_turns: int = 6) -> str:
    messages = list(state.get("messages") or [])
    user_turns: list[str] = []
    for message in messages:
        if message.get("role") != "user":
            continue
        content = str(message.get("content") or "").strip()
        if content:
            user_turns.append(content)

    if not user_turns:
        return ""

    return " | ".join(user_turns[-max_user_turns:])


# ─────────────────────────────────────────────────────────────────────────────
# RAG-POWERED LLM CHAT RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

def _build_rag_query(
    latest_message: str,
    profile: dict[str, Any],
    ratios: dict[str, Any],
) -> str:
    """Build a query that combines the user's question with profile context."""
    parts = [latest_message]
    if profile.get("loan_purpose"):
        parts.append(f"loan purpose {profile['loan_purpose']}")
    if profile.get("employment_type"):
        parts.append(f"employment {profile['employment_type']}")
    if profile.get("collateral_type"):
        parts.append(f"collateral {profile['collateral_type']}")
    parts.append("RBI NBFC underwriting fair practices lending")
    return " ".join(parts)


def _format_profile_for_llm(profile: dict[str, Any], ratios: dict[str, Any]) -> str:
    """Format borrower profile and ratios as readable text for the LLM."""
    lines: list[str] = []
    field_labels = {
        "name": "Name", "age": "Age", "city": "City",
        "employment_type": "Employment", "employment_years": "Years Employed",
        "monthly_income": "Monthly Income (INR)", "credit_score": "Credit Score",
        "existing_loan_count": "Existing Loans", "existing_emi_monthly": "Existing EMI (INR)",
        "payment_history": "Payment History",
        "loan_amount_requested": "Loan Requested (INR)", "loan_purpose": "Loan Purpose",
        "loan_tenure_months": "Loan Tenure (Months)",
        "collateral_type": "Collateral Type", "collateral_value": "Collateral Value (INR)",
    }
    for field, label in field_labels.items():
        val = profile.get(field)
        if val is not None and str(val).strip():
            if isinstance(val, float) and val == int(val):
                lines.append(f"- {label}: {int(val)}")
            else:
                lines.append(f"- {label}: {val}")

    if ratios:
        lines.append("")
        lines.append("**Computed Ratios:**")
        if ratios.get("projected_emi") is not None:
            lines.append(f"- Projected EMI: ₹{ratios['projected_emi']:,.0f}")
        if ratios.get("current_dti") is not None:
            lines.append(f"- Current DTI: {ratios['current_dti']:.2f}")
        if ratios.get("post_loan_dti") is not None:
            lines.append(f"- Post-loan DTI: {ratios['post_loan_dti']:.2f}")
        if ratios.get("ltv_ratio") is not None:
            lines.append(f"- LTV Ratio: {ratios['ltv_ratio']:.2f}")

    return "\n".join(lines) if lines else "No profile data available yet."


def _format_rag_context(rag_chunks: list[dict[str, Any]]) -> str:
    """Format retrieved RAG chunks as context for the LLM."""
    if not rag_chunks:
        return "No regulatory documents retrieved."

    lines: list[str] = []
    for idx, chunk in enumerate(rag_chunks[:6], 1):
        source = chunk.get("source", "unknown")
        text = chunk.get("text", "").strip()
        if text:
            lines.append(f"[Source {idx}: {source}]\n{text}")

    return "\n\n".join(lines) if lines else "No regulatory documents retrieved."


def _llm_chat_reply(
    latest_message: str,
    profile: dict[str, Any],
    ratios: dict[str, Any],
    missing_fields: list[str] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Generate a grounded chat reply using RAG retrieval + Groq LLM.
    Returns (reply_text, citations).
    """
    # 1. Retrieve RAG context
    query = _build_rag_query(latest_message, profile, ratios)
    rag_chunks, citations = retriever.query(query, top_k=settings.rag_top_k)

    # 2. Build the user prompt with all context
    profile_text = _format_profile_for_llm(profile, ratios)
    rag_text = _format_rag_context(rag_chunks)

    missing_note = ""
    if missing_fields:
        labels = [f.replace("_", " ") for f in missing_fields[:5]]
        missing_note = f"\n\n**Note:** Profile is incomplete. Missing fields: {', '.join(labels)}. Guidance is provisional."

    user_prompt = (
        f"**BORROWER'S QUESTION:** {latest_message}\n\n"
        f"**BORROWER PROFILE:**\n{profile_text}{missing_note}\n\n"
        f"**REGULATORY CONTEXT (from RBI/NBFC documents):**\n{rag_text}"
    )

    # 3. Call Groq LLM
    if not groq_pool.has_keys():
        return _deterministic_fallback(latest_message, profile, ratios, missing_fields), citations

    try:
        reply = chat_completion(
            model="llama-3.3-70b-versatile",
            system_prompt=CHAT_RESPONSE_PROMPT,
            user_prompt=user_prompt,
            temperature=0.25,
            max_tokens=800,
        )
        return reply, citations
    except Exception:
        return _deterministic_fallback(latest_message, profile, ratios, missing_fields), citations


def _deterministic_fallback(
    latest_message: str,
    profile: dict[str, Any],
    ratios: dict[str, Any],
    missing_fields: list[str] | None = None,
) -> str:
    """Simple fallback when Groq LLM is unavailable."""
    lines: list[str] = ["**Financial Consultation** (offline mode — LLM unavailable)\n"]

    if ratios.get("projected_emi") is not None:
        lines.append(f"- Estimated EMI: ₹{ratios['projected_emi']:,.0f}")
    if ratios.get("current_dti") is not None:
        lines.append(f"- Current DTI: {ratios['current_dti']:.2f}")
    if ratios.get("post_loan_dti") is not None:
        dti = ratios["post_loan_dti"]
        status = "comfortable" if dti <= 0.45 else "borderline" if dti <= 0.60 else "high"
        lines.append(f"- Post-loan DTI: {dti:.2f} ({status})")
    if ratios.get("ltv_ratio") is not None:
        lines.append(f"- LTV Ratio: {ratios['ltv_ratio']:.2f}")

    cs = profile.get("credit_score")
    if cs is not None:
        quality = "strong" if cs >= 720 else "acceptable" if cs >= 650 else "weak"
        lines.append(f"- Credit Score: {cs} ({quality})")

    if missing_fields:
        labels = [f.replace("_", " ") for f in missing_fields[:5]]
        lines.append(f"\nMissing fields for full assessment: {', '.join(labels)}.")

    lines.append("\nSay **'generate report'** for a full RBI-aligned credit assessment.")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# GREETING DETECTION
# ─────────────────────────────────────────────────────────────────────────────

_GREETING_WORDS = {
    "hi", "hello", "hey", "hii", "hiii", "heya", "hola", "namaste",
    "good morning", "good afternoon", "good evening", "gm", "yo",
    "what's up", "whats up", "sup", "howdy",
}

_WELCOME_MSG = (
    "👋 **Welcome to CreditSense!**\n\n"
    "I'm your AI credit risk advisor, powered by RBI regulatory intelligence.\n\n"
    "Here's how I can help:\n"
    "- 🏦 **Assess your loan eligibility** based on your borrower profile\n"
    "- 📊 **Analyze credit risk** with DTI, EMI, and LTV calculations\n"
    "- 📋 **Generate a detailed credit report** with RBI/NBFC regulatory citations\n"
    "- 💡 **Answer financial questions** about lending guidelines and policies\n\n"
    "**To get started**, fill in your borrower details in the sidebar and click **Save & Analyze Profile**, "
    "then ask me anything about your loan eligibility!"
)


def _is_greeting(message: str) -> bool:
    msg = message.lower().strip().rstrip("!?.")
    if msg in _GREETING_WORDS:
        return True
    # Check multi-word greetings
    for greeting in _GREETING_WORDS:
        if " " in greeting and greeting in msg:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# NODE 1: GUARDRAIL
# ─────────────────────────────────────────────────────────────────────────────

def guardrail_node(state: AgentState) -> AgentState:
    latest_message = _latest_user_message(state.get("messages", []))

    # Greetings get a friendly welcome — not a block
    if _is_greeting(latest_message):
        return _merge(state, {
            "is_finance_query": True,
            "guardrail_reason": "greeting",
            "assistant_reply": _WELCOME_MSG,
            "trace": _add_trace(state, "guardrail:greeting"),
        })

    safe, safety_reason, safety_reply = check_project_guardrails(latest_message)
    if not safe:
        return _merge(state, {
            "is_finance_query": False,
            "guardrail_reason": safety_reason,
            "assistant_reply": safety_reply,
            "trace": _add_trace(state, f"guardrail:block:{safety_reason}"),
        })

    collected = dict(state.get("collected") or {})
    missing_fields = list(state.get("missing_fields") or [])
    continuation, continuation_reason = should_treat_as_continuation(
        latest_message,
        has_finance_context=_has_collected_progress(collected),
        missing_fields=missing_fields,
    )
    if continuation:
        return _merge(state, {
            "is_finance_query": True,
            "guardrail_reason": continuation_reason,
            "trace": _add_trace(state, f"guardrail:continuation:{continuation_reason}"),
        })

    is_finance, reason = check_finance_query(latest_message)

    if not is_finance:
        return _merge(state, {
            "is_finance_query": False,
            "guardrail_reason": reason,
            "assistant_reply": (
                "I'm CreditSense — I specialize in **credit risk assessment and loan eligibility**.\n\n"
                "Try asking me things like:\n"
                "- _\"Am I eligible for a home loan?\"_\n"
                "- _\"What is a good DTI ratio?\"_\n"
                "- _\"What are RBI guidelines for NBFC lending?\"_\n\n"
                "Fill in your profile in the sidebar to get personalized guidance!"
            ),
            "trace": _add_trace(state, f"guardrail:block:{reason}"),
        })

    return _merge(state, {
        "is_finance_query": True,
        "guardrail_reason": reason,
        "trace": _add_trace(state, f"guardrail:pass:{reason}"),
    })


# ─────────────────────────────────────────────────────────────────────────────
# NODE 2: CONVERSATION (profile extraction + RAG-powered LLM response)
# ─────────────────────────────────────────────────────────────────────────────

def conversation_node(state: AgentState) -> AgentState:
    # If guardrail already set a reply (e.g. greeting welcome), preserve it
    if state.get("guardrail_reason") == "greeting" and state.get("assistant_reply"):
        return state

    collected = dict(state.get("collected") or {})
    latest_message = _latest_user_message(state.get("messages", []))
    existing_report = bool(state.get("report_en"))

    updates = extract_profile_updates(latest_message, collected)
    merged = merge_collected(collected, updates)
    missing = get_missing_fields(merged)
    profile_complete = len(missing) == 0
    report_requested = is_report_request(latest_message)

    # Compute ratios with whatever data we have
    ratios = compute_ratios(merged, annual_rate=settings.annual_interest_rate)
    citations: list[dict[str, Any]] = list(state.get("citations") or [])

    if profile_complete and report_requested:
        reply = "Understood. Generating the borrower report now."
    elif report_requested and not profile_complete:
        wait_fields = ", ".join(field.replace("_", " ") for field in missing[:5])
        reply = f"I can generate the report once remaining details are shared: {wait_fields}."
    elif profile_complete or _is_finance_question(latest_message):
        # RAG + LLM powered response for any financial question
        reply, citations = _llm_chat_reply(
            latest_message, merged, ratios,
            missing_fields=missing if not profile_complete else None,
        )
    else:
        # Pure profile intake — ask for next missing fields
        reply = build_follow_up_reply(
            missing_fields=missing,
            collected=merged,
            latest_message=latest_message,
            updates=updates,
        )

    clear_report = existing_report and bool(updates)

    return _merge(state, {
        "collected": merged,
        "missing_fields": missing,
        "profile_complete": profile_complete,
        "borrower_profile": merged if profile_complete else state.get("borrower_profile", {}),
        "report_requested": bool(profile_complete and report_requested),
        "computed_ratios": ratios,
        "citations": citations,
        "report_en": "" if clear_report else str(state.get("report_en") or ""),
        "report_hi": "" if clear_report else str(state.get("report_hi") or ""),
        "assistant_reply": reply,
        "trace": _add_trace(
            state,
            f"conversation:updates={list(updates.keys())},missing={len(missing)},report_req={report_requested}",
        ),
    })


def _is_finance_question(message: str) -> bool:
    """Check if message contains a financial question worth an LLM-powered answer."""
    msg = (message or "").lower()
    keywords = [
        "loan", "lend", "approval", "approve", "eligible", "should i",
        "can i", "afford", "emi", "dti", "risk", "stable", "nbfc", "rbi",
        "guideline", "policy", "finance", "credit", "income", "debt",
        "interest", "collateral", "underwriting", "assessment", "report",
        "improve", "better", "chance", "what", "how", "why", "when",
        "digital lending", "fair practice",
    ]
    return any(token in msg for token in keywords)


# ─────────────────────────────────────────────────────────────────────────────
# NODE 3: RAG RETRIEVER
# ─────────────────────────────────────────────────────────────────────────────

def rag_retriever_node(state: AgentState) -> AgentState:
    profile = dict(state.get("borrower_profile") or state.get("collected") or {})
    ratios = compute_ratios(profile, annual_rate=settings.annual_interest_rate)
    context = _conversation_context(state)

    rag_chunks, citations = retriever.retrieve(
        profile,
        ratios,
        conversation_context=context,
        top_k=settings.rag_top_k,
    )
    return _merge(state, {
        "computed_ratios": ratios,
        "rag_chunks": rag_chunks,
        "citations": citations,
        "conversation_context": context,
        "trace": _add_trace(state, f"rag:chunks={len(rag_chunks)}"),
    })


# ─────────────────────────────────────────────────────────────────────────────
# NODE 4: POLICY ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def policy_node(state: AgentState) -> AgentState:
    profile = dict(state.get("borrower_profile") or state.get("collected") or {})
    ratios = dict(state.get("computed_ratios") or {})

    ml_score, ml_class = risk_model.score(profile, ratios)
    checks, risk_flags, decision, decision_score = evaluate_policy(profile, ratios, ml_score)

    return _merge(state, {
        "ml_risk_score": ml_score,
        "ml_risk_class": ml_class,
        "policy_checks": checks,
        "risk_flags": risk_flags,
        "decision": decision,
        "decision_score": decision_score,
        "trace": _add_trace(state, f"policy:decision={decision},score={decision_score}"),
    })


# ─────────────────────────────────────────────────────────────────────────────
# NODE 5: REPORT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def report_node(state: AgentState) -> AgentState:
    profile = dict(state.get("borrower_profile") or state.get("collected") or {})
    ratios = dict(state.get("computed_ratios") or {})
    checks = list(state.get("policy_checks") or [])
    decision = str(state.get("decision") or "ESCALATE")
    decision_score = float(state.get("decision_score") or 0)
    risk_flags = list(state.get("risk_flags") or [])
    citations = list(state.get("citations") or [])
    context = str(state.get("conversation_context") or _conversation_context(state))

    report_en = generate_report(
        profile,
        ratios,
        checks,
        decision,
        decision_score,
        risk_flags,
        citations,
        context,
    )

    return _merge(state, {
        "report_en": report_en,
        "report_requested": False,
        "assistant_reply": report_en,
        "trace": _add_trace(state, "report:generated"),
    })


# ─────────────────────────────────────────────────────────────────────────────
# NODE 6: HINDI TRANSLATOR
# ─────────────────────────────────────────────────────────────────────────────

def translate_node(state: AgentState) -> AgentState:
    report_en = str(state.get("report_en") or "")
    report_hi = translate_to_hindi(report_en)

    return _merge(state, {
        "report_hi": report_hi,
        "trace": _add_trace(state, "translate:generated"),
    })
