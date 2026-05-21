"""
Final interview report generator.

Compiles scores from all phases, generates a narrative report via the
configured LLM, and stores everything in Supabase.

Supports two LLM providers:
  - Gemini (active)  — gemini-2.5-flash via google-genai
  - OpenAI (inactive) — GPT-5.4 via the Responses API
"""

import json
import logging
from typing import Any

from backend.config import settings
from backend.database.supabase_client import get_supabase
from backend.interview.engine import get_session, InterviewState
from backend.evaluation.socratic_metric import compute_socratic_score
from backend.evaluation.factual_scorer import compute_factual_score
from backend.evaluation.behavioral_scorer import compute_behavioral_score

logger = logging.getLogger(__name__)

REPORT_PROMPT = """\
You are writing a professional interview evaluation report for an ML engineering \
candidate. Based on the scores and conversation data below, write a comprehensive \
report.

Candidate: {name}
Field: {field}

Phase 2 - Project Deep-Dive #1:
  Max Depth Reached: {p2_depth}/5
  Depth Score: {p2_depth_score}%
  Hints Given: {p2_hints_given}, Recovered: {p2_hints_recovered}
  Composite Score: {p2_composite}%

Phase 3 - Project Deep-Dive #2:
  Max Depth Reached: {p3_depth}/5
  Depth Score: {p3_depth_score}%
  Hints Given: {p3_hints_given}, Recovered: {p3_hints_recovered}
  Composite Score: {p3_composite}%

Phase 4 - Factual Knowledge:
  Correct: {p4_correct}/{p4_total}
  Accuracy: {p4_accuracy}%

Phase 5 - Behavioral:
  Visionary: {p5_visionary}/10
  Grounded: {p5_grounded}/10
  Team Player: {p5_teamplayer}/10
  Composite: {p5_composite}%

Overall Score: {overall_score}/100

Write the report with these sections:
1. Executive Summary (2-3 sentences)
2. Technical Depth Analysis (strengths and gaps from phases 2-3)
3. Knowledge Assessment (phase 4 observations)
4. Behavioral Assessment (phase 5 observations)
5. Key Strengths (bullet list, 3-5 items)
6. Areas for Improvement (bullet list, 3-5 items)
7. Recommendations (2-3 actionable suggestions)
8. Overall Assessment (1 sentence verdict)

Be professional and constructive. Do not use superlatives.
"""


