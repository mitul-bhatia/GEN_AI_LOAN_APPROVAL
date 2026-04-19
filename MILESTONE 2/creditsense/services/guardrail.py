from __future__ import annotations

import re

from .groq_client import chat_completion, parse_json_response
from .groq_pool import groq_pool
from agent.prompts import GUARDRAIL_PROMPT


FINANCE_KEYWORDS = {
    "loan",
    "emi",
    "credit",
    "lending",
    "borrower",
    "rbi",
    "nbfc",
    "income",
    "debt",
    "dti",
    "ltv",
    "underwriting",
    "interest",
    "collateral",
    "cibil",
    "report",
    "assessment",
    "decision",
}

EMOTION_KEYWORDS = {
    "stressed",
    "stress",
    "anxious",
    "anxiety",
    "worried",
    "worry",
    "tension",
    "tense",
    "scared",
    "afraid",
    "confused",
    "guidance",
    "guide",
    "help",
}

CONTINUATION_HINT_PATTERNS = [
    r"\bage\s*(?:is|:)?\s*\d{2}\b",
    r"\bcity\b",
    r"\bmonthly\s+income\b",
    r"\b(?:credit\s*score|cibil)\b",
    r"\bexisting\s+loan\b",
    r"\b(?:existing\s+)?emi\b",
    r"\bloan\s*(?:amount|requested|tenure)\b",
    r"\bcollateral\b",
    r"\breport\b",
    r"\bassessment\b",
    r"\bdecision\b",
    r"\b\d{3,}\b",
    r"\b(?:yes|no|none|nil)\b",
]

UNSAFE_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"\b(fake|forg(e|ed|ing)|counterfeit|fabricate)\b.*\b(document|bank\s*statement|salary\s*slip|itr|kyc)\b",
        "unsafe-fraud-documents",
        "I can't help with document forgery or fake financial records. I can help with legitimate ways to improve loan eligibility.",
    ),
    (
        r"\b(bypass|avoid|evade|skip)\b.*\b(kyc|compliance|policy|regulation|rbi\s*rules?)\b",
        "unsafe-compliance-evasion",
        "I can't assist with bypassing KYC, compliance, or RBI policy requirements.",
    ),
    (
        r"\b(money\s*launder|laundering|hawala|terror\s*financ|illegal\s*fund)\b",
        "unsafe-illegal-finance",
        "I can't assist with illegal financial activity.",
    ),
    (
        r"\b(ignore|override|bypass|disable)\b.*\b(system\s*prompt|guardrail|policy|safety\s*rule|instruction)\b",
        "unsafe-prompt-bypass",
        "I can't bypass system safeguards. I can continue with safe financial guidance.",
    ),
    (
        r"\b(reveal|show|print|leak)\b.*\b(system\s*prompt|hidden\s*prompt|internal\s*instruction|chain\s*of\s*thought|cot)\b",
        "unsafe-internal-disclosure",
        "I can't reveal internal prompts or reasoning traces, but I can explain conclusions clearly.",
    ),
]

ABUSE_PATTERNS = [
    r"\b(kill|murder|bomb|attack)\b",
    r"\b(hate|racist|sexist)\b",
]


def _keyword_guardrail(message: str) -> tuple[bool, str]:
    msg = message.lower()
    matched = [
        kw for kw in FINANCE_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", msg)
    ]
    if matched:
        return True, f"Keyword match: {', '.join(sorted(matched)[:3])}"
    return False, "Message appears non-financial."


def check_project_guardrails(message: str) -> tuple[bool, str, str]:
    msg = message.lower().strip()
    if not msg:
        return True, "empty-safe", ""

    for pattern, reason, reply in UNSAFE_PATTERNS:
        if re.search(pattern, msg):
            return False, reason, reply

    for pattern in ABUSE_PATTERNS:
        if re.search(pattern, msg):
            return False, "unsafe-abusive-content", "I can only support safe, policy-compliant financial guidance."

    return True, "safe", ""


def should_treat_as_continuation(
    message: str,
    *,
    has_finance_context: bool,
    missing_fields: list[str] | None = None,
) -> tuple[bool, str]:
    if not has_finance_context:
        return False, "No active finance context."

    msg = message.lower().strip()
    if not msg:
        return True, "Empty follow-up treated as continuation."

    keyword_pass, keyword_reason = _keyword_guardrail(message)
    if keyword_pass:
        return True, keyword_reason

    emotional = [word for word in EMOTION_KEYWORDS if re.search(rf"\b{re.escape(word)}\b", msg)]
    if emotional:
        return True, f"Emotional continuation in active intake: {', '.join(sorted(emotional)[:2])}"

    for pattern in CONTINUATION_HINT_PATTERNS:
        if re.search(pattern, msg):
            return True, "Profile detail hint in active intake."

    if (missing_fields or []) and len(msg.split()) <= 10:
        return True, "Short response treated as continuation in active intake."

    return False, "No continuation hint detected."


def check_finance_query(message: str) -> tuple[bool, str]:
    if not message.strip():
        return True, "Empty message treated as conversational continuation."

    # LLM-first: use Groq classifier as the primary guardrail
    if groq_pool.has_keys():
        try:
            response = chat_completion(
                model="llama-3.1-8b-instant",
                system_prompt=GUARDRAIL_PROMPT,
                user_prompt=f"User message: {message}",
                temperature=0.0,
                max_tokens=120,
                expect_json=True,
            )
            payload = parse_json_response(response)
            is_finance = bool(payload.get("is_finance_query", False))
            reason = str(payload.get("reason", "No reason provided")).strip()
            return is_finance, reason or "No reason provided"
        except Exception:
            pass  # Fall through to keyword fallback

    # Keyword fallback when LLM is unavailable
    keyword_pass, keyword_reason = _keyword_guardrail(message)
    return keyword_pass, keyword_reason
