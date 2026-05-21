"""
Behavioral assessment scorer for Phase 5.

Supports two LLM providers:
  - Gemini (active)  — gemini-2.5-flash via google-genai
  - OpenAI (inactive) — GPT-5.4 via the Responses API
"""

import json
import logging
from dataclasses import dataclass

from backend.config import settings
from backend.interview.prompt_templates import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class BehavioralScore:
    visionary: float  # 0-10
    grounded: float   # 0-10
    teamplayer: float  # 0-10
    composite_pct: float  # 0-100
    per_question: list[dict]


BEHAVIORAL_EVAL_PROMPT = """\
Evaluate the candidate's responses to the behavioral interview questions below.

For each response, score on three dimensions (0-10 scale):
1. Visionary: Forward-thinking, ambition, clear long-term goals, bigger-picture awareness.
2. Grounded: Backed by concrete examples, practical awareness, realistic self-assessment.
3. Team Player: Collaboration skills, empathy, interpersonal navigation.

Conversation:
{conversation}

Return ONLY a JSON object:
{{
    "per_question": [
        {{
            "question_summary": "<brief question>",
            "visionary": <float 0-10>,
            "grounded": <float 0-10>,
            "teamplayer": <float 0-10>,
            "notes": "<1 sentence>"
        }}
    ],
    "overall_visionary": <float 0-10>,
    "overall_grounded": <float 0-10>,
    "overall_teamplayer": <float 0-10>
}}
"""


def compute_behavioral_score(
    phase5_conversation: list[dict[str, str]],
) -> BehavioralScore:
    """Evaluate behavioral responses using the configured LLM."""
    conversation_text = "\n".join(
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in phase5_conversation
    )

    prompt = BEHAVIORAL_EVAL_PROMPT.format(conversation=conversation_text)
    full_prompt = SYSTEM_PROMPT + "\n\n" + prompt

    provider = settings.LLM_PROVIDER.lower()

    # ── CLAUDE (active) ──
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

    # ── GEMINI ──
    elif provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        )
        raw = response.text.strip()

    # ── OPENAI (commented out — uncomment when you have credits) ──
    # elif provider == "openai":
    #     from openai import OpenAI
    #     client = OpenAI(api_key=settings.OPENAI_API_KEY)
    #     response = client.responses.create(
    #         model="gpt-5.4",
    #         reasoning={"effort": "low"},
    #         input=[{"role": "user", "content": full_prompt}],
    #     )
    #     raw = response.output_text.strip()

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Behavioral eval returned non-JSON: %s", raw[:300])
        data = {
            "overall_visionary": 5.0,
            "overall_grounded": 5.0,
            "overall_teamplayer": 5.0,
            "per_question": [],
        }

    visionary = float(data.get("overall_visionary", 5.0))
    grounded = float(data.get("overall_grounded", 5.0))
    teamplayer = float(data.get("overall_teamplayer", 5.0))
    composite = (visionary + grounded + teamplayer) / 30 * 100

    return BehavioralScore(
        visionary=visionary,
        grounded=grounded,
        teamplayer=teamplayer,
        composite_pct=round(composite, 1),
        per_question=data.get("per_question", []),
    )