def generate_report(session_id: str) -> dict[str, Any]:
    """Generate the complete interview evaluation report.

    Returns a dict with all scores and the narrative report text.
    """
    state = get_session(session_id)
    if not state:
        raise ValueError(f"Session {session_id} not found in memory.")

    # ── Phase 2 scoring ──
    p2_score = compute_socratic_score(
        max_depth_reached=state.max_depth_reached.get(2, 0),
        total_questions=state.question_count.get(2, 0),
        hints_given=state.hints_given.get(2, 0),
        hints_recovered=state.hints_recovered.get(2, 0),
    )

    # ── Phase 3 scoring ──
    p3_score = compute_socratic_score(
        max_depth_reached=state.max_depth_reached.get(3, 0),
        total_questions=state.question_count.get(3, 0),
        hints_given=state.hints_given.get(3, 0),
        hints_recovered=state.hints_recovered.get(3, 0),
    )

    # ── Phase 4 scoring ──
    p4_score = compute_factual_score(state.factual_evaluations)

    # ── Phase 5 scoring ──
    p5_score = compute_behavioral_score(state.phase_conversations.get(5, []))

    # ── Overall score (weighted average) ──
    # Phase 2: 25%, Phase 3: 25%, Phase 4: 25%, Phase 5: 25%
    overall = (
        p2_score.composite_score * 0.25
        + p3_score.composite_score * 0.25
        + p4_score.accuracy_pct * 0.25
        + p5_score.composite_pct * 0.25
    )
    overall = round(overall, 1)

    # ── Generate narrative report via configured LLM ──
    prompt = REPORT_PROMPT.format(
        name=state.candidate.get("name", "Unknown"),
        field=state.candidate.get("identified_field", "ML"),
        p2_depth=p2_score.max_depth_reached,
        p2_depth_score=p2_score.depth_score_pct,
        p2_hints_given=p2_score.hints_given,
        p2_hints_recovered=p2_score.hints_recovered,
        p2_composite=p2_score.composite_score,
        p3_depth=p3_score.max_depth_reached,
        p3_depth_score=p3_score.depth_score_pct,
        p3_hints_given=p3_score.hints_given,
        p3_hints_recovered=p3_score.hints_recovered,
        p3_composite=p3_score.composite_score,
        p4_correct=p4_score.correct,
        p4_total=p4_score.total,
        p4_accuracy=p4_score.accuracy_pct,
        p5_visionary=p5_score.visionary,
        p5_grounded=p5_score.grounded,
        p5_teamplayer=p5_score.teamplayer,
        p5_composite=p5_score.composite_pct,
        overall_score=overall,
    )

    provider = settings.LLM_PROVIDER.lower()

    # ── CLAUDE (active) ──
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        report_text = response.content[0].text.strip()

    # ── GEMINI ──
    elif provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )
        report_text = response.text.strip()

    # ── OPENAI (commented out — uncomment when you have credits) ──
    # elif provider == "openai":
    #     from openai import OpenAI
    #     client = OpenAI(api_key=settings.OPENAI_API_KEY)
    #     response = client.responses.create(
    #         model="gpt-5.4",
    #         reasoning={"effort": "low"},
    #         input=[{"role": "user", "content": prompt}],
    #     )
    #     report_text = response.output_text.strip()

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    # ── Build report data ──
    phase_scores = {
        "phase_2": {
            "name": "Project Deep-Dive #1",
            "max_depth": p2_score.max_depth_reached,
            "depth_score": p2_score.depth_score_pct,
            "hints_given": p2_score.hints_given,
            "hints_recovered": p2_score.hints_recovered,
            "hint_recovery_rate": p2_score.hint_recovery_rate,
            "composite": p2_score.composite_score,
        },
        "phase_3": {
            "name": "Project Deep-Dive #2",
            "max_depth": p3_score.max_depth_reached,
            "depth_score": p3_score.depth_score_pct,
            "hints_given": p3_score.hints_given,
            "hints_recovered": p3_score.hints_recovered,
            "hint_recovery_rate": p3_score.hint_recovery_rate,
            "composite": p3_score.composite_score,
        },
        "phase_4": {
            "name": "Factual Knowledge",
            "correct": p4_score.correct,
            "partial": p4_score.partial,
            "incorrect": p4_score.incorrect,
            "total": p4_score.total,
            "accuracy": p4_score.accuracy_pct,
        },
        "phase_5": {
            "name": "Behavioral",
            "visionary": p5_score.visionary,
            "grounded": p5_score.grounded,
            "teamplayer": p5_score.teamplayer,
            "composite": p5_score.composite_pct,
            "per_question": p5_score.per_question,
        },
    }

    strengths = _extract_list_section(report_text, "Key Strengths")
    weaknesses = _extract_list_section(report_text, "Areas for Improvement")
    recommendations = _extract_list_section(report_text, "Recommendations")

    report_data = {
        "session_id": session_id,
        "candidate_id": state.candidate.get("id", ""),
        "overall_score": overall,
        "phase_scores": phase_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "report_text": report_text,
    }

    # ── Store in Supabase ──
    try:
        supabase = get_supabase()

        for phase_num, phase_data in [(2, p2_score), (3, p3_score)]:
            supabase.table("evaluations").insert(
                {
                    "session_id": session_id,
                    "phase": phase_num,
                    "score": phase_data.composite_score,
                    "max_depth_reached": phase_data.max_depth_reached,
                    "hints_given": phase_data.hints_given,
                    "hints_recovered": phase_data.hints_recovered,
                }
            ).execute()

        supabase.table("evaluations").insert(
            {
                "session_id": session_id,
                "phase": 4,
                "score": p4_score.accuracy_pct,
                "factual_correct": p4_score.correct,
                "factual_total": p4_score.total,
            }
        ).execute()

        supabase.table("evaluations").insert(
            {
                "session_id": session_id,
                "phase": 5,
                "score": p5_score.composite_pct,
                "behavioral_visionary": p5_score.visionary,
                "behavioral_grounded": p5_score.grounded,
                "behavioral_teamplayer": p5_score.teamplayer,
            }
        ).execute()

        supabase.table("reports").insert(report_data).execute()

    except Exception:
        logger.exception("Failed to store report in Supabase")

    return report_data


def _extract_list_section(text: str, header: str) -> list[str]:
    """Extract bullet items under a markdown header."""
    items = []
    in_section = False
    for line in text.split("\n"):
        if header.lower() in line.lower() and ("#" in line or "**" in line):
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "• ")):
                items.append(stripped.lstrip("-*• ").strip())
            elif stripped.startswith("#") or (stripped.startswith("**") and stripped.endswith("**")):
                break
            elif not stripped:
                continue
    return items
