from __future__ import annotations

from functools import lru_cache
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from .settings import settings


def build_query_from_profile(
    profile: dict[str, Any],
    ratios: dict[str, Any],
    conversation_context: str = "",
) -> str:
    return " ".join(
        [
            f"loan purpose {profile.get('loan_purpose', '')}",
            f"loan amount {profile.get('loan_amount_requested', 0)}",
            f"credit score {profile.get('credit_score', 0)}",
            f"post loan dti {ratios.get('post_loan_dti', 'na')}",
            f"employment type {profile.get('employment_type', '')}",
            f"collateral {profile.get('collateral_type', 'none')}",
            f"borrower conversation context {conversation_context[:400]}",
            "RBI NBFC underwriting fair practices",
        ]
    )


@lru_cache(maxsize=1)
def _embedder() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


class ChromaRetriever:
    def __init__(self, chroma_path: str | None = None, collection_name: str | None = None) -> None:
        self._path = chroma_path or settings.chroma_path
        self._collection_name = collection_name or settings.collection_name

    def _collection(self):
        client = chromadb.PersistentClient(path=self._path)
        return client.get_or_create_collection(self._collection_name)

    def retrieve(
        self,
        profile: dict[str, Any],
        ratios: dict[str, Any],
        conversation_context: str = "",
        top_k: int | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        query = build_query_from_profile(profile, ratios, conversation_context)
        return self.query(query, top_k=top_k)

    def query(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Run a plain-text similarity search against the RAG collection."""
        collection = self._collection()
        if collection.count() == 0:
            return [], []

        embedding = _embedder().encode([query_text], normalize_embeddings=True).tolist()[0]
        result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k or settings.rag_top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        rag_chunks: list[dict[str, Any]] = []
        citations: list[dict[str, Any]] = []
        for idx, doc in enumerate(documents):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            distance = distances[idx] if idx < len(distances) else None
            source = str(metadata.get("source_file") or "unknown")
            priority = str(metadata.get("priority") or "P2")

            rag_chunks.append(
                {
                    "text": doc,
                    "source": source,
                    "priority": priority,
                    "distance": distance,
                }
            )
            citations.append(
                {
                    "title": source,
                    "snippet": (doc[:300] + "...") if len(doc) > 300 else doc,
                    "source": source,
                }
            )

        return rag_chunks, citations


retriever = ChromaRetriever()
