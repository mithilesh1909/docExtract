# DocExtract AI — Intelligent Document Field Extraction

A production-ready AI pipeline that auto-detects document type and extracts structured fields from any document using **GPT-4o**.

Built by **Mithilesh Singh** · [GitHub](https://github.com/mithilesh1909)

---

## What It Does

Upload a PDF, DOCX, TXT, or image → AI detects the document type → GPT-4o extracts every named field into clean JSON.

| Document Type | Fields Extracted |
|---|---|
| 🧾 Invoice / Receipt | Vendor, line items, totals, tax, payment terms |
| ⚖️ Legal / Contract | Parties, clauses, dates, jurisdiction, obligations |
| 👤 Resume / CV | Education, experience, skills, projects, contacts |
| 🏥 Medical Record | Patient info, diagnosis, medications, vitals |
| 📄 General | All key entities auto-detected |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | Python 3.12, FastAPI, Uvicorn |
| **AI** | OpenAI GPT-4o (extraction) + GPT-4o-mini (classification) |
| **Text Extraction** | pdfplumber (PDF), python-docx (DOCX), pytesseract (images) |
| **Validation** | Pydantic v2 |
| **Frontend** | Vanilla HTML/CSS/JS (zero build step, served by FastAPI) |

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/mithilesh1909/docextract-ai.git
cd docextract-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your OpenAI key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-...

# 4. Run
uvicorn main:app --reload --port 8000

# Open http://localhost:8000
# API docs at http://localhost:8000/api/docs
```

---

## API Usage

### Extract fields from a document
```bash
curl -X POST http://localhost:8000/api/extract \
  -F "file=@invoice.pdf"
```

### Force a document type
```bash
curl -X POST http://localhost:8000/api/extract \
  -F "file=@contract.pdf" \
  -F "force_type=legal"
```

### Response shape
```json
{
  "filename": "invoice.pdf",
  "doc_type": "invoice",
  "doc_type_confidence": 0.97,
  "doc_type_reason": "Contains vendor info, line items, and a total amount",
  "fields": {
    "vendor_name": "Acme Corp",
    "invoice_number": "INV-2024-0042",
    "total_amount": "$4,320.00",
    "line_items": [...]
  },
  "extraction_confidence": 0.84,
  "summary": "An invoice from Acme Corp...",
  "char_count": 1420,
  "processed_at": "2024-06-20T10:30:00Z"
}
```

---

## Deploying to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set these:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable**: `OPENAI_API_KEY` = your key
5. Click Deploy — live in ~2 minutes

---

## Project Structure

```
docextract-ai/
├── main.py                    # FastAPI app entry point
├── requirements.txt
├── .env.example               # Copy to .env and add your key
├── render.yaml                # One-click Render deploy
├── app/
│   ├── core/
│   │   └── config.py          # Settings from .env
│   ├── models/
│   │   └── schemas.py         # Pydantic response models
│   ├── routers/
│   │   └── extract.py         # POST /api/extract endpoint
│   └── services/
│       ├── extractor.py       # PDF/DOCX/image text extraction
│       └── llm.py             # OpenAI GPT-4o integration
└── static/
    └── index.html             # Frontend UI (served by FastAPI)
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | Your OpenAI API key |
| `APP_ENV` | ✗ | `development` | `development` or `production` |
| `MAX_FILE_SIZE_MB` | ✗ | `10` | Max upload size in MB |
