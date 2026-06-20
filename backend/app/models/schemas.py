from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class ExtractionResult(BaseModel):
    filename: str
    doc_type: str
    doc_type_confidence: float
    doc_type_reason: str
    fields: dict[str, Any]
    extraction_confidence: float
    summary: str
    char_count: int
    processed_at: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
