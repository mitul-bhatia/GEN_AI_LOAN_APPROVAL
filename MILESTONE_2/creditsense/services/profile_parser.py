from __future__ import annotations

import re
from typing import Any

from agent.prompts import CONVERSATION_EXTRACTION_PROMPT
from agent.state import REQUIRED_FIELDS
from .groq_client import chat_completion, parse_json_response
from .groq_pool import groq_pool


FIELDS_TO_ASK_TOGETHER = [
    ["name", "age", "city"],
    ["employment_type", "employment_years", "monthly_income"],
    ["credit_score", "existing_loan_count", "existing_emi_monthly"],
    ["payment_history"],
    ["loan_amount_requested", "loan_purpose", "loan_tenure_months"],
    ["collateral_type", "collateral_value"],
]

FIELD_LABELS = {
    "name": "name",
    "age": "age",
    "city": "city",
    "employment_type": "employment type",
    "monthly_income": "monthly income",
    "employment_years": "employment years",
    "credit_score": "credit score",
    "existing_loan_count": "existing loan count",
    "existing_emi_monthly": "existing EMI",
    "payment_history": "payment history",
    "loan_amount_requested": "loan amount requested",
    "loan_purpose": "loan purpose",
    "loan_tenure_months": "loan tenure (months)",
    "collateral_type": "collateral type",
    "collateral_value": "collateral value",
}

EMPATHY_WORDS = {
    "stress",
    "stressed",
    "anxious",
    "anxiety",
    "worried",
    "worry",
    "tense",
    "confused",
    "scared",
    "afraid",
}

REPORT_INTENT_PATTERNS = [
    r"\bgenerate\s+(?:the\s+)?report\b",
    r"\bcreate\s+(?:the\s+)?report\b",
    r"\bmake\s+(?:a\s+)?report\b",
    r"\bprepare\s+(?:a\s+)?report\b",
    r"\breport\s+now\b",
    r"\bfinal\s+report\b",
    r"\bassessment\s+report\b",
    r"\bcredit\s+report\b",
    r"\bfinal\s+decision\b",
    r"\bunderwriting\s+report\b",
]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _safe_float(text: str) -> float | None:
    try:
        return float(text)
    except Exception:
        return None


def _scale_amount(value: float, scale: str | None) -> float:
    if not scale:
        return value
    token = scale.lower().strip()
    if token == "lakh":
        return value * 100000
    if token == "crore":
        return value * 10000000
    return value


def _amount_from_text(text: str) -> float | None:
    msg = text.lower()
    lakh = re.search(r"(\d+(?:\.\d+)?)\s*lakh", msg)
    if lakh:
        return float(lakh.group(1)) * 100000

    crore = re.search(r"(\d+(?:\.\d+)?)\s*crore", msg)
    if crore:
        return float(crore.group(1)) * 10000000

    currency = re.search(r"(?:₹|\brs\.?\b|\binr\b)\s*([\d,]+(?:\.\d+)?)", msg)
    if currency:
        value = _safe_float(currency.group(1).replace(",", ""))
        if value is not None:
            return value

    plain = re.search(r"\b([1-9]\d{3,})\b", msg)
    if plain:
        return _safe_float(plain.group(1))
    return None


def _extract_name(text: str) -> str:
    direct_patterns = [
        r"name\s+is\s+([a-zA-Z][a-zA-Z\s]{1,50}?)(?=,|\.|;|:|\b(?:age|city|from|payment|credit|loan|income|employment)\b|$)",
        r"borrower\s+is\s+([a-zA-Z][a-zA-Z\s]{1,50}?)(?=,|\.|;|:|\b(?:age|city|from|payment|credit|loan|income|employment)\b|$)",
    ]
    for pattern in direct_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        name = _clean_text(match.group(1))
        if len(name.split()) >= 2:
            return name.title()

    fallback = re.search(r"^([A-Z][a-z]+\s+[A-Z][a-z]+)(?=\b|,|\.|;|:)", text)
    if fallback:
        name = _clean_text(fallback.group(1))
        if len(name.split()) >= 2:
            return name.title()
    return ""


