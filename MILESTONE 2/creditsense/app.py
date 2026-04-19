"""
CreditSense v2 — AI-Powered Credit Risk Assessment Agent
Premium Streamlit Interface with Financial Green Theme
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from agent.state import AgentState, REQUIRED_FIELDS, make_initial_state
from services.backend_client import (
    DEFAULT_BACKEND_URL,
    health as backend_health,
    seed_parameters as backend_seed_parameters,
    run_turn as backend_run_turn,
)
from services.pdf_exporter import export_reports

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM FINANCIAL GREEN THEME
# ─────────────────────────────────────────────────────────────────────────────

STYLES = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

  :root {
    --bg-dark: #0a0f0d;
    --bg-main: #0d1210;
    --bg-card: #121a16;
    --bg-card-alt: #162019;
    --bg-elevated: #1a2620;
    --bg-input: #111b15;
    --border: #1e3329;
    --border-hover: #2a4d3a;
    --border-active: #10b981;

    --green-50: #ecfdf5;
    --green-100: #d1fae5;
    --green-300: #6ee7b7;
    --green-400: #34d399;
    --green-500: #10b981;
    --green-600: #059669;
    --green-700: #047857;
    --green-800: #065f46;
    --green-900: #064e3b;

    --gold-400: #fbbf24;
    --gold-500: #f59e0b;

    --red-400: #f87171;
    --red-500: #ef4444;

    --text: #e8efe8;
    --text-secondary: #9cb3a5;
    --text-muted: #627a6e;
    --text-on-green: #022c22;

    --gradient-brand: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
    --gradient-gold: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    --gradient-bg: radial-gradient(ellipse at 20% 50%, rgba(16, 185, 129, 0.06) 0%, transparent 60%),
                   radial-gradient(ellipse at 80% 20%, rgba(5, 150, 105, 0.04) 0%, transparent 50%);

    --radius: 12px;
    --radius-sm: 8px;
    --radius-lg: 16px;
    --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    --font: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-display: 'Space Grotesk', 'DM Sans', sans-serif;
  }

  /* ═══════ GLOBAL ═══════ */
  html, body, .stApp {
    font-family: var(--font) !important;
    background: var(--bg-main) !important;
    color: var(--text) !important;
  }

  .stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background: var(--gradient-bg);
    pointer-events: none;
    z-index: 0;
  }

  #MainMenu, footer,
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stDecoration"] { display: none !important; }

  [data-testid="stAppViewContainer"],
  [data-testid="stMain"] { background: transparent !important; }

  /* ═══════ SIDEBAR ═══════ */
  [data-testid="stSidebar"] {
    background: var(--bg-dark) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 320px !important;
  }

  [data-testid="stSidebar"] * { font-family: var(--font) !important; }

  /* FIXED: Form labels clearly visible */
  [data-testid="stSidebar"] label {
    color: var(--text) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
  }

  [data-testid="stSidebar"] .stMarkdown p,
  [data-testid="stSidebar"] .stMarkdown li {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
  }

  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {
    color: var(--text) !important;
    font-family: var(--font-display) !important;
  }

  /* ═══════ LAYOUT ═══════ */
  .block-container {
    max-width: 920px;
    padding: 1.5rem 2rem 1rem 2rem;
  }

  h1, h2, h3, h4, h5 {
    font-family: var(--font-display) !important;
    color: var(--text) !important;
    font-weight: 700 !important;
  }

  p, li, span { color: var(--text) !important; }
  label { color: var(--text) !important; }

  /* ═══════ TEXT INPUTS ═══════ */
  [data-testid="stTextInput"] input,
  [data-testid="stNumberInput"] input {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font) !important;
    font-size: 0.9rem !important;
  }

  [data-testid="stTextInput"] input:focus,
  [data-testid="stNumberInput"] input:focus {
    border-color: var(--green-500) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
  }

  /* ═══════ SELECTBOX / DROPDOWN — DARK OVERRIDE ═══════ */
  /* The trigger button */
  [data-baseweb="select"] > div {
    background: var(--bg-input) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
  }
  [data-baseweb="select"] > div > div { color: var(--text) !important; }
  [data-baseweb="select"] svg { color: var(--text-secondary) !important; }

  /* The dropdown menu / popover — FORCE DARK */
  [data-baseweb="popover"],
  [data-baseweb="popover"] > div,
  [data-baseweb="menu"],
  [data-baseweb="menu"] > div,
  div[role="listbox"],
  div[role="listbox"] > div {
    background: var(--bg-card) !important;
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
  }

  /* Dropdown items */
  [data-baseweb="menu"] li,
  [data-baseweb="menu"] [role="option"],
  div[role="listbox"] li,
  div[role="listbox"] [role="option"],
  ul[role="listbox"] li {
    color: var(--text) !important;
    background: var(--bg-card) !important;
    background-color: var(--bg-card) !important;
    font-family: var(--font) !important;
  }

  /* Dropdown hover */
  [data-baseweb="menu"] li:hover,
  [data-baseweb="menu"] [role="option"]:hover,
  div[role="listbox"] li:hover,
  div[role="listbox"] [role="option"]:hover,
  ul[role="listbox"] li:hover,
  [data-baseweb="menu"] [data-highlighted="true"],
  [role="option"][aria-selected="true"] {
    background: rgba(16, 185, 129, 0.15) !important;
    background-color: rgba(16, 185, 129, 0.15) !important;
    color: var(--green-300) !important;
  }

  /* ═══════ BUTTONS ═══════ */
  div[data-testid="stButton"] > button {
    background: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-family: var(--font) !important;
    transition: all 0.25s ease !important;
  }

  div[data-testid="stButton"] > button:hover {
    background: var(--bg-elevated) !important;
    border-color: var(--green-500) !important;
    color: var(--green-400) !important;
  }

  /* Primary buttons */
  div[data-testid="stButton"] > button[kind="primary"],
  div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
    background: var(--gradient-brand) !important;
    color: var(--text-on-green) !important;
    border: none !important;
    font-weight: 700 !important;
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover,
  div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"]:hover {
    opacity: 0.92 !important;
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3) !important;
    color: var(--text-on-green) !important;
  }

  /* ═══════ CHAT MESSAGES ═══════ */
  .stChatMessage {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background: var(--bg-card) !important;
    padding: 12px 16px !important;
    margin-bottom: 0.6rem !important;
  }

  .stChatMessage p, .stChatMessage li,
  .stChatMessage td, .stChatMessage th { color: var(--text) !important; }
  .stChatMessage strong { color: var(--green-300) !important; }
  .stChatMessage em { color: var(--text-secondary) !important; }
  .stChatMessage code { background: var(--bg-elevated) !important; color: var(--green-400) !important; padding: 2px 6px !important; border-radius: 4px !important; }
  .stChatMessage h1, .stChatMessage h2, .stChatMessage h3,
  .stChatMessage h4, .stChatMessage h5 { color: var(--green-300) !important; }

  /* User vs assistant styling */
  .stChatMessage[data-testid="stChatMessage-user"] {
    background: rgba(16, 185, 129, 0.06) !important;
    border-color: rgba(16, 185, 129, 0.15) !important;
  }

  /* ═══════ CHAT INPUT — NUCLEAR DARK OVERRIDE ═══════ */
  /* Target EVERY possible container Streamlit renders for chat input */
  [data-testid="stBottom"],
  [data-testid="stBottom"] > div,
  [data-testid="stBottom"] > div > div,
  [data-testid="stBottomBlockContainer"],
  [data-testid="stBottomBlockContainer"] > div,
  [data-testid="stBottomBlockContainer"] > div > div,
  [data-testid="stBottomBlockContainer"] > div > div > div {
    background: var(--bg-main) !important;
    background-color: var(--bg-main) !important;
  }

  [data-testid="stChatInputContainer"],
  [data-testid="stChatInputContainer"] > div {
    background: var(--bg-main) !important;
    background-color: var(--bg-main) !important;
    border-top: none !important;
  }

  /* The chat input form wrapper */
  [data-testid="stChatInput"],
  [data-testid="stChatInput"] > div {
    background: transparent !important;
  }

  [data-testid="stChatInput"] textarea {
    background: var(--bg-card) !important;
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font) !important;
    font-size: 0.95rem !important;
    caret-color: var(--green-400) !important;
  }
  [data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }
  [data-testid="stChatInput"] textarea:focus {
    border-color: var(--green-500) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.12) !important;
  }
  [data-testid="stChatInput"] button {
    background: var(--gradient-brand) !important;
    color: var(--text-on-green) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
  }

  /* Also catch any stray white backgrounds in the bottom area */
  .stBottom, .stBottom * {
    background-color: var(--bg-main) !important;
  }
  .stBottom [data-testid="stChatInput"] textarea {
    background-color: var(--bg-card) !important;
  }
  .stBottom [data-testid="stChatInput"] button {
    background: var(--gradient-brand) !important;
  }

  /* ═══════ TABS ═══════ */
  .stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: var(--radius) !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(16, 185, 129, 0.12) !important;
    color: var(--green-400) !important;
  }
  .stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
  }

  /* ═══════ EXPANDER / SPINNER / ALERTS ═══════ */
  [data-testid="stExpander"] details {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
  }
  [data-testid="stExpander"] summary * { color: var(--text) !important; background-color: transparent !important; }
  .stAlert { border-radius: var(--radius-sm) !important; }

  /* ═══════ DOWNLOADS ═══════ */
  .stDownloadButton > button {
    background: var(--bg-card) !important;
    color: var(--green-400) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
  }
  .stDownloadButton > button:hover {
    border-color: var(--green-500) !important;
    background: var(--bg-elevated) !important;
  }

  /* ═══════ TABLE ═══════ */
  .stMarkdown table { border-collapse: collapse !important; width: 100% !important; }
  .stMarkdown th {
    background: var(--bg-elevated) !important;
    color: var(--green-300) !important;
    padding: 0.6rem 0.8rem !important;
    border: 1px solid var(--border) !important;
    font-weight: 600 !important;
    text-align: left !important;
  }
  .stMarkdown td {
    background: var(--bg-card) !important;
    color: var(--text) !important;
    padding: 0.5rem 0.8rem !important;
    border: 1px solid var(--border) !important;
  }

  /* ═══════ SLIDER ═══════ */
  [data-testid="stSlider"] > div > div > div > div { background: var(--green-500) !important; }
  [data-testid="stSlider"] [role="slider"] { background: var(--green-400) !important; border-color: var(--green-600) !important; }
  [data-testid="stSlider"] [data-testid="stThumbValue"] { color: var(--green-400) !important; }

  /* ═══════ SELECT SLIDER ═══════ */
  [data-testid="stSlider"] span { color: var(--text-secondary) !important; }

  /* ═══════════════ CUSTOM COMPONENTS ═══════════════ */

  .cs-hero {
    text-align: center;
    padding: 1.2rem 0 0.8rem 0;
    position: relative;
  }

  .cs-hero h1 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    font-family: var(--font-display) !important;
    color: var(--green-400) !important;
    letter-spacing: -0.02em !important;
    margin: 0 !important;
  }

  .cs-hero .cs-tagline {
    color: var(--text-secondary);
    font-size: 0.92rem;
    margin-top: 0.3rem;
    letter-spacing: 0.02em;
  }

  .cs-metric-row {
    display: flex;
    gap: 12px;
    margin: 0.8rem 0;
  }

  .cs-metric {
    flex: 1;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    text-align: center;
    transition: border-color 0.2s;
  }

  .cs-metric:hover {
    border-color: var(--border-hover);
  }

  .cs-metric-value {
    font-family: var(--font-display);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--green-300);
    line-height: 1.2;
  }

  .cs-metric-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 0.3rem;
  }

  .cs-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0.6rem 1.2rem;
    border-radius: var(--radius-sm);
    font-weight: 700;
    font-size: 1rem;
    width: 100%;
    justify-content: center;
  }
  .cs-badge.approve  { background: rgba(16, 185, 129, 0.1); color: var(--green-400); border: 1px solid rgba(16, 185, 129, 0.2); }
  .cs-badge.conditional { background: rgba(251, 191, 36, 0.08); color: var(--gold-400); border: 1px solid rgba(251, 191, 36, 0.2); }
  .cs-badge.escalate { background: rgba(248, 113, 113, 0.08); color: var(--red-400); border: 1px solid rgba(248, 113, 113, 0.2); }

  .cs-divider {
    height: 1px;
    background: var(--border);
    margin: 1rem 0;
    border: none;
  }

  /* Sidebar branding */
  .sb-brand {
    text-align: center;
    padding: 0.6rem 0;
  }
  .sb-brand-icon {
    font-size: 2rem;
    line-height: 1;
  }
  .sb-brand-name {
    font-family: var(--font-display);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--green-400) !important;
    letter-spacing: -0.01em;
  }
  .sb-brand-sub {
    font-size: 0.68rem;
    color: var(--text-muted) !important;
    letter-spacing: 1.2px;
    text-transform: uppercase;
  }

  .sb-section-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--green-600) !important;
    margin: 0.8rem 0 0.3rem 0;
    padding-left: 2px;
  }

  .sb-pill {
    font-size: 0.75rem;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
    font-weight: 600;
    display: inline-block;
  }
  .sb-pill.ok   { background: rgba(16,185,129,0.12); color: var(--green-400); }
  .sb-pill.warn { background: rgba(251,191,36,0.1); color: var(--gold-400); }

  .sb-backend {
    text-align: center;
    font-size: 0.68rem;
    margin-top: 0.5rem;
    letter-spacing: 0.3px;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .block-container { padding: 0.5rem 1rem; }
    .cs-hero h1 { font-size: 1.6rem !important; }
    .cs-metric-row { flex-direction: column; }
  }
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def _init_state() -> None:
    if "backend_url" not in st.session_state:
        st.session_state.backend_url = os.getenv("BACKEND_API_BASE_URL", DEFAULT_BACKEND_URL)

    if "agent_state" not in st.session_state:
        try:
            from services.backend_client import fetch_initial_state
            st.session_state.agent_state = fetch_initial_state(st.session_state.backend_url)
        except Exception:
            st.session_state.agent_state = make_initial_state()

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []


def _is_empty(v: object) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return False


def _count_filled(collected: dict[str, Any]) -> int:
    return sum(1 for f in REQUIRED_FIELDS if not _is_empty(collected.get(f)))


def _val(d: dict, k: str, default: str = "") -> str:
    v = d.get(k)
    return str(v) if v is not None and str(v).strip() else default


def _int_val(d: dict, k: str, default: int = 0) -> int:
    v = d.get(k)
    if v is None:
        return default
    try:
        return int(float(v))
    except Exception:
        return default


def _idx(options: list[str], current: str | None) -> int:
    if current and current in options:
        return options.index(current)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — BORROWER PROFILE
# ─────────────────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        # Branding
        st.markdown(
            '<div class="sb-brand">'
            '<div class="sb-brand-icon">🏛️</div>'
            '<div class="sb-brand-name">CreditSense</div>'
            '<div class="sb-brand-sub">AI Credit Risk Agent</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="cs-divider"></div>', unsafe_allow_html=True)

        state: AgentState = st.session_state.agent_state
        collected = dict(state.get("collected") or {})
        filled = _count_filled(collected)
        total = len(REQUIRED_FIELDS)
        is_complete = state.get("profile_complete", False)

        if is_complete:
            st.markdown('<span class="sb-pill ok">✓ Profile Complete</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="sb-pill warn">◉ {filled}/{total} Fields Filled</span>', unsafe_allow_html=True)

        st.markdown("")

        # ── Personal ──
        st.markdown('<div class="sb-section-label">👤 Personal</div>', unsafe_allow_html=True)
        name = st.text_input("Full Name", value=_val(collected, "name"), key="sb_name", placeholder="e.g. Rahul Sharma")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Age", 18, 80, _int_val(collected, "age", 30), key="sb_age")
        with c2:
            cities = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kolkata", "Other"]
            city = st.selectbox("City", cities, index=_idx(cities, collected.get("city", "Mumbai")), key="sb_city")

        # ── Employment ──
        st.markdown('<div class="sb-section-label">💼 Employment</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        emp_types = ["Salaried", "Self-Employed", "Contract", "Gig"]
        with c3:
            emp_type = st.selectbox("Type", emp_types, index=_idx(emp_types, collected.get("employment_type", "Salaried")), key="sb_emp")
        with c4:
            emp_years = st.number_input("Years", 0, 40, _int_val(collected, "employment_years", 2), key="sb_years")
        monthly_income = st.number_input("Monthly Income (₹)", 0, 10_000_000, _int_val(collected, "monthly_income", 50000), step=5000, key="sb_income")

        # ── Credit ──
        st.markdown('<div class="sb-section-label">📊 Credit History</div>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            credit_score = st.number_input("CIBIL Score", 300, 900, _int_val(collected, "credit_score", 700), step=10, key="sb_cibil")
        with c6:
            existing_loans = st.number_input("Existing Loans", 0, 10, _int_val(collected, "existing_loan_count", 0), key="sb_eloans")
        existing_emi = st.number_input("Existing EMI (₹/mo)", 0, 1_000_000, _int_val(collected, "existing_emi_monthly", 0), step=1000, key="sb_eemi")
        history_opts = ["Clean", "1 Default", "2+ Defaults"]
        payment_history = st.selectbox("Payment History", history_opts, index=_idx(history_opts, collected.get("payment_history", "Clean")), key="sb_hist")

        # ── Loan Request ──
        st.markdown('<div class="sb-section-label">🏦 Loan Request</div>', unsafe_allow_html=True)
        c7, c8 = st.columns(2)
        with c7:
            loan_amt = st.number_input("Amount (₹)", 0, 100_000_000, _int_val(collected, "loan_amount_requested", 500000), step=50000, key="sb_lamt")
        with c8:
            purposes = ["Home", "Business", "Personal", "Education", "Vehicle"]
            loan_purpose = st.selectbox("Purpose", purposes, index=_idx(purposes, collected.get("loan_purpose", "Personal")), key="sb_purp")
        tenure = st.select_slider("Tenure (months)", [12, 24, 36, 48, 60, 72, 84, 96, 120, 180, 240], value=_int_val(collected, "loan_tenure_months", 60), key="sb_ten")

        # ── Collateral ──
        st.markdown('<div class="sb-section-label">🔒 Collateral (Optional)</div>', unsafe_allow_html=True)
        c9, c10 = st.columns(2)
        coll_types = ["None", "Property", "Gold", "Fixed Deposit", "Vehicle"]
        with c9:
            coll_type = st.selectbox("Type", coll_types, index=_idx(coll_types, collected.get("collateral_type", "None")), key="sb_ctype")
        with c10:
            coll_val = st.number_input("Value (₹)", 0, 100_000_000, _int_val(collected, "collateral_value", 0) if coll_type != "None" else 0, step=100000, key="sb_cval", disabled=(coll_type == "None"))

        st.markdown("")

        # Save
        if st.button("💾  Save & Analyze Profile", use_container_width=True, type="primary"):
            params: dict[str, Any] = {
                "name": name, "age": age, "city": city,
                "employment_type": emp_type, "employment_years": float(emp_years),
                "monthly_income": float(monthly_income),
                "credit_score": credit_score,
                "existing_loan_count": existing_loans, "existing_emi_monthly": float(existing_emi),
                "payment_history": payment_history,
                "loan_amount_requested": float(loan_amt), "loan_purpose": loan_purpose,
                "loan_tenure_months": tenure,
                "collateral_type": coll_type,
                "collateral_value": float(coll_val) if coll_type != "None" else 0.0,
            }
            try:
                result = backend_seed_parameters(
                    parameters=params,
                    state=st.session_state.agent_state,
                    base_url=st.session_state.backend_url,
                )
                new_state = result.get("state")
                if isinstance(new_state, dict):
                    st.session_state.agent_state = new_state
                st.success("✓ Profile saved & analyzed")
                st.rerun()
            except Exception as exc:
                st.error(f"Save failed: {exc}")

        st.markdown('<div class="cs-divider"></div>', unsafe_allow_html=True)

        if st.button("↺  Reset Session", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        # Backend indicator
        try:
            backend_health(st.session_state.backend_url)
            st.markdown('<div class="sb-backend" style="color:#34d399;">● Backend Connected</div>', unsafe_allow_html=True)
        except Exception:
            st.markdown('<div class="sb-backend" style="color:#f87171;">● Backend Offline</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT TURN
# ─────────────────────────────────────────────────────────────────────────────

def _run_agent_turn(text: str) -> AgentState:
    state: AgentState = st.session_state.agent_state
    payload = backend_run_turn(user_message=text, state=state, base_url=st.session_state.backend_url)
    updated = payload.get("state")
    if not isinstance(updated, dict):
        raise RuntimeError("Backend returned invalid state")
    st.session_state.agent_state = updated
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# METRIC CARDS
# ─────────────────────────────────────────────────────────────────────────────

def _render_metrics(state: AgentState) -> None:
    ratios = dict(state.get("computed_ratios") or {})
    profile = dict(state.get("collected") or {})

    if not ratios and not profile.get("credit_score"):
        return

    cs = profile.get("credit_score")
    cs_display = str(cs) if cs else "—"
    dti = ratios.get("post_loan_dti")
    dti_display = f"{dti:.2f}" if dti is not None else "—"
    emi = ratios.get("projected_emi")
    emi_display = f"₹{emi:,.0f}" if emi else "—"
    ltv = ratios.get("ltv_ratio")
    ltv_display = f"{ltv:.2f}" if ltv is not None else "N/A"

    st.markdown(
        f"""
        <div class="cs-metric-row">
          <div class="cs-metric">
            <div class="cs-metric-value">{cs_display}</div>
            <div class="cs-metric-label">CIBIL Score</div>
          </div>
          <div class="cs-metric">
            <div class="cs-metric-value">{dti_display}</div>
            <div class="cs-metric-label">Post-Loan DTI</div>
          </div>
          <div class="cs-metric">
            <div class="cs-metric-value">{emi_display}</div>
            <div class="cs-metric-label">Projected EMI</div>
          </div>
          <div class="cs-metric">
            <div class="cs-metric-value">{ltv_display}</div>
            <div class="cs-metric-label">LTV Ratio</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# REPORT PANEL
