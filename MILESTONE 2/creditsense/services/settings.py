from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def _default_rag_docs_path() -> str:
    workspace_rag = BASE_DIR.parent.parent / "RAG files"
    if workspace_rag.exists() and workspace_rag.is_dir():
        return str(workspace_rag)
    return str(BASE_DIR / "rag_docs")


@dataclass(frozen=True)
class Settings:
    chroma_path: str = os.getenv("CHROMA_PATH", str(BASE_DIR / "chroma_store"))
    collection_name: str = os.getenv("COLLECTION_NAME", "creditsense_docs")
    rag_docs_path: str = os.getenv("RAG_DOCS_PATH", _default_rag_docs_path())
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "8"))
    annual_interest_rate: float = float(
        os.getenv("DEFAULT_ANNUAL_INTEREST_RATE", "0.15")
    )
    model_path: str = os.getenv("ML_MODEL_PATH", str(BASE_DIR / "ml_model" / "model.pkl"))
    fallback_model_path: str = os.getenv(
        "ML_MODEL_FALLBACK_PATH",
        str(BASE_DIR.parent.parent / "MILESTONE 1" / "models" / "logistic_regression.pkl"),
    )
    hindi_font_path: str = os.getenv(
        "HINDI_FONT_PATH",
        str(BASE_DIR / "assets" / "fonts" / "NotoSansDevanagari-Regular.ttf"),
    )


settings = Settings()
