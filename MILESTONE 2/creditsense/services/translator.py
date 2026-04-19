from __future__ import annotations

import re

from agent.prompts import TRANSLATE_PROMPT
from .groq_client import chat_completion
from .groq_pool import groq_pool


def _has_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text))


def _deterministic_hindi_report(report_en: str) -> str:
    line_map = {
        "## Credit Assessment Report": "## क्रेडिट मूल्यांकन रिपोर्ट",
        "### Computed Metrics": "### गणना किए गए मानदंड",
        "### Financial Ratios": "### वित्तीय अनुपात",
        "### Regulatory Context": "### नियामकीय संदर्भ",
        "### Fairness Note": "### निष्पक्षता नोट",
        "**Conditions:**": "**शर्तें:**",
        "| Metric | Value | Threshold | Status |": "| मानदंड | मान | सीमा | स्थिति |",
        "|---|---|---|---|": "|---|---|---|---|",
    }

    inline_map = {
        "**Borrower:**": "**उधारकर्ता:**",
        "**Employment:**": "**रोज़गार:**",
        "**Loan Request:**": "**ऋण अनुरोध:**",
        "**Generated On:**": "**तिथि:**",
        "Projected EMI": "अनुमानित EMI",
        "Current DTI": "वर्तमान DTI",
        "Post-loan DTI": "पोस्ट-लोन DTI",
        "LTV Ratio": "LTV अनुपात",
        "Payment History": "भुगतान इतिहास",
        "Assessment uses borrower financial variables and repayment indicators only.": "मूल्यांकन केवल उधारकर्ता के वित्तीय मानकों और पुनर्भुगतान संकेतकों पर आधारित है।",
        "No protected personal attributes are used in final decisioning.": "अंतिम निर्णय में किसी संरक्षित व्यक्तिगत विशेषता का उपयोग नहीं किया जाता।",
        "*Disclaimer: This is an AI-assisted assessment tool. It does not constitute a legally binding credit decision. Final approval requires authorized officer review per RBI guidelines.*": "*अस्वीकरण: यह AI-सहायित मूल्यांकन उपकरण है। यह कानूनी रूप से बाध्यकारी क्रेडिट निर्णय नहीं है। अंतिम स्वीकृति RBI दिशा-निर्देशों के अनुसार अधिकृत अधिकारी की समीक्षा के बाद ही होगी।*",
        "None": "कोई नहीं",
    }

    translated_lines: list[str] = []
    for raw_line in report_en.splitlines():
        line = raw_line
        if line in line_map:
            translated_lines.append(line_map[line])
            continue

        for src, dst in inline_map.items():
            line = line.replace(src, dst)

        line = re.sub(r"\bDecision:\s*APPROVE\b", "निर्णय: स्वीकृत", line)
        line = re.sub(r"\bDecision:\s*ESCALATE\b", "निर्णय: एस्केलेट", line)
        line = re.sub(r"\bDecision:\s*REJECT\b", "निर्णय: अस्वीकृत", line)
        line = line.replace("PASS", "PASS").replace("WATCH", "WATCH").replace("FAIL", "FAIL")

        translated_lines.append(line)

    return "\n".join(translated_lines)


def translate_to_hindi(report_en: str) -> str:
    if not report_en.strip():
        return ""

    if not groq_pool.has_keys():
        return _deterministic_hindi_report(report_en)

    for _ in range(2):
        try:
            translated = chat_completion(
                model="llama-3.3-70b-versatile",
                system_prompt=TRANSLATE_PROMPT,
                user_prompt=report_en,
                temperature=0.1,
                max_tokens=1600,
            )
            if _has_devanagari(translated):
                return translated
        except Exception:
            continue

    return _deterministic_hindi_report(report_en)
