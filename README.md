# 🏦 CreditSense v2: AI-Powered Loan Approval Agent

![Status: Milestone 2 Deployed](https://img.shields.io/badge/Status-Milestone_2_Deployed-success?style=for-the-badge&logoColor=white)
![Stack: Streamlit | FastAPI | LangGraph](https://img.shields.io/badge/Stack-Streamlit_|_FastAPI_|_LangGraph-blue?style=for-the-badge&logoColor=white)
![Retrieval: ChromaDB | ONNX MiniLM](https://img.shields.io/badge/Retrieval-ChromaDB_|_ONNX_MiniLM-orange?style=for-the-badge&logoColor=white)

**CreditSense v2** is a professional, bilingual (English/Hindi) AI credit assessment platform. It combines a deterministic policy engine, RAG-backed regulatory knowledge (RBI & NBFC guidelines), and LangGraph agent orchestration to provide explainable loan decisions.

---

## 📊 Visual System Architecture

Understanding how CreditSense works is critical for auditability. We utilize a **hybrid deterministic-AI pipeline** that ensures strict policy enforcement with natural language reasoning.

![CreditSense System Architecture](docs/arhctecture_diagram.png)

> **Why ONNX over PyTorch?**
> To support lightning-fast ultra-lightweight deployments on Streamlit Community Cloud and Render Free Tier, we fully modernized the vector stack. `SentenceTransformers` and `PyTorch` (2GB+) were replaced by Chroma's native **`ONNXMiniLM_L6_V2`** engine (50MB), yielding the exact same inference outputs at 5% of the memory footprint.

---

## 👥 Core Team & Project Contributions

![Milestone: Complete](https://img.shields.io/badge/Milestone-Complete-blue?style=flat-square)

| Member | Role | Contribution |
| --- | --- | --- |
| 👨‍💻 Mitul | Project Lead and Full-Stack Development | Spearheaded the overall software architecture and engineered the FastAPI backend, Streamlit frontend, LangGraph orchestration, local RAG integration, and deployment pipelines. |
| 📚 Vaibhav | Technical Documentation and Report Strategy | Structured and developed the comprehensive project documentation, architecture records, READMEs, and formal technical submission report. |
| 🖥️ Sarvjeet | Media and Presentation Lead | Designed and delivered the final project presentation, mapped technical flow into digestible visual slides, and produced the final demo walkthrough video. |
| 💡 Hardik | Product Ideation and Strategy | Led initial concept framing, conceptualized RBI guideline integration, structured business logic requirements (for example DTI and LTV), and defined target user experience. |

---

## 📑 The Professional Visual Report (Agentic AI Whitepaper)

For deep academic or architectural review, we have included a highly structured **Agentic AI Whitepaper**. It fundamentally details how the architectural problem of LLM hallucination is solved through our LangGraph Multi-Agent implementation.

- **Markdown Source (Easily exportable to PDF):** [`docs/CreditSense_M2_Professional_Report.md`](docs/CreditSense_M2_Professional_Report.md)
- **LaTeX Source:** [`docs/CreditSense_M2_Professional_Report.tex`](docs/CreditSense_M2_Professional_Report.tex)

*(Note: Open the `.md` file in VS Code and click "Open Preview" -> Right-click -> "Export to PDF" to instantly generate your highly-formatted official report!)*

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

## 🌐 Live Deployment

Use the following public deployment links for direct access:

- 🎨 Streamlit App: https://genailoanapproval-fdwemcnw96p8fgwpen6xcd.streamlit.app/
- ⚙️ Backend Health API: https://gen-ai-loan-approval.onrender.com/api/v1/health

---

## 📂 Project Navigation

| Directory | Purpose |
| --- | --- |
| 🌲 [`MILESTONE_2/`](MILESTONE_2/) | **Primary Codebase:** The entire Streamlit + FastAPI + LangGraph architecture. |
| 📚 [`docs/`](docs/) | **Documentation Map:** Deep dives into API, deployment, design specs, and LaTeX reports. |
| 🗃️ [`RAG files/`](RAG%20files/) | **Corpus:** The raw regulatory documents feeding the intelligence layer. |
| 🕰️ [`MILESTONE 1/`](MILESTONE%201/) | **Legacy:** The original prototype terminal app. |
