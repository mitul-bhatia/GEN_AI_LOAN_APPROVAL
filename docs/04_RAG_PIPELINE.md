# CreditSense — RAG Pipeline Documentation

> **Document ingestion, chunking, embedding, and retrieval architecture**

---

## 1. RAG Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                         │
│                    (scripts/ingest.py)                        │
│                                                              │
│  RAG files/ (57 docs)                                        │
│       │                                                      │
│       ├── PDF extraction (pdfplumber)                         │
│       ├── DOCX extraction (python-docx)                      │
│       ├── Text extraction (UTF-8 read)                       │
│       │                                                      │
│       ▼                                                      │
│  Chunk text: 1200 chars, 150 char overlap                    │
│       │                                                      │
│       ▼                                                      │
│  Embed: all-MiniLM-L6-v2 (normalized)                        │
│       │                                                      │
│       ▼                                                      │
│  Upsert → ChromaDB (PersistentClient)                        │
│  Collection: "creditsense_docs"                              │
│  Total: 8,452 chunks                                         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    RETRIEVAL PIPELINE                         │
│                    (services/retriever.py)                    │
│                                                              │
│  Borrower Profile + Ratios + Conversation Context            │
│       │                                                      │
│       ▼                                                      │
│  Build composite query string                                │
│       │                                                      │
│       ▼                                                      │
│  Encode with all-MiniLM-L6-v2                                │
│       │                                                      │
│       ▼                                                      │
│  ChromaDB.query(top_k=8)                                     │
│       │                                                      │
│       ▼                                                      │
│  Return: [{text, source, priority, distance}]                │
│  +      [{title, snippet, source}] (citations)               │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Regulatory Corpus

### 2.1 Corpus Statistics

| Metric | Value |
|---|---|
| **Total documents** | 57 |
| **Total chunks** | 8,452 |
| **Chunk size** | 1,200 characters |
| **Overlap** | 150 characters |
| **Embedding model** | `all-MiniLM-L6-v2` (384 dimensions) |
| **Vector store** | ChromaDB (PersistentClient) |
| **Collection name** | `creditsense_docs` |

### 2.2 Document Categories

| Priority | Count | Category | Key Documents |
|---|---|---|---|
| **P0 — Critical** | ~8 | Core NBFC/RBI regulations | IRACP Master Circular, Fair Practices Code, Digital Lending Guidelines, NBFC Master Directions |
| **P1 — Important** | ~12 | Basel, prudential norms, capital adequacy | Basel III data, Capital Requirements, Scale-Based Framework, Prudential Norms |
| **P2 — Reference** | ~37 | Supporting frameworks, industry reports | Ombudsman Scheme, Co-lending Policy, Demographic Studies, FAME Reports |

### 2.3 Priority Assignment Logic

```python
PRIORITY_MAP = {
    "irac": "P0",     # Income Recognition & Asset Classification
    "fair": "P0",     # Fair Practices Code
    "digital": "P0",  # Digital Lending Guidelines
    "nbfc": "P0",     # NBFC Master Directions
    "master": "P1",   # RBI Master Circulars
    "rbi": "P1",      # General RBI documents
    "basel": "P1",    # Basel III/IV frameworks
    "prudential": "P1", # Prudential norms
}
# Default: "P2" (reference)
```

Priority is inferred from the filename by substring matching.

---

## 3. Ingestion Pipeline Detail

### 3.1 File Discovery (`iter_docs()`)

```
1. Recursively scan source directory
2. Skip hidden files (.DS_Store, .*)
3. Include files by:
   a. Extension match: .pdf, .txt, .md, .docx, .html, .htm
   b. PDF magic byte check: %PDF- header
   c. Text heuristic: ≥80% printable ASCII, no null bytes
4. Sort alphabetically
```

### 3.2 Text Extraction (`extract_text()`)

| Format | Extractor | Notes |
|---|---|---|
| **PDF** | `pdfplumber` | Page-by-page text extraction, handles scanned PDFs with text layers |
| **DOCX** | `python-docx` | Paragraph-level text extraction |
| **TXT/MD/HTML** | Direct read | UTF-8 with `errors="ignore"` |
| **Unknown** | Magic byte detection | Falls back to PDF or text based on binary analysis |

