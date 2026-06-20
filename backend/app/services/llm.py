from openai import OpenAI
from app.core.config import OPENAI_API_KEY
import json
import re

client = OpenAI(api_key=OPENAI_API_KEY)


# ── Prompts ────────────────────────────────────────────────────────────────

DETECT_PROMPT = """You are a document classifier. Given the text below, identify the document type.
Return ONLY a JSON object with this exact shape — no markdown, no explanation:
{
  "doc_type": "<one of: invoice, legal, resume, medical, general>",
  "confidence": <0.0 to 1.0>,
  "reason": "<one sentence>"
}"""

EXTRACTION_PROMPTS = {
    "invoice": """Extract all invoice/receipt fields from the document text below.
Return ONLY a JSON object — no markdown, no explanation:
{
  "vendor_name": "",
  "vendor_address": "",
  "invoice_number": "",
  "invoice_date": "",
  "due_date": "",
  "line_items": [{"description": "", "quantity": "", "unit_price": "", "total": ""}],
  "subtotal": "",
  "tax": "",
  "total_amount": "",
  "payment_terms": "",
  "currency": "",
  "notes": ""
}
If a field is not found, use null. Extract as accurately as possible.""",

    "legal": """Extract all legal document fields from the text below.
Return ONLY a JSON object — no markdown, no explanation:
{
  "document_title": "",
  "parties": [{"role": "", "name": "", "address": ""}],
  "effective_date": "",
  "expiry_date": "",
  "governing_law": "",
  "jurisdiction": "",
  "key_clauses": [{"clause_type": "", "summary": ""}],
  "obligations": [],
  "penalties": "",
  "signatures": [{"party": "", "date": ""}],
  "document_id": ""
}
If a field is not found, use null.""",

    "resume": """Extract all resume/CV fields from the text below.
Return ONLY a JSON object — no markdown, no explanation:
{
  "full_name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "summary": "",
  "education": [{"degree": "", "institution": "", "year": "", "grade": ""}],
  "experience": [{"title": "", "company": "", "duration": "", "responsibilities": []}],
  "skills": [],
  "certifications": [],
  "projects": [{"name": "", "tech_stack": "", "description": ""}],
  "achievements": []
}
If a field is not found, use null.""",

    "medical": """Extract all medical document fields from the text below.
Return ONLY a JSON object — no markdown, no explanation:
{
  "patient_name": "",
  "patient_id": "",
  "date_of_birth": "",
  "date_of_visit": "",
  "doctor_name": "",
  "facility": "",
  "diagnosis": [],
  "medications": [{"name": "", "dosage": "", "frequency": ""}],
  "procedures": [],
  "allergies": [],
  "vitals": {"blood_pressure": "", "heart_rate": "", "temperature": "", "weight": ""},
  "notes": "",
  "follow_up": ""
}
If a field is not found, use null.""",

    "general": """Extract all meaningful structured fields from the document text below.
Identify every key piece of information and return ONLY a JSON object — no markdown, no explanation.
The keys should be descriptive snake_case field names, values should be the extracted data.
Include: names, dates, IDs, amounts, addresses, emails, phone numbers, organizations,
reference numbers, and any domain-specific fields present.
Group related fields logically. If a field is not found, use null."""
}


def detect_document_type(text: str) -> dict:
    """Use GPT to detect the document type."""
    truncated = text[:3000]  # Keep token cost low for detection
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": DETECT_PROMPT},
                {"role": "user", "content": f"Document text:\n\n{truncated}"}
            ],
            temperature=0,
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"doc_type": "general", "confidence": 0.5, "reason": str(e)}


def extract_fields(text: str, doc_type: str) -> dict:
    """Use GPT-4o to extract structured fields based on document type."""
    prompt = EXTRACTION_PROMPTS.get(doc_type, EXTRACTION_PROMPTS["general"])
    truncated = text[:8000]  # Stay within token limits

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Document text:\n\n{truncated}"}
        ],
        temperature=0,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


def generate_summary(text: str, doc_type: str, fields: dict) -> str:
    """Generate a human-readable summary of what was extracted."""
    fields_str = json.dumps(fields, indent=2)[:1500]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a document analyst. Write a concise 2-3 sentence summary of what this document is and the key information extracted. Be specific, not generic."},
            {"role": "user", "content": f"Document type: {doc_type}\n\nExtracted fields:\n{fields_str}\n\nOriginal text snippet:\n{text[:500]}"}
        ],
        temperature=0.3,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


def calculate_confidence(fields: dict) -> float:
    """Calculate extraction confidence based on how many fields were populated."""
    if not fields:
        return 0.0

    def count_filled(obj, depth=0):
        if depth > 4:
            return 0, 0
        filled, total = 0, 0
        if isinstance(obj, dict):
            for v in obj.values():
                f, t = count_filled(v, depth + 1)
                filled += f; total += t
        elif isinstance(obj, list):
            for item in obj:
                f, t = count_filled(item, depth + 1)
                filled += f; total += t
        else:
            total = 1
            if obj is not None and str(obj).strip() not in ("", "null", "None"):
                filled = 1
        return filled, total

    filled, total = count_filled(fields)
    return round(filled / total, 2) if total > 0 else 0.0