# ─────────────────────────────────────────────────────────────────────────────

def _render_report(state: AgentState) -> None:
    report_en = str(state.get("report_en") or "")
    report_hi = str(state.get("report_hi") or "")
    if not report_en:
        return

    st.markdown('<div class="cs-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📄 Credit Assessment Report")

    # Decision badge
    decision = str(state.get("decision") or "").upper()
    score = state.get("decision_score") or 0
    badge_map = {"APPROVE": "approve", "CONDITIONAL": "conditional", "ESCALATE": "escalate"}
    icon_map = {"APPROVE": "✅", "CONDITIONAL": "⚠️", "ESCALATE": "🔴"}
    cls = badge_map.get(decision, "conditional")
    icon = icon_map.get(decision, "📋")

    st.markdown(f'<div class="cs-badge {cls}">{icon} {decision} — Confidence Score: {score:.0f}/100</div>', unsafe_allow_html=True)
    st.markdown("")

    # Multilingual tabs
    tab_en, tab_hi = st.tabs(["🇬🇧 English Report", "🇮🇳 Hindi Report (हिंदी)"])
    with tab_en:
        st.markdown(report_en)
    with tab_hi:
        if report_hi:
            st.markdown(report_hi)
        else:
            st.info("Hindi translation is being generated...")

    # PDF Downloads
    st.markdown("")
    try:
        en_pdf, hi_pdf = export_reports(report_en, report_hi or report_en)
        c1, c2 = st.columns(2)
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        with c1:
            st.download_button("📥 Download English PDF", data=en_pdf, file_name=f"CreditSense-Report-EN-{ts}.pdf", mime="application/pdf", use_container_width=True)
        with c2:
            st.download_button("📥 Download Hindi PDF", data=hi_pdf, file_name=f"CreditSense-Report-HI-{ts}.pdf", mime="application/pdf", use_container_width=True)
    except Exception as exc:
        st.warning(f"PDF export unavailable: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="CreditSense — AI Credit Risk Agent",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(STYLES, unsafe_allow_html=True)
    _init_state()

    # Sidebar
    _render_sidebar()

    # Main content
    state: AgentState = st.session_state.agent_state

    # Hero
    st.markdown(
        '<div class="cs-hero">'
        '<h1>CreditSense</h1>'
        '<div class="cs-tagline">AI-powered credit risk assessment · RBI regulatory intelligence · Multilingual reports</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Metrics
    _render_metrics(state)

    # Report generation button
    if state.get("profile_complete"):
        if state.get("report_en"):
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Regenerate Report", use_container_width=True):
                    with st.spinner("Regenerating..."):
                        try:
                            upd = _run_agent_turn("Regenerate the credit assessment report.")
                            reply = str(upd.get("assistant_reply") or "")
                            if reply:
                                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
        else:
            if st.button("📊  Generate Credit Assessment Report", use_container_width=True, type="primary"):
                trigger = "Generate the credit assessment report using the submitted borrower profile."
                st.session_state.chat_messages.append({"role": "user", "content": trigger})
                with st.spinner("Generating your credit report with regulatory analysis..."):
                    try:
                        upd = _run_agent_turn(trigger)
                        reply = str(upd.get("assistant_reply") or "")
                        if reply:
                            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    st.markdown('<div class="cs-divider"></div>', unsafe_allow_html=True)

    # Chat section
    st.markdown("#### 💬 Financial Guidance Chat")
    st.caption("Ask about loan eligibility, RBI norms, EMI affordability, credit improvement, or NBFC policies.")

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_text = st.chat_input("Ask about your loan, credit score, RBI policy, or EMI...")

    if user_text:
        st.session_state.chat_messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.spinner("Analyzing your query..."):
            try:
                updated = _run_agent_turn(user_text)
                error_msg = None
            except Exception as exc:
                updated = st.session_state.agent_state
                error_msg = str(exc)

        if error_msg:
            st.error(f"Agent error: {error_msg}")

        reply = str(updated.get("assistant_reply") or "")
        if reply:
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)

        st.rerun()

    # Report panel (below chat)
    _render_report(state)


if __name__ == "__main__":
    main()