### 3.3 Chunking Strategy (`chunk_text()`)

```
Parameters:
  chunk_size = 1200 characters
  overlap    = 150 characters

Algorithm:
  1. Collapse all whitespace to single spaces
  2. Sliding window: start at 0
  3. Each chunk = text[start : start + chunk_size]
  4. Next start = end - overlap
  5. Continue until end of document
```

**Design rationale:**
- 1,200 chars ≈ 200-300 tokens — fits comfortably in LLM context
- 150 char overlap ensures cross-boundary context preservation
- Whitespace normalization prevents chunk-size waste

### 3.4 Embedding

```python
embedder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedder.encode(chunks, normalize_embeddings=True)
```

| Property | Value |
|---|---|
| Model | `all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Size | ~80 MB |
| Normalization | L2-normalized for cosine similarity |
| Speed | ~14,000 sentences/sec on CPU |

### 3.5 ChromaDB Upsert

```python
collection.upsert(
    ids=stable_chunk_ids,      # SHA-256 hash of filepath:chunk_idx:content[:80]
    documents=chunks,           # Raw text
    embeddings=embeddings,      # 384-dim vectors
    metadatas=[{
        "source_file": relative_path,
        "priority": priority,       # P0/P1/P2
        "chunk_index": idx,
    }],
)
```

**Stable IDs:** Chunk IDs are deterministic based on file path, chunk index, and content prefix — enabling idempotent re-ingestion without duplicates.

---

## 4. Retrieval Pipeline Detail

### 4.1 Query Construction

The retriever builds a **rich composite query** that combines profile attributes with regulatory terminology:

```python
query = " ".join([
    f"loan purpose {loan_purpose}",
    f"loan amount {loan_amount_requested}",
    f"credit score {credit_score}",
    f"post loan dti {post_loan_dti}",
    f"employment type {employment_type}",
    f"collateral {collateral_type}",
    f"borrower conversation context {context[:400]}",
    "RBI NBFC underwriting fair practices",   # Anchor terms
])
```

**Why this works:**
- Specific numbers (credit score, amounts) bias toward relevant threshold discussions
- Regulatory anchor terms ("RBI NBFC underwriting fair practices") ensure baseline regulatory coverage
- Conversation context adds user intent and nuance

### 4.2 Semantic Search

```python
embedding = embedder.encode([query], normalize_embeddings=True)
results = collection.query(
    query_embeddings=[embedding],
    n_results=top_k,  # default: 8
    include=["documents", "metadatas", "distances"],
)
```

### 4.3 Output Processing

For each retrieved chunk:
- Extract full document text
- Extract metadata (source, priority, chunk index)
- Record cosine distance for relevance scoring
- Build citation object (title, snippet[:300], source)

---

## 5. Running the Ingestion Pipeline

### CLI Usage

```bash
cd creditsense

# Default: reads from RAG files directory, writes to chroma_store/
python scripts/ingest.py

# Custom source:
python scripts/ingest.py --source-dir ./rag_docs

# Custom parameters:
python scripts/ingest.py \
  --source-dir "../../RAG files" \
  --chroma-path ./chroma_store \
  --collection creditsense_docs \
  --chunk-size 1200 \
  --overlap 150 \
  --embedding-model all-MiniLM-L6-v2
```

### API-Triggered Ingestion

```bash
curl -X POST http://localhost:8010/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_dir": "../../RAG files",
    "chunk_size": 1200,
    "overlap": 150
  }'
```

---

## 6. ChromaDB Storage

### Persistence Model

```
chroma_store/
├── chroma.sqlite3          # Metadata, IDs, chunk text
└── <collection-hash>/      # Embedding vectors (HNSW index)
```

- **PersistentClient**: Data survives restarts without re-ingestion
- **Collection**: `creditsense_docs` — single collection for all regulatory documents
- **Index type**: HNSW (Hierarchical Navigable Small World) — default ChromaDB index

### Storage Location Priority

1. `CHROMA_PATH` environment variable
2. Default: `./chroma_store` (relative to `creditsense/` directory)

---

*CreditSense v2.0 — RAG Pipeline Documentation | Last Updated: April 2026*
