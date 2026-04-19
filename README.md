# 🏦 CreditSense v2: AI-Powered Loan Approval Agent

<div align="center">
  <img src="https://img.shields.io/badge/Status-Milestone_2_Deployed-success?style=for-the-badge&logoColor=white" />
  <img src="https://img.shields.io/badge/Stack-Streamlit_|_FastAPI_|_LangGraph-blue?style=for-the-badge&logoColor=white" />
  <img src="https://img.shields.io/badge/Retrieval-ChromaDB_|_ONNX_MiniLM-orange?style=for-the-badge&logoColor=white" />
</div>
<br>

**CreditSense v2** is a professional, bilingual (English/Hindi) AI credit assessment platform. It combines a deterministic policy engine, RAG-backed regulatory knowledge (RBI & NBFC guidelines), and LangGraph agent orchestration to provide explainable loan decisions.

---

## 📊 Visual System Architecture

Understanding how CreditSense works is critical for auditability. We utilize a **hybrid deterministic-AI pipeline** that ensures strict policy enforcement with natural language reasoning.

```mermaid
graph TD
    classDef frontend fill:#1E293B,stroke:#38BDF8,stroke-width:2px,color:#fff
    classDef backend fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#fff
    classDef agent fill:#701A75,stroke:#D946EF,stroke-width:2px,color:#fff
    classDef data fill:#3F3F46,stroke:#A1A1AA,stroke-width:2px,color:#fff

    User((👤 Borrower / User))

    subgraph "Presentation Layer (Streamlit Cloud)"
        UI[💻 Streamlit Intake UI & Chat]:::frontend
        Report[📄 Bilingual PDF Export]:::frontend
    end

    subgraph "API Layer (Render / FastAPI)"
        API[⚡ FastAPI Endpoints]:::backend
    end

    subgraph "Intelligence Orchestrator (LangGraph)"
        Guard[🛡️ Guardrails]:::agent
        RAGNode[📚 Retriever Node]:::agent
        PolicyNode[⚖️ Policy Decision Node]:::agent
        ReportNode[📝 Report Generation Node]:::agent
    end

    subgraph "Data & Vector Store"
        DB[(🗄️ ChromaDB <br> ONNX Embeddings)]:::data
        Docs[📄 RBI/NBFC Docs]:::data
        LLM{🧠 Groq LLM <br> llama-3.3-70b}:::data
    end

    User -->|Profile & Chat| UI
    UI <-->|JSON State| API
    API -->|Turn Trigger| Guard
    Guard -->|Valid Request| RAGNode
    RAGNode -->|Semantic Query| DB
    Docs -.->|Ingested via ONNX| DB
    DB -.->|Citations| RAGNode
    RAGNode --> PolicyNode
    PolicyNode -->|Risk Flags| ReportNode
    ReportNode <-->|Summarization / Translation| LLM
    ReportNode --> API
    API --> UI
    UI -->|Downloads| Report
```

> **Why ONNX over PyTorch?** 
> To support lightning-fast ultra-lightweight deployments on Streamlit Community Cloud and Render Free Tier, we fully modernized the vector stack. `SentenceTransformers` and `PyTorch` (2GB+) were replaced by Chroma's native **`ONNXMiniLM_L6_V2`** engine (50MB), yielding the exact same inference outputs at 5% of the memory footprint.

---

## 📑 The Professional Visual Report (LaTeX)

For deep academic or architectural review, compile our highly structured **LaTeX Visual Technical Report**. It includes technical depth, data-flow diagrams, and viva-voce talking points.

- **LaTeX Source:** [`docs/CreditSense_M2_Professional_Report.tex`](docs/CreditSense_M2_Professional_Report.tex)
- **Compiled PDF:** [`docs/CreditSense_M2_Professional_Report.pdf`](docs/CreditSense_M2_Professional_Report.pdf) 
*(Note: To generate the newest PDF, compile the `.tex` file locally or on Overleaf since automated GitHub compilation is skipped for file size).*

> 💡 **Tip:** Use these `docs/` files directly as your script and visual aid to build your professional PowerPoint (PPT) presentation!

---

## 🚀 Quick Start (Local Deployment)

Run the full dual-stack locally using the terminal commands below from the `MILESTONE_2/creditsense` directory.

```bash
cd "MILESTONE_2/creditsense"

# 1. Install dependencies
pip install -r requirements.txt

# 2. Ingest Reference Documents (Optional: if chroma_store is missing)
python3 scripts/ingest.py --source-dir "../../RAG files"

# 3. Boot the API Layer
bash scripts/run_backend.sh

# 4. Open a second terminal and Boot the UI Layer
bash scripts/run_streamlit.sh
```

**Local Endpoints**:
- 🎨 Frontend: `http://localhost:8502`
- ⚙️ Backend API: `http://localhost:8010`

---

## 📂 Project Navigation

| Directory | Purpose |
|---|---|
| 🌲 [`MILESTONE_2/`](MILESTONE_2/) | **Primary Codebase:** The entire Streamlit + FastAPI + LangGraph architecture. |
| 📚 [`docs/`](docs/) | **Documentation Map:** Deep dives into API, deployment, design specs, and LaTeX reports. |
| 🗃️ [`RAG files/`](RAG%20files/) | **Corpus:** The raw regulatory documents feeding the intelligence layer. |
| 🕰️ [`MILESTONE 1/`](MILESTONE%201/) | **Legacy:** The original prototype terminal app. |
