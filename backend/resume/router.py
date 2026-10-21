"""Resume upload and parsing endpoints."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.database.supabase_client import get_supabase
from backend.resume.parser import parse_resume_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


from backend.database.local_store import save_candidate


def _store_candidate(parsed: dict[str, Any], candidate_id: str) -> str:
    """Insert the parsed resume into the Supabase candidates table."""
    supabase = get_supabase()

    resume_sections = {
        "about_me": parsed.get("about_me"),
        "education": parsed.get("education"),
        "work_experience": parsed.get("work_experience"),
        "projects": parsed.get("projects"),
        "technical_skills": parsed.get("technical_skills"),
        "publications": parsed.get("publications"),
    }

    row = {
        "id": candidate_id,
        "name": parsed.get("name") or "Unknown",
        "email": parsed.get("email") or "unknown@example.com",
        "resume_raw_text": parsed.get("raw_text", ""),
        "resume_sections": resume_sections,
        "identified_field": parsed.get("identified_field", ""),
        "primary_project": parsed.get("primary_project") or {},
        "secondary_project": parsed.get("secondary_project") or {},
    }

    result = (
        supabase.table("candidates")
        .insert(row)
        .execute()
    )

    return result.data[0]["id"] if result.data else candidate_id


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Accept a PDF resume, parse it, store in Supabase/local cache, and return structured data."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()

    try:
        parsed = await parse_resume_pdf(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    candidate_id = str(uuid.uuid4())
    candidate_record = {
        "id": candidate_id,
        "name": parsed.get("name") or "Unknown",
        "email": parsed.get("email") or "unknown@example.com",
        "resume_raw_text": parsed.get("raw_text", ""),
        "resume_sections": {
            "about_me": parsed.get("about_me"),
            "education": parsed.get("education"),
            "work_experience": parsed.get("work_experience"),
            "projects": parsed.get("projects"),
            "technical_skills": parsed.get("technical_skills"),
            "publications": parsed.get("publications"),
        },
        "identified_field": parsed.get("identified_field", ""),
        "primary_project": parsed.get("primary_project") or {},
        "secondary_project": parsed.get("secondary_project") or {},
    }

    # Always persist locally first so interview can start regardless of DB state
    save_candidate(candidate_id, candidate_record)

    storage_warning: str | None = None
    try:
        _store_candidate(parsed, candidate_id)
    except Exception as exc:
        logger.warning("Supabase storage unavailable (%s). Cached in local session store.", exc)
        storage_warning = "Operating in local resilient mode (Supabase unreachable). Data saved locally."

    response: dict[str, Any] = {
        "status": "ok",
        "candidate_id": candidate_id,
        "data": parsed,
    }
    if storage_warning:
        response["warning"] = storage_warning
    return response
