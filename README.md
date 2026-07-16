# Plateforme IA TGR — Intelligent Document Processing Platform

> Engineering Internship Project — General Treasury of the Kingdom (TGR)
> International University of Rabat (UIR) — Academic Year 2025/2026
> Internship Supervisor: Mr. Mohssine Dardar

---

## Overview

An AI-powered platform for processing bank account opening dossiers at the TGR (Tresorerie Generale du Royaume), built as part of the Morocco Digital 2030 national strategy. The platform automates document digitization, compliance verification, and regulatory assistance for TGR banking agents.

---

## Features

- **OCR Extraction** — EasyOCR for printed Arabic/French text + Gemini 2.5 Flash Vision for handwritten fields
- **Batch OCR** — Process up to 20 documents simultaneously with real-time progress bar
- **Compliance Verification** — Deterministic rule engine covering 7 client types (OLYMPIC reference system)
- **SQLite History** — Full dossier history with versioning and statistics
- **PDF Reports** — Official compliance reports via ReportLab (cover page, anomaly details, signature page)
- **RAG Assistant** — Regulatory Q&A in natural language with ChromaDB + Ollama (local) or Gemini 2.5 Flash (API)
- **Analytics Dashboard** — 6 interactive Plotly charts + full audit trail with CSV export
- **Email Notifications** — Automatic alerts via Resend API (anomaly, OCR, question triggers)
- **Role-Based Authentication** — Admin / Agent / Auditeur with SQLite + SHA-256
- **User Management** — Admin-only user creation, role assignment, and management
- **Dual AI Mode** — Switch between 100% local (Ollama) and cloud (Gemini) from Settings page

---

## Tech Stack

| Component | Technology | Version | Role |
|---|---|---|---|
| Web framework | Streamlit | 1.35+ | Multi-page web application |
| OCR engine | EasyOCR | 1.7+ | Bilingual Arabic/French OCR |
| Vision OCR | Gemini 2.5 Flash | v1 | Handwritten document extraction |
| Image processing | OpenCV | 4.x | Preprocessing + stamp detection |
| PDF conversion | pdf2image + poppler | 3.x | PDF to image for OCR |
| Local LLM server | Ollama | 0.3+ | On-premises model serving |
| Local LLM | Mistral 7B | 0.3 | Local text generation |
| Cloud LLM | Gemini 2.5 Flash | v1 | Fast cloud generation (free tier) |
| Embeddings | nomic-embed-text | v1.5 | 768-dimensional vector encoding |
| Vector database | ChromaDB | 1.5+ | Semantic search with metadata filtering |
| PDF generation | ReportLab | 4.x | Compliance report generation |
| Email service | Resend API | v1 | Notifications + email composer |
| Authentication | SQLite + hashlib | built-in | Secure local user management |
| Charts | Plotly | 5.x | Interactive analytics |
| Language | Python | 3.11 | Primary development language |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/nour629/tgr-plateforme-ia.git
cd tgr-plateforme-ia
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama and models

Download Ollama from https://ollama.ai then run:

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

### 5. Configure the platform

Edit `config.json` at the project root:

```json
{
  "mode": "gemini",
  "ollama_model": "mistral",
  "gemini_api_key": "AQ.Ab8RN6JNTR_sd1nztGIz36_k5XEMrHE4NMuR3fd5lboAiFToyA",
  "notifications_enabled": false,
  "resend_api_key": "",
  "email_to": "",
  "email_from": "TGR Platform <noreply@resend.dev>",
  "notify_anomalie": true,
  "notify_ocr": true,
  "notify_assistant": false
}
```

Get a free Gemini API key at https://aistudio.google.com

### 6. Run the application

```bash
streamlit run main.py
```

Open http://localhost:8501 in your browser.

---

## Default Accounts

| Username | Password | Role | Access |
|---|---|---|---|
| admin | admin123 | Administrator | All modules + Settings + User Management |
| agent1 | agent123 | Agent | OCR, Anomalies, Assistant, Dashboard |
| agent2 | agent123 | Agent | OCR, Anomalies, Assistant, Dashboard |
| auditeur | audit123 | Auditeur | Dashboard + Audit trail (read-only) |

