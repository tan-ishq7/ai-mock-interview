"""Evaluation and report generation endpoints."""

from fastapi import APIRouter, HTTPException

from backend.database.supabase_client import get_supabase
from backend.evaluation.report_generator import generate_report

router = APIRouter()


from backend.database.local_store import get_report as get_cached_report


@router.post("/{session_id}/evaluate")
async def evaluate_session(session_id: str):
    """Trigger evaluation and report generation for a completed interview."""
    try:
        report = generate_report(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {exc}"
        ) from exc

    return {"status": "ok", "report": report}


@router.get("/{session_id}/report")
@router.get("/report/{session_id}")
async def get_report(session_id: str):
    """Retrieve a previously generated report."""
    cached = get_cached_report(session_id)
    if cached:
        return {"status": "ok", "report": cached}

    try:
        supabase = get_supabase()
        result = (
            supabase.table("reports")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return {"status": "ok", "report": result.data[0]}
    except Exception:
        pass

    raise HTTPException(
        status_code=404,
        detail="Report not found. Run POST /evaluate first.",
    )
