from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from .settings import settings


def _to_plain_text(markdown_text: str) -> str:
    """Strip markdown formatting for PDF rendering."""
    text = re.sub(r"^#{1,6}\s*", "", markdown_text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    # Handle table separators — replace with dashes line
    text = re.sub(r"^\|[-| :]+\|$", "─" * 60, text, flags=re.MULTILINE)
    return text


def _normalize_line(line: str, *, max_token_len: int = 80) -> str:
    text = re.sub(r"\s+", " ", line.strip())
    if not text:
        return ""
    chunks: list[str] = []
    for token in text.split(" "):
        if len(token) <= max_token_len:
            chunks.append(token)
        else:
            chunks.extend(token[i: i + max_token_len] for i in range(0, len(token), max_token_len))
    return " ".join(chunks)


def _split_token_by_width(pdf: FPDF, token: str, max_width: float) -> list[str]:
    if not token:
        return [""]

    if pdf.get_string_width(token) <= max_width:
        return [token]

    parts: list[str] = []
    current = ""
    for char in token:
        candidate = current + char
        if current and pdf.get_string_width(candidate) > max_width:
            parts.append(current)
            current = char
        else:
            current = candidate

        # If a single glyph exceeds width in the active font, degrade safely.
        if pdf.get_string_width(current) > max_width:
            parts.append("?")
            current = ""

    if current:
        parts.append(current)

    return parts or ["?"]


def _wrap_text_by_width(pdf: FPDF, text: str, max_width: float) -> list[str]:
    if not text:
        return [""]

    tokens: list[str] = []
    for token in text.split(" "):
        if not token:
            continue
        tokens.extend(_split_token_by_width(pdf, token, max_width))

    if not tokens:
        return [""]

    lines: list[str] = []
    current = tokens[0]
    for token in tokens[1:]:
        candidate = f"{current} {token}"
        if pdf.get_string_width(candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = token
    lines.append(current)

    return lines


def _write_line(pdf: FPDF, line: str, *, language: str) -> None:
    safe_line = _normalize_line(line)
    if not safe_line:
        pdf.ln(4)
        return

    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    try:
        for wrapped in _wrap_text_by_width(pdf, safe_line, max_width):
            pdf.multi_cell(max_width, 7, wrapped, new_x="LMARGIN", new_y="NEXT")
    except Exception:
        if language == "hi":
            raise
        # Last-resort for latin-only fonts: simplify characters and retry.
        fallback = safe_line.encode("latin-1", "replace").decode("latin-1")
        for wrapped in _wrap_text_by_width(pdf, fallback, max_width):
            pdf.multi_cell(max_width, 7, wrapped, new_x="LMARGIN", new_y="NEXT")


def _build_pdf(report_text: str, title: str, language: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    if language == "hi":
        font_path = Path(settings.hindi_font_path)
        if font_path.exists():
            pdf.add_font("NotoDevanagari", "", str(font_path), uni=True)
            pdf.set_font("NotoDevanagari", size=11)
        else:
            # Fall back gracefully with a note
            pdf.set_font("Helvetica", size=11)
            report_text = (
                "[Note: Hindi font (NotoSansDevanagari-Regular.ttf) not found in assets/fonts/. "
                "Place the font file there for proper Devanagari rendering.]\n\n"
                + report_text
            )
    else:
        pdf.set_font("Helvetica", size=11)

    # Title
    pdf.set_font_size(15)
    pdf.set_text_color(18, 58, 47)
    pdf.cell(0, 11, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # Generated timestamp
    pdf.set_font_size(9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 7, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Body
    pdf.set_font_size(11)
    plain_text = _to_plain_text(report_text)
    for line in plain_text.splitlines():
        _write_line(pdf, line, language=language)

    # Footer disclaimer
    pdf.ln(6)
    pdf.set_font_size(8)
    pdf.set_text_color(100, 100, 100)
    disclaimer = (
        "AI-assisted assessment only. This does not constitute a legally binding credit decision. "
        "Final approval requires authorized officer review per RBI guidelines."
    )
    pdf.multi_cell(0, 5, disclaimer)

    # Return bytes — compatible with all fpdf2 versions
    return bytes(pdf.output())


def export_reports(report_en: str, report_hi: str) -> tuple[bytes, bytes]:
    """Generate English and Hindi PDF bytes for download."""
    english_pdf = _build_pdf(report_en, "CreditSense Credit Report (English)", "en")
    hindi_pdf = _build_pdf(report_hi, "CreditSense Credit Report (Hindi)", "hi")
    return english_pdf, hindi_pdf
