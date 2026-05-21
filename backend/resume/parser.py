"""
Resume PDF parser.

Supports two LLM providers:
  - Gemini (active)  — uses google-genai SDK with gemini-2.5-flash
  - OpenAI (inactive) — uses GPT-5.4 via the Responses API

Switch providers by setting LLM_PROVIDER=gemini or LLM_PROVIDER=openai in .env.
"""

import base64
import json
import logging
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a precise resume parser. You will receive a PDF resume.
Extract the following sections and return ONLY valid JSON (no markdown fences,
no commentary). If a section is not present, use null for strings, an empty
list for lists, or an empty dict for dicts.

Return this exact JSON schema:

{
  "name": "<candidate full name>",
  "email": "<email address or null>",
  "about_me": "<summary / objective / about section text or null>",
  "education": [
    {
      "degree": "<degree name>",
      "institution": "<university / school>",
      "year": "<graduation year or date range>",
      "details": "<GPA, honors, relevant coursework, etc. or null>"
    }
  ],
  "work_experience": [
    {
      "title": "<job title>",
      "company": "<company name>",
      "period": "<date range>",
      "key_skills": ["<skill1>", "<skill2>"],
      "responsibilities": ["<responsibility1>", "<responsibility2>"]
    }
  ],
  "projects": [
    {
      "title": "<project title>",
      "description": "<short description>",
      "technologies": ["<tech1>", "<tech2>"]
    }
  ],
  "technical_skills": {
    "programming": ["<lang1>", "<lang2>"],
    "frameworks": ["<fw1>", "<fw2>"],
    "tools": ["<tool1>", "<tool2>"]
  },
  "publications": ["<publication citation string>"],
  "identified_field": "<primary ML/tech field, e.g. NLP, Computer Vision, Reinforcement Learning, Backend Engineering>",
  "primary_project": {
    "title": "<most significant project title>",
    "description": "<description>",
    "technologies": ["<tech1>"]
  },
  "secondary_project": {
    "title": "<second most significant project title>",
    "description": "<description>",
    "technologies": ["<tech1>"]
  }
}

Rules:
- primary_project and secondary_project should be chosen from the projects list
  (pick the most impressive / substantial ones). If only one project exists,
  set secondary_project to null.
- identified_field should reflect the candidate's dominant area of expertise.
- Return ONLY the JSON object. No extra text.
"""


# =========================================================================
# GEMINI PROVIDER (active)
# =========================================================================
def _parse_with_gemini(file_bytes: bytes) -> str:
    """Send PDF to Gemini and get structured JSON back.

    Tries gemini-2.5-flash first, falls back to gemini-2.0-flash if 503.
    """
    import time
    from google import genai
    from google.genai import errors as genai_errors

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")

    contents = [
        {
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64,
                    }
                },
                {"text": EXTRACTION_PROMPT},
            ]
        }
    ]

    # Try models in order: 2.5-flash (best) -> 2.0-flash (fallback)
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    last_error = None

    for model_name in models:
        for attempt in range(2):  # 2 attempts per model
            try:
                logger.info("Trying %s (attempt %d)", model_name, attempt + 1)
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                )
                return response.text.strip()
            except (genai_errors.ServerError, genai_errors.APIError) as e:
                last_error = e
                logger.warning("%s attempt %d failed: %s", model_name, attempt + 1, e)
                if attempt == 0:
                    time.sleep(2)  # brief pause before retry

    raise RuntimeError(f"All Gemini models unavailable: {last_error}")


# =========================================================================
# OPENAI PROVIDER (commented out — uncomment when you have OpenAI credits)
# =========================================================================
# def _parse_with_openai(file_bytes: bytes) -> str:
#     """Send PDF to GPT-5.4 via the Responses API and get structured JSON."""
#     from openai import OpenAI
#
#     if not settings.OPENAI_API_KEY:
#         raise RuntimeError("OPENAI_API_KEY must be set in the .env file.")
#     client = OpenAI(api_key=settings.OPENAI_API_KEY)
#
#     pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
#
#     response = client.responses.create(
#         model="gpt-5.4",
#         reasoning={"effort": "low"},
#         input=[
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "input_file",
#                         "filename": "resume.pdf",
#                         "file_data": f"data:application/pdf;base64,{pdf_b64}",
#                     },
#                     {
#                         "type": "input_text",
#                         "text": EXTRACTION_PROMPT,
#                     },
#                 ],
#             }
#         ],
#     )
#
#     return response.output_text.strip()


# =========================================================================
# CLAUDE / ANTHROPIC PROVIDER (active)
# =========================================================================
def _parse_with_claude(file_bytes: bytes) -> str:
    """Send PDF to Claude Sonnet 4 and get structured JSON back."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    return message.content[0].text.strip()


# =========================================================================
# Main entry point
# =========================================================================
async def parse_resume_pdf(file_bytes: bytes) -> dict[str, Any]:
    """Parse raw PDF bytes of a resume and return structured sections.

    Dispatches to the configured LLM provider (Claude, Gemini, or OpenAI).

    Parameters
    ----------
    file_bytes:
        Raw bytes of the uploaded PDF file.

    Returns
    -------
    dict
        Structured resume data.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "claude":
        raw_text = _parse_with_claude(file_bytes)
    elif provider == "gemini":
        raw_text = _parse_with_gemini(file_bytes)
    # elif provider == "openai":                    # <-- uncomment for OpenAI
    #     raw_text = _parse_with_openai(file_bytes)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'claude', 'gemini', or 'openai'.")

    # Strip markdown code fences if the model wraps the JSON
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1]).strip()

    try:
        parsed: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned non-JSON response: %s", raw_text[:500])
        raise ValueError(
            "Failed to parse structured data from the resume. "
            "LLM did not return valid JSON."
        ) from exc

    parsed["raw_text"] = raw_text
    return parsed
