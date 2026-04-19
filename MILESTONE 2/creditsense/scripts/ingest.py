from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import chromadb
import docx
import pdfplumber
from sentence_transformers import SentenceTransformer


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".html", ".htm"}


PRIORITY_MAP = {
    "irac": "P0",
    "fair": "P0",
    "digital": "P0",
    "nbfc": "P0",
    "master": "P1",
    "rbi": "P1",
    "basel": "P1",
    "prudential": "P1",
}


def infer_priority(file_name: str) -> str:
    name = file_name.lower()
    for key, priority in PRIORITY_MAP.items():
        if key in name:
            return priority
    return "P2"


def read_pdf(path: Path) -> str:
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def read_docx(path: Path) -> str:
    d = docx.Document(str(path))
    return "\n".join(p.text for p in d.paragraphs)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _head_bytes(path: Path, size: int = 8) -> bytes:
    with path.open("rb") as file_obj:
        return file_obj.read(size)


def looks_like_pdf(path: Path) -> bool:
    try:
        return _head_bytes(path, 5) == b"%PDF-"
    except Exception:
        return False


def looks_like_text(path: Path) -> bool:
    try:
        sample = _head_bytes(path, 2048)
        if not sample:
            return False
        if b"\x00" in sample:
            return False
        printable = sum(32 <= b <= 126 or b in {9, 10, 13} for b in sample)
        return (printable / max(1, len(sample))) >= 0.80
    except Exception:
        return False


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or looks_like_pdf(path):
        return read_pdf(path)
    if suffix == ".docx":
        return read_docx(path)
    return read_text(path)


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(end - overlap, 0)
    return chunks


def iter_docs(source_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.name == ".DS_Store":
            continue

        suffix = path.suffix.lower()
        if suffix in SUPPORTED_EXTENSIONS:
            files.append(path)
            continue

        if looks_like_pdf(path) or looks_like_text(path):
            files.append(path)
    return sorted(files)


def stable_chunk_id(file_path: Path, chunk_idx: int, content: str) -> str:
    h = hashlib.sha256(f"{file_path}:{chunk_idx}:{content[:80]}".encode("utf-8")).hexdigest()
    return f"{file_path.stem}-{chunk_idx}-{h[:16]}"


def ingest(
    source_dir: Path,
    chroma_path: Path,
    collection_name: str,
    chunk_size: int,
    overlap: int,
    embedding_model: str,
) -> None:
    files = iter_docs(source_dir)
    if not files:
        print(f"No supported files found in {source_dir}")
        return

    print(f"Found {len(files)} documents for ingestion")

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(collection_name)
    embedder = SentenceTransformer(embedding_model)

    total_chunks = 0
    for file_path in files:
        try:
            text = extract_text(file_path)
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            if not chunks:
                print(f"Skipping empty file: {file_path}")
                continue

            embeddings = embedder.encode(chunks, normalize_embeddings=True).tolist()
            rel_source = str(file_path.relative_to(source_dir))
            priority = infer_priority(file_path.name)

            ids = [stable_chunk_id(file_path, idx, chunk) for idx, chunk in enumerate(chunks)]
            metadatas = [
                {
                    "source_file": rel_source,
                    "priority": priority,
                    "chunk_index": idx,
                }
                for idx, _ in enumerate(chunks)
            ]

            collection.upsert(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            total_chunks += len(chunks)
            print(f"Indexed {file_path.name}: {len(chunks)} chunks")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed {file_path}: {exc}")

    print(
        "INGEST_SUMMARY",
        {
            "documents": len(files),
            "total_chunks": total_chunks,
            "collection": collection_name,
            "chroma_path": str(chroma_path),
        },
    )


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parents[1]
    default_source = Path(os.getenv("RAG_DOCS_PATH", str(base_dir / "rag_docs")))
    default_chroma = Path(os.getenv("CHROMA_PATH", str(base_dir / "chroma_store")))
    default_collection = os.getenv("COLLECTION_NAME", "creditsense_docs")

    parser = argparse.ArgumentParser(description="Ingest regulatory documents into Chroma")
    parser.add_argument("--source-dir", type=Path, default=default_source)
    parser.add_argument("--chroma-path", type=Path, default=default_chroma)
    parser.add_argument("--collection", type=str, default=default_collection)
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=150)
    parser.add_argument("--embedding-model", type=str, default="all-MiniLM-L6-v2")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ingest(
        source_dir=args.source_dir,
        chroma_path=args.chroma_path,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        embedding_model=args.embedding_model,
    )
