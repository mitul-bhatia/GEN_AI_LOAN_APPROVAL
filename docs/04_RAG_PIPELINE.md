# CreditSense RAG Pipeline

> Refreshed from current code scan on 2026-04-19.

## 1. Purpose

The RAG pipeline grounds loan guidance and report generation in regulatory text retrieved from the project corpus.

Implementation points:

- ingestion script: `MILESTONE_2/creditsense/scripts/ingest.py`
- retriever service: `MILESTONE_2/creditsense/services/retriever.py`
- vector store path: `CHROMA_PATH` (default `./chroma_store`)
- collection name: `COLLECTION_NAME` (default `creditsense_docs`)

## 2. Ingestion Pipeline (As Implemented)

### 2.1 File Discovery

`iter_docs(source_dir)` recursively scans source directory and includes:

1. extensions in `SUPPORTED_EXTENSIONS`:
   - `.pdf`, `.txt`, `.md`, `.docx`, `.html`, `.htm`
2. files that pass fallback heuristics:
   - PDF magic bytes (`%PDF-`)
   - text-likeness check (printable bytes ratio)

It excludes hidden files and `.DS_Store`.

### 2.2 Text Extraction

Extraction behavior:

- PDF: `pdfplumber`
- DOCX: `python-docx`
- text-like files: UTF-8 read with ignore errors

### 2.3 Chunking Strategy

`chunk_text(text, chunk_size=1200, overlap=150)`:

1. collapse whitespace
2. sliding window chunking
3. overlap between adjacent chunks for continuity

### 2.4 Embedding and Upsert

For each chunk batch:

1. encode using Chroma ONNX embedding function `ONNXMiniLM_L6_V2()`
2. generate deterministic vector output per chunk batch
3. upsert to Chroma with metadata:
   - `source_file`
   - `priority`
   - `chunk_index`

Stable chunk IDs are generated using SHA256 of path/index/content prefix.

## 3. Priority Tagging

`infer_priority(file_name)` uses keyword mapping:

- `P0`: keywords like `irac`, `fair`, `digital`, `nbfc`
- `P1`: keywords like `master`, `rbi`, `basel`, `prudential`
- `P2`: default fallback

## 4. Retrieval Pipeline (As Implemented)

Retrieval entrypoints:

- `retrieve(profile, ratios, conversation_context, top_k)`
- `query(query_text, top_k)`

### 4.1 Query Construction

`build_query_from_profile(...)` composes a query using:

1. loan purpose
2. loan amount
3. credit score
4. post-loan DTI
5. employment type
6. collateral type
7. conversation context
8. anchor phrase: `RBI NBFC underwriting fair practices`

### 4.2 Similarity Search

1. encode query text using ONNX MiniLM embedder (`ONNXMiniLM_L6_V2`)
2. query Chroma collection with `n_results = top_k or settings.rag_top_k`
3. include documents, metadata, and distances

### 4.3 Output Formatting

Returns both:

1. `rag_chunks` with text/source/priority/distance
2. `citations` with title/snippet/source

## 5. End-to-End Ingestion Commands

Run from `MILESTONE_2/creditsense`.

### 5.1 Default ingestion

```bash
python3 scripts/ingest.py
```

### 5.2 Workspace corpus ingestion

```bash
python3 scripts/ingest.py --source-dir "../../RAG files"
```

### 5.3 Explicit parameters

```bash
python3 scripts/ingest.py \
  --source-dir "../../RAG files" \
  --chroma-path ./chroma_store \
  --collection creditsense_docs \
  --chunk-size 1200 \
  --overlap 150 \
  --embedding-model all-MiniLM-L6-v2
```

## 6. API-Based Ingestion Trigger

The backend exposes an ingestion endpoint:

- `POST /api/v1/ingest`

Example:

```bash
curl -X POST http://localhost:8010/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_dir": "../../RAG files",
    "chunk_size": 1200,
    "overlap": 150
  }'
```

## 7. Operational Notes

1. If collection is empty, retrieval returns empty chunks and citations.
2. Retrieval depth defaults to `RAG_TOP_K` env (default 8).
3. Embedder is memoized with `lru_cache(maxsize=1)`.
4. Corpus refresh is manual unless ingestion is re-run.
5. `--embedding-model` is currently accepted by the script/API for compatibility, while implementation uses the ONNX MiniLM embedder from Chroma utilities.

## 8. Validation Checklist

1. Run ingestion and check console `INGEST_SUMMARY`
2. Start backend and verify `/api/v1/health`
3. Generate report from app and confirm:
   - citations count > 0
   - retrieved count > 0
4. Run scenario script for broad flow coverage
