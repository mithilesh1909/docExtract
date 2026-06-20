from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from datetime import datetime, timezone
import traceback

from app.core.config import MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS
from app.services.extractor import extract_text
from app.services.llm import detect_document_type, extract_fields, generate_summary, calculate_confidence
from app.models.schemas import ExtractionResult
from pathlib import Path

router = APIRouter(prefix="/api", tags=["extraction"])


@router.post("/extract", response_model=ExtractionResult)
async def extract_document(
    file: UploadFile = File(...),
    force_type: Optional[str] = Form(None)
):
    # ── Validate file ──────────────────────────────────────────────────────
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE_BYTES // (1024*1024)}MB"
        )

    # ── Extract raw text ───────────────────────────────────────────────────
    try:
        raw_text = extract_text(file_bytes, file.filename or "file.txt")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text: {str(e)}")

    if not raw_text or len(raw_text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="Could not extract readable text from this document. Try a text-based PDF or DOCX."
        )

    # ── Detect doc type ────────────────────────────────────────────────────
    if force_type and force_type in ["invoice", "legal", "resume", "medical", "general"]:
        detection = {"doc_type": force_type, "confidence": 1.0, "reason": "Manually selected"}
    else:
        detection = detect_document_type(raw_text)

    doc_type = detection.get("doc_type", "general")

    # ── Extract fields ─────────────────────────────────────────────────────
    try:
        fields = extract_fields(raw_text, doc_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {str(e)}")

    # ── Summary + confidence ───────────────────────────────────────────────
    summary = generate_summary(raw_text, doc_type, fields)
    confidence = calculate_confidence(fields)

    return ExtractionResult(
        filename=file.filename or "unknown",
        doc_type=doc_type,
        doc_type_confidence=detection.get("confidence", 0.8),
        doc_type_reason=detection.get("reason", ""),
        fields=fields,
        extraction_confidence=confidence,
        summary=summary,
        char_count=len(raw_text),
        processed_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/supported-types")
def supported_types():
    return {
        "doc_types": ["invoice", "legal", "resume", "medical", "general"],
        "file_types": [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"]
    }