---

## Project Structure

```
tgr_projet/
├── main.py                       # Main entry point + home dashboard
├── auth.py                       # Authentication + RBAC + login page
├── styles.py                     # Global CSS + sidebar + UI components
├── audit.py                      # Centralized audit logging
├── config.json                   # Mode config + API keys
├── users.db                      # SQLite user database
├── dossiers.db                   # SQLite compliance history
├── audit_log.json                # Full audit trail
├── requirements.txt              # Python dependencies
├── assets/
│   └── TGR_LOGO.jpg             # Official TGR logo
├── .streamlit/
│   └── config.toml              # Streamlit theme configuration
├── pages/
│   ├── 1_OCR.py                 # Simple OCR extraction module
│   ├── 2_Anomalies.py           # Compliance verification + history + PDF
│   ├── 3_Assistant.py           # RAG regulatory assistant
│   ├── 4_Dashboard.py           # Analytics dashboard + audit trail
│   ├── 5_Parametres.py          # Settings (mode, API key, notifications)
│   ├── 6_Utilisateurs.py        # User management (Admin only)
│   └── 7_OCR_Lot.py             # Batch OCR processing
└── core/
    ├── notifications.py          # Resend email notifications
    ├── ml/
    │   ├── client_compliance.py  # OLYMPIC rule engine (7 client types)
    │   ├── dossiers_db.py        # SQLite dossier history
    │   └── rapport_pdf.py        # ReportLab PDF generation
    └── rag/
        ├── chatbot.py            # RAG pipeline (Ollama + Gemini)
        ├── indexer.py            # PDF indexing pipeline
        ├── vector_store.py       # ChromaDB interface
        └── chroma_db/            # Persistent vector index (37 chunks)
```

---

## AI Modes

| Feature | Mode Local (Ollama) | Mode API (Gemini Flash) |
|---|---|---|
| Internet required | No | Yes |
| Data confidentiality | 100% on-premises | Google cloud |
| OCR engine | EasyOCR | Gemini 2.5 Flash Vision |
| RAG generation | Mistral 7B | Gemini 2.5 Flash |
| Response time | 60-180 seconds | 3-10 seconds |
| Cost | Free | Free tier (Google AI Studio) |
| Best for | Production | Demonstrations |

Switch between modes from the Settings page — no code changes required.

---

## Compliance Engine — 7 Client Types

| Client Type | Key Required Fields | Key Required Documents |
|---|---|---|
| Individual | Nom, Prenom, CIN, Adresse | CIN copy, Request, Signature specimen |
| Civil servant | Nom, CIN, Employeur, PPR | CIN, Salary domiciliation |
| Company | Raison sociale, RC | Articles, RC extract, Signatory PV |
| Association | Nom, President, Date certificat | Articles, GA minutes, Deposit certificate |
| Cooperative | Nom, Code ODCO | Articles, GA minutes, ODCO approval |
| Public institution | Denomination, Responsable | Creation text, Appointment decision |
| Regisseur | Nom regie, Code regie | Authorization, Appointment decree |

---

## Performance Benchmarks

| Operation | Duration | Mode |
|---|---|---|
| OCR single page (EasyOCR) | 45-90s | Local — i5-6300U, 16GB, no GPU |
| OCR single page (Gemini Vision) | 8-15s | Gemini API |
| Compliance check (5 dossiers) | < 0.5s | Python rule engine |
| PDF report generation | 2-3s | ReportLab in-memory |
| RAG query (Ollama/Mistral) | 60-180s | Local CPU inference |
| RAG query (Gemini Flash) | 3-10s | Gemini API |
| Email notification | 1-3s | Resend API |

---

## Author

**Nour ElHouda TAROUJENA**
Student ID: 120386
Computer Engineering — AI & Data Science
International University of Rabat (UIR)

Academic Supervisor: Mme. Basma GUERMAH
Company Supervisor: Mr. Mohssine Dardar — TGR

---

## License

Confidential — Internal TGR use only.
This project was developed as part of an engineering internship at the General Treasury of the Kingdom of Morocco.
Unauthorized use, reproduction, or distribution is strictly prohibited.
