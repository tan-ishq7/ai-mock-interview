"""Interview session management endpoints."""

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.database.supabase_client import get_supabase
from backend.interview.engine import (
    create_session,
    get_session,
    generate_first_message,
    process_candidate_response,
)

router = APIRouter()


class StartRequest(BaseModel):
    candidate_id: str


class RespondRequest(BaseModel):
    text: str
    anxiety_detected_voice: bool = False


@router.post("/start")
async def start_interview(body: StartRequest):
    """Create a new interview session for an existing candidate."""
    supabase = get_supabase()

    # Fetch candidate from DB
    result = (
        supabase.table("candidates")
        .select("*")
        .eq("id", body.candidate_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    candidate_data = result.data

    # Create in-memory session
    state = create_session(candidate_data)

    # Persist session to Supabase
    supabase.table("interview_sessions").insert(
        {
            "id": state.session_id,
            "candidate_id": body.candidate_id,
            "current_phase": 1,
            "status": "in_progress",
        }
    ).execute()

    # Generate opening message
    first_message = generate_first_message(state)

    # Store in conversation history
    supabase.table("conversation_history").insert(
        {
            "session_id": state.session_id,
            "phase": 1,
            "role": "assistant",
            "content": first_message,
            "depth_level": None,
            "is_hint": False,
        }
    ).execute()

    return {
        "status": "ok",
        "session_id": state.session_id,
        "phase": 1,
        "phase_name": "Background",
        "message": first_message,
    }


@router.post("/{session_id}/respond")
async def candidate_respond(session_id: str, body: RespondRequest):
    """Process a candidate response and return the next interviewer message."""
    state = get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=404, detail="Session not found. It may have expired."
        )

    supabase = get_supabase()

    # Store candidate message
    supabase.table("conversation_history").insert(
        {
            "session_id": session_id,
            "phase": state.current_phase,
            "role": "user",
            "content": body.text,
            "anxiety_detected": body.anxiety_detected_voice,
        }
    ).execute()

    # Process and get next message
    result = process_candidate_response(
        state, body.text, body.anxiety_detected_voice
    )

    # Store interviewer response
    supabase.table("conversation_history").insert(
        {
            "session_id": session_id,
            "phase": result["phase"],
            "role": "assistant",
            "content": result["message"],
            "depth_level": result.get("depth_level"),
            "is_hint": result.get("is_hint", False),
        }
    ).execute()

    # Update session phase in DB
    update_data = {"current_phase": result["phase"]}
    if result["interview_complete"]:
        update_data["status"] = "completed"

    supabase.table("interview_sessions").update(update_data).eq(
        "id", session_id
    ).execute()

    return {
        "status": "ok",
        "session_id": session_id,
        "phase": result["phase"],
        "phase_name": result["phase_name"],
        "message": result["message"],
        "depth_level": result.get("depth_level"),
        "is_hint": result.get("is_hint", False),
        "anxiety_break": result.get("anxiety_break", False),
        "interview_complete": result.get("interview_complete", False),
    }


@router.get("/{session_id}/status")
async def session_status(session_id: str):
    """Return current session metadata."""
    state = get_session(session_id)
    if not state:
        # Try DB
        supabase = get_supabase()
        result = (
            supabase.table("interview_sessions")
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Session not found.")
        return {
            "status": "ok",
            "session_id": session_id,
            "phase": result.data["current_phase"],
            "session_status": result.data["status"],
        }

    return {
        "status": "ok",
        "session_id": session_id,
        "phase": state.current_phase,
        "phase_name": state.phase_name,
        "question_count": state.question_count,
        "depth_level": state.current_depth if state.current_phase in (2, 3) else None,
        "session_status": "in_progress",
    }
