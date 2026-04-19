from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.graph import run_turn
from agent.state import AgentState, REQUIRED_FIELDS, make_initial_state
from scripts.ingest import ingest as run_ingestion
from services.profile_parser import get_missing_fields, merge_collected, next_question
from services.settings import settings


APP_NAME = "CreditSense Backend API"


def _cors_origins() -> list[str]:
    raw = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:8501,http://localhost:8502,http://localhost:8503,http://localhost:8504,http://localhost:8505,http://localhost:3000",
    )
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    return parts or ["*"]


app = FastAPI(title=APP_NAME, version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentTurnRequest(BaseModel):
    user_message: str = Field(min_length=1)
    state: dict[str, Any] | None = None


class SeedParametersRequest(BaseModel):
    parameters: dict[str, Any]
    state: dict[str, Any] | None = None


class IngestRequest(BaseModel):
    source_dir: str | None = None
    chroma_path: str | None = None
    collection: str | None = None
    chunk_size: int = 1200
    overlap: int = 150
    embedding_model: str = "all-MiniLM-L6-v2"


INT_FIELDS = {"age", "credit_score", "existing_loan_count", "loan_tenure_months"}
FLOAT_FIELDS = {
    "monthly_income",
    "employment_years",
    "existing_emi_monthly",
    "loan_amount_requested",
    "collateral_value",
}


def _normalize_seed_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for field in REQUIRED_FIELDS:
        if field not in parameters:
            continue

        value = parameters.get(field)
        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue

        if field in INT_FIELDS:
            try:
                normalized[field] = int(float(value))
            except Exception:
                continue
            continue

        if field in FLOAT_FIELDS:
            try:
                normalized[field] = float(value)
            except Exception:
                continue
            continue

        normalized[field] = str(value)

    if normalized.get("collateral_type", "").lower() == "none":
        normalized["collateral_value"] = 0.0

    if normalized.get("existing_loan_count") == 0 and "existing_emi_monthly" not in normalized:
        normalized["existing_emi_monthly"] = 0.0

    return normalized


def _seed_summary_text(parameters: dict[str, Any]) -> str:
    ordered = [f"{key}={value}" for key, value in parameters.items()]
    return "Form parameters submitted: " + ", ".join(ordered)


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": APP_NAME,
        "chroma_path": settings.chroma_path,
        "collection": settings.collection_name,
    }


@app.get("/api/v1/agent/state/initial")
def initial_state() -> dict[str, Any]:
    return {"state": make_initial_state()}


@app.post("/api/v1/agent/turn")
def agent_turn(payload: AgentTurnRequest) -> dict[str, Any]:
    state: AgentState = (
        payload.state if isinstance(payload.state, dict) else make_initial_state()
    )

    messages = list(state.get("messages") or [])
    messages.append({"role": "user", "content": payload.user_message})
    state["messages"] = messages

    try:
        updated = run_turn(state)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    assistant_reply = str(updated.get("assistant_reply") or "")
    if assistant_reply:
        updated_messages = list(updated.get("messages") or messages)
        updated_messages.append({"role": "assistant", "content": assistant_reply})
        updated["messages"] = updated_messages

    return {
        "assistant_reply": assistant_reply,
        "state": updated,
        "report_ready": bool(updated.get("report_en")),
        "decision": updated.get("decision"),
        "decision_score": updated.get("decision_score"),
        "citations_count": len(updated.get("citations") or []),
        "retrieved_count": len(updated.get("rag_chunks") or []),
    }


@app.post("/api/v1/agent/seed-parameters")
def seed_parameters(payload: SeedParametersRequest) -> dict[str, Any]:
    state: AgentState = (
        payload.state if isinstance(payload.state, dict) else make_initial_state()
    )

    normalized = _normalize_seed_parameters(payload.parameters)
    if not normalized:
        return {
            "assistant_reply": "No valid parameters detected. Please fill at least one borrower field.",
            "state": state,
            "profile_complete": bool(state.get("profile_complete")),
            "missing_fields": list(state.get("missing_fields") or []),
            "applied_fields": [],
        }

    collected = dict(state.get("collected") or {})
    merged = merge_collected(collected, normalized)
    missing = get_missing_fields(merged)
    profile_complete = len(missing) == 0

    messages = list(state.get("messages") or [])
    messages.append({"role": "user", "content": _seed_summary_text(normalized)})

    if profile_complete:
        assistant_reply = (
            "Parameters saved. Borrower profile is complete. "
            "You can ask me to generate the report now."
        )
    else:
        assistant_reply = f"Parameters saved. {next_question(missing)}"
    messages.append({"role": "assistant", "content": assistant_reply})

    # Compute financial ratios immediately for metric display
    from services.borrower_metrics import compute_ratios
    ratios = compute_ratios(merged, annual_rate=settings.annual_interest_rate)

    state["messages"] = messages
    state["collected"] = merged
    state["missing_fields"] = missing
    state["profile_complete"] = profile_complete
    state["borrower_profile"] = merged if profile_complete else dict(state.get("borrower_profile") or {})
    state["computed_ratios"] = ratios
    state["assistant_reply"] = assistant_reply

    trace = list(state.get("trace") or [])
    trace.append(f"seed_parameters:applied={list(normalized.keys())},missing={len(missing)}")
    state["trace"] = trace[-30:]

    return {
        "assistant_reply": assistant_reply,
        "state": state,
        "profile_complete": profile_complete,
        "missing_fields": missing,
        "applied_fields": list(normalized.keys()),
    }


@app.post("/api/v1/ingest")
def ingest_endpoint(payload: IngestRequest) -> dict[str, Any]:
    source_dir = Path(payload.source_dir or settings.rag_docs_path)
    chroma_path = Path(payload.chroma_path or settings.chroma_path)
    collection = payload.collection or settings.collection_name

    if not source_dir.exists():
        raise HTTPException(status_code=400, detail=f"Source directory does not exist: {source_dir}")

    try:
        run_ingestion(
            source_dir=source_dir,
            chroma_path=chroma_path,
            collection_name=collection,
            chunk_size=payload.chunk_size,
            overlap=payload.overlap,
            embedding_model=payload.embedding_model,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return {
        "status": "ok",
        "source_dir": str(source_dir),
        "chroma_path": str(chroma_path),
        "collection": collection,
    }
