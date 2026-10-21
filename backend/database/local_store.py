"""
In-memory resilient fallback store for candidates, sessions, and reports.

Ensures the mock interview platform continues to operate with full functionality
even when external database connectivity (e.g. Supabase paused or network offline)
is interrupted.
"""

from typing import Any

_candidates: dict[str, dict[str, Any]] = {}
_reports: dict[str, dict[str, Any]] = {}
_session_records: dict[str, dict[str, Any]] = {}
_conversation_history: dict[str, list[dict[str, Any]]] = {}


def save_candidate(candidate_id: str, data: dict[str, Any]) -> None:
    _candidates[candidate_id] = data


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    return _candidates.get(candidate_id)


def save_report(session_id: str, report_data: dict[str, Any]) -> None:
    _reports[session_id] = report_data


def get_report(session_id: str) -> dict[str, Any] | None:
    return _reports.get(session_id)


def record_message(session_id: str, msg: dict[str, Any]) -> None:
    if session_id not in _conversation_history:
        _conversation_history[session_id] = []
    _conversation_history[session_id].append(msg)


def get_messages(session_id: str) -> list[dict[str, Any]]:
    return _conversation_history.get(session_id, [])