def _extract_age(text: str) -> int | None:
    patterns = [
        r"(\d{2})\s*(?:years?\s*old|yrs?\s*old|yo)\b",
        r"age\s*(?:is|:)?\s*(\d{2})",
        r"^[a-zA-Z][a-zA-Z\s]+,\s*(\d{2})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            age = int(match.group(1))
            if 18 <= age <= 85:
                return age
    return None


def _extract_city(text: str) -> str:
    patterns = [
        r"city\s*(?:is|:)?\s*([a-zA-Z][a-zA-Z\s]{1,40}?)(?=,|\.|;|\b(?:and|i\s+am|i'm|my|salaried|self|contract|gig|employment|monthly|income|credit|loan|payment|existing)\b|$)",
        r"from\s+([a-zA-Z][a-zA-Z\s]{1,40}?)(?=,|\.|;|\b(?:and|i\s+am|i'm|my|salaried|self|contract|gig|employment|monthly|income|credit|loan|payment|existing)\b|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = _clean_text(match.group(1)).strip(" .,;:-")
            if value:
                return value.title()
    return ""


def _extract_employment_type(text: str) -> str:
    msg = text.lower()
    if "salaried" in msg:
        return "Salaried"
    if "self employed" in msg or "self-employed" in msg:
        return "Self-Employed"
    if "own business" in msg or "business owner" in msg or "running a business" in msg:
        return "Self-Employed"
    if "contract" in msg:
        return "Contract"
    if "gig" in msg or "freelance" in msg:
        return "Gig"
    return ""


def _extract_employment_years(text: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:employment|experience|job)",
        r"(?:employ\w*|experience|job)\s*(?:for|of)?\s*(\d+(?:\.\d+)?)\s*years?",
        r"(?:employ\w*)\s*years?\s*(?:is|are|:)?\s*(\d+(?:\.\d+)?)",
        r"(?:salaried|self\s*-?employed|contract|gig|freelance)\s*(?:for)?\s*(\d+(?:\.\d+)?)\s*years?",
        r"(\d+(?:\.\d+)?)\s*(?:are|is)?\s*my\s*employ\w*\s*years?",
        r"(\d+(?:\.\d+)?)\s*employ\w*\s*years?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        years = float(match.group(1))
        if 0 <= years <= 60:
            return years
    return None


def _extract_credit_score(text: str) -> int | None:
    match = re.search(r"(?:credit\s*score|cibil)\s*(?:is|:)?\s*(\d{3})", text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        if 300 <= score <= 900:
            return score
    return None


def _extract_existing_loan_count(text: str) -> int | None:
    number_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "zero": 0,
        "none": 0,
        "no": 0,
    }

    if re.search(r"\b(?:no\s+existing\s+loan|no\s+existing\s+loans|no\s+loans?)\b", text, re.IGNORECASE):
        return 0

    match = re.search(
        r"(?:existing\s+loans?(?:\s+count)?|loan\s+count|number\s+of\s+existing\s+loans?)\s*(?:is|:)?\s*(\d+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return int(match.group(1))

    for word, value in number_map.items():
        if re.search(rf"\b{word}\b\s+existing\s+loan", text, re.IGNORECASE):
            return value
    return None


def _extract_existing_emi_monthly(text: str) -> float | None:
    match = re.search(
        r"(?:existing\s*)?emi(?:\s*monthly)?\s*(?:is|:)?\s*(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    return _safe_float(match.group(1).replace(",", ""))


def _extract_requested_loan_amount(text: str) -> float | None:
    msg = text.lower()
    amount_patterns = [
        r"loan\s+requested\s*(?:is|:)?\s*(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore)?",
        r"loan\s+amount\s*(?:requested\s*)?(?:is|:)?\s*(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore)?",
        r"(?:need|needs|want|wants|apply|applying|request|requested|seeking|require|requires)\b[^\n\r]{0,80}?\bloan(?:\s+amount)?(?:\s+of|\s+for|\s+is|:)?\s*(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore)?",
        r"(?:personal|business|education|home|vehicle)\s+loan(?:\s+amount)?(?:\s+of|\s+for|\s+is|:)?\s*(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|crore)?",
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, msg, re.IGNORECASE)
        if not match:
            continue
        base = _safe_float(match.group(1).replace(",", ""))
        if base is None:
            continue
        return _scale_amount(base, match.group(2))

    if "loan" not in msg:
        return None

    request_match = re.search(
        r"\b(?:need|needs|want|wants|apply|applying|request|requested|seeking|require|requires)\b",
        msg,
    )
    if not request_match:
        return None

    request_segment = msg[request_match.start() :]
    return _amount_from_text(request_segment)


def _extract_collateral_value(text: str) -> float | None:
    lowered = text.lower()
    if "no collateral" in lowered or "without collateral" in lowered:
        return None

    patterns = [
        r"collateral[^\d]{0,50}(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)",
        r"property[^\d]{0,30}(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)",
        r"fixed\s+deposit[^\d]{0,30}(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)",
        r"vehicle\s+collateral[^\d]{0,30}(?:₹|\brs\.?\b|\binr\b)?\s*([\d,]+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        value = _safe_float(match.group(1).replace(",", ""))
        if value is not None:
            return value

    if "collateral" in text.lower() and "none" not in text.lower():
        return _amount_from_text(text)
    return None


def _extract_payment_history(text: str) -> str:
    msg = text.lower()
    if "clean" in msg or "no default" in msg or "no defaults" in msg:
        return "Clean"
    if "2+" in msg or "multiple defaults" in msg or "many defaults" in msg:
        return "2+ Defaults"
    if "1 default" in msg or "one default" in msg or "single default" in msg:
        return "1 Default"
    return ""


def _extract_loan_purpose(text: str) -> str:
    msg = text.lower()
    mapping = {
        "home": "Home",
        "business": "Business",
        "personal": "Personal",
        "education": "Education",
        "vehicle": "Vehicle",
    }
    for key, label in mapping.items():
        if key in msg:
            return label
    return ""


def _extract_tenure_months(text: str) -> int | None:
    months = re.search(r"(\d{1,3})\s*months?", text, re.IGNORECASE)
    if months:
        return int(months.group(1))

    years = re.search(r"(\d{1,2})\s*years?", text, re.IGNORECASE)
    if years:
        return int(years.group(1)) * 12
    return None


def _extract_collateral_type(text: str) -> str:
    msg = text.lower()
    if "no collateral" in msg or "none" in msg:
        return "None"
    if "property" in msg or "house" in msg or "flat" in msg:
        return "Property"
    if "gold" in msg:
        return "Gold"
    if "fixed deposit" in msg or "fd" in msg:
        return "Fixed Deposit"
    if "vehicle" in msg or "car" in msg or "bike" in msg:
        return "Vehicle"
    return ""


def _extract_deterministic(message: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    msg = message.strip()

    name = _extract_name(msg)
    if name:
        data["name"] = name

    age = _extract_age(msg)
    if age is not None:
        data["age"] = age

    city = _extract_city(msg)
    if city:
        data["city"] = city

    emp_type = _extract_employment_type(msg)
    if emp_type:
        data["employment_type"] = emp_type

    employment_years = _extract_employment_years(msg)
    if employment_years is not None:
        data["employment_years"] = employment_years

    credit_score = _extract_credit_score(msg)
    if credit_score is not None:
        data["credit_score"] = credit_score

    existing_loan_count = _extract_existing_loan_count(msg)
    if existing_loan_count is not None:
        data["existing_loan_count"] = existing_loan_count
        if existing_loan_count == 0:
            data["existing_emi_monthly"] = 0.0

    emi = _extract_existing_emi_monthly(msg)
    if emi is not None:
        data["existing_emi_monthly"] = emi

    payment_history = _extract_payment_history(msg)
    if payment_history:
        data["payment_history"] = payment_history

    requested_amount = _extract_requested_loan_amount(msg)
    if requested_amount is not None:
        data["loan_amount_requested"] = requested_amount

    purpose = _extract_loan_purpose(msg)
    if purpose:
        data["loan_purpose"] = purpose

    if "loan" in msg.lower() or "tenure" in msg.lower():
        tenure = _extract_tenure_months(msg)
        if tenure is not None:
            data["loan_tenure_months"] = tenure

    collateral_type = _extract_collateral_type(msg)
    if collateral_type:
        data["collateral_type"] = collateral_type
        if collateral_type == "None":
            data["collateral_value"] = 0.0

    if data.get("collateral_type") != "None":
        collateral_value = _extract_collateral_value(msg)
        if collateral_value is not None:
            data["collateral_value"] = collateral_value

    if "income" in msg.lower() or "salary" in msg.lower():
        income = _amount_from_text(msg)
        if income is not None:
            data["monthly_income"] = income

    return data


def _extract_with_llm(message: str) -> dict[str, Any]:
    if not groq_pool.has_keys():
        return {}

    try:
        response = chat_completion(
            model="llama-3.3-70b-versatile",
            system_prompt=CONVERSATION_EXTRACTION_PROMPT,
            user_prompt=f"Latest user message: {message}",
            temperature=0.0,
            max_tokens=350,
            expect_json=True,
        )
        payload = parse_json_response(response)
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception:
        return {}


def _normalize_updates(updates: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for field in REQUIRED_FIELDS:
        if field not in updates:
            continue
        value = updates[field]
        if value is None:
            continue

        if field in {"name", "employment_type", "payment_history", "loan_purpose", "collateral_type", "city"}:
            text = _clean_text(str(value))
            if text:
                normalized[field] = text
            continue

        if field in {"age", "credit_score", "existing_loan_count", "loan_tenure_months"}:
            try:
                normalized[field] = int(float(value))
            except Exception:
                continue
            continue

        if field in {"monthly_income", "employment_years", "existing_emi_monthly", "loan_amount_requested", "collateral_value"}:
            try:
                normalized[field] = float(value)
            except Exception:
                continue

    return normalized


def merge_collected(collected: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(collected)
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


def get_missing_fields(collected: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        value = collected.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
            continue
    return missing


def extract_profile_updates(message: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    deterministic = _extract_deterministic(message)
    llm = _extract_with_llm(message)

    merged = dict(deterministic)
    for key, value in llm.items():
        if key not in merged and value is not None:
            merged[key] = value

    normalized = _normalize_updates(merged)
    if existing and normalized.get("collateral_type", "").lower() == "none":
        normalized["collateral_value"] = 0.0
    return normalized


def next_question(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "Borrower profile is complete. Say 'generate report' when you want the final report."

    for group in FIELDS_TO_ASK_TOGETHER:
        ask_now = [field for field in group if field in missing_fields]
        if ask_now:
            human = ", ".join(FIELD_LABELS.get(field, field.replace("_", " ")) for field in ask_now)
            return f"Please share: {human}."

    fallback = ", ".join(FIELD_LABELS.get(field, field.replace("_", " ")) for field in missing_fields[:3])
    return f"Please provide: {fallback}."


def _is_emotional_message(message: str) -> bool:
    msg = message.lower()
    return any(re.search(rf"\b{re.escape(word)}\b", msg) for word in EMPATHY_WORDS)


def _to_natural_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _next_missing_group(missing_fields: list[str]) -> list[str]:
    for group in FIELDS_TO_ASK_TOGETHER:
        ask_now = [field for field in group if field in missing_fields]
        if ask_now:
            return ask_now
    return missing_fields[:3]


def build_follow_up_reply(
    *,
    missing_fields: list[str],
    collected: dict[str, Any],
    latest_message: str,
    updates: dict[str, Any],
) -> str:
    if not missing_fields:
        return "Borrower profile is complete. I can provide financial consultation, or generate the report when you ask."

    parts: list[str] = []

    if _is_emotional_message(latest_message):
        parts.append("I understand this can feel stressful. We will do this step by step.")

    acknowledged = [
        FIELD_LABELS.get(field, field.replace("_", " "))
        for field in updates.keys()
        if field in FIELD_LABELS
    ]
    if acknowledged:
        parts.append(f"I have noted your {_to_natural_list(acknowledged[:4])}.")

    ask_fields = _next_missing_group(missing_fields)
    ask_human = [FIELD_LABELS.get(field, field.replace("_", " ")) for field in ask_fields]
    parts.append(f"Next, please share your {_to_natural_list(ask_human)}.")

    return " ".join(part for part in parts if part).strip()


def is_report_request(message: str) -> bool:
    text = message.lower().strip()
    if not text:
        return False
    return any(re.search(pattern, text) for pattern in REPORT_INTENT_PATTERNS)
