"""
Core interview orchestrator.

Manages the 5-phase interview flow, conversation state, depth tracking,
hint system, and phase transitions.

Supports two LLM providers:
  - Gemini (active)  — gemini-2.5-flash via google-genai
  - OpenAI (inactive) — GPT-5.4 via the Responses API

Switch providers by setting LLM_PROVIDER=gemini or LLM_PROVIDER=openai in .env.
"""

import json
import logging
from typing import Any
from uuid import uuid4

from backend.config import settings
from backend.interview.prompt_templates import (
    SYSTEM_PROMPT,
    PHASE1_BACKGROUND,
    PHASE2_PROJECT_DEEP_DIVE,
    PHASE3_PROJECT_DEEP_DIVE_2,
    PHASE4_FACTUAL,
    PHASE5_BEHAVIORAL,
    HINT_TEMPLATE,
    EVALUATE_RESPONSE,
)
from backend.knowledge.question_retriever import retrieve_questions_by_field

logger = logging.getLogger(__name__)

# Phase configuration
PHASE_CONFIG = {
    1: {"name": "Background", "max_questions": 3},
    2: {"name": "Project Deep-Dive #1", "max_questions": 8},
    3: {"name": "Project Deep-Dive #2", "max_questions": 8},
    4: {"name": "Factual ML Questions", "max_questions": 5},
    5: {"name": "Behavioral", "max_questions": 4},
}

BEHAVIORAL_QUESTIONS = [
    "Where do you see yourself in five years?",
    "What are the most important challenges you have faced in your work?",
    "How do you work in a team? Can you give me a specific example?",
    "Do you have any questions for me?",
]


# =========================================================================
# LLM CALL ABSTRACTION
# =========================================================================

def _call_llm(
    system_prompt: str,
    conversation: list[dict[str, str]],
) -> str:
    """Call the configured LLM provider.

    Dispatches to Gemini (active) or OpenAI (commented out).
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "claude":
        return _call_claude(system_prompt, conversation)
    elif provider == "gemini":
        return _call_gemini(system_prompt, conversation)
    # elif provider == "openai":                  # <-- uncomment for OpenAI
    #     return _call_openai(system_prompt, conversation)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# =========================================================================
# CLAUDE / ANTHROPIC PROVIDER (active)
# =========================================================================
def _call_claude(
    system_prompt: str,
    conversation: list[dict[str, str]],
) -> str:
    """Call Claude Sonnet 4 with the given system prompt and conversation."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    messages = []
    for msg in conversation:
        messages.append({"role": msg["role"], "content": msg["content"]})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )

    return response.content[0].text.strip()


# =========================================================================
# GEMINI PROVIDER
# =========================================================================
def _call_gemini(
    system_prompt: str,
    conversation: list[dict[str, str]],
) -> str:
    """Call Gemini with the given system prompt and conversation.

    Tries gemini-2.5-flash first, falls back to gemini-2.0-flash if 503.
    """
    import time
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    contents = []
    for msg in conversation:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    config = types.GenerateContentConfig(system_instruction=system_prompt)
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    last_error = None

    for model_name in models:
        for attempt in range(2):
            try:
                logger.info("Trying %s (attempt %d)", model_name, attempt + 1)
                response = client.models.generate_content(
                    model=model_name,
                    config=config,
                    contents=contents,
                )
                return response.text.strip()
            except (genai_errors.ServerError, genai_errors.APIError) as e:
                last_error = e
                logger.warning("%s attempt %d failed: %s", model_name, attempt + 1, e)
                if attempt == 0:
                    time.sleep(2)

    raise RuntimeError(f"All Gemini models unavailable: {last_error}")


# =========================================================================
# OPENAI PROVIDER (commented out — uncomment when you have OpenAI credits)
# =========================================================================
# def _call_openai(
#     system_prompt: str,
#     conversation: list[dict[str, str]],
#     effort: str = "low",
# ) -> str:
#     """Call GPT-5.4 with the given system prompt and conversation history."""
#     from openai import OpenAI
#
#     client = OpenAI(api_key=settings.OPENAI_API_KEY)
#
#     messages = [{"role": "user", "content": system_prompt}]
#     for msg in conversation:
#         messages.append({"role": msg["role"], "content": msg["content"]})
#
#     response = client.responses.create(
#         model="gpt-5.4",
#         reasoning={"effort": effort},
#         input=messages,
#     )
#     return response.output_text.strip()


# =========================================================================
# EVALUATION (uses LLM internally)
# =========================================================================
def _evaluate_response_llm(
    phase: int,
    depth_level: int,
    question: str,
    response: str,
    ground_truth: str | None = None,
) -> dict[str, Any]:
    """Use the configured LLM to evaluate a candidate's response."""
    ground_truth_section = ""
    if ground_truth:
        ground_truth_section = f"Ground truth answer: {ground_truth}"

    eval_prompt = EVALUATE_RESPONSE.format(
        phase=phase,
        depth_level=depth_level,
        question=question,
        response=response,
        ground_truth_section=ground_truth_section,
    )

    raw = _call_llm(SYSTEM_PROMPT, [{"role": "user", "content": eval_prompt}])

    # Strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Eval response not valid JSON: %s", raw[:300])
        return {
            "understanding_score": 5.0,
            "completeness_score": 5.0,
            "accuracy_score": 5.0,
            "communication_score": 5.0,
            "should_go_deeper": False,
            "should_give_hint": False,
            "anxiety_detected": False,
            "key_observations": "Evaluation parsing failed.",
            "missing_concepts": [],
        }


# =========================================================================
# INTERVIEW STATE
# =========================================================================
class InterviewState:
    """Holds the mutable state for a single interview session."""

    def __init__(
        self,
        session_id: str,
        candidate_data: dict[str, Any],
    ):
        self.session_id = session_id
        self.candidate = candidate_data
        self.current_phase = 1
        self.conversation: list[dict[str, str]] = []
        self.phase_conversations: dict[int, list[dict[str, str]]] = {
            1: [], 2: [], 3: [], 4: [], 5: [],
        }

        # Phase 2/3 depth tracking
        self.current_depth = 1
        self.questions_at_depth = 0
        self.max_depth_reached = {2: 0, 3: 0}

        # Hint tracking
        self.hints_given = {2: 0, 3: 0}
        self.hints_recovered = {2: 0, 3: 0}
        self.last_was_hint = False

        # Phase 4 factual tracking
        self.factual_questions: list[dict[str, Any]] = []
        self.factual_index = 0
        self.factual_correct = 0
        self.factual_evaluations: list[dict[str, Any]] = []

        # Phase 5 behavioral tracking
        self.behavioral_index = 0
        self.behavioral_scores: list[dict[str, float]] = []

        # Question counters per phase
        self.question_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Evaluation results per response
        self.response_evaluations: list[dict[str, Any]] = []

        # Anxiety tracking
        self.anxiety_break_active = False

    @property
    def phase_name(self) -> str:
        return PHASE_CONFIG[self.current_phase]["name"]

    @property
    def max_questions(self) -> int:
        return PHASE_CONFIG[self.current_phase]["max_questions"]

    def is_phase_complete(self) -> bool:
        return self.question_count[self.current_phase] >= self.max_questions


# ──────────────────────────────────────────────────────────────────────
# In-memory session store (maps session_id -> InterviewState)
# In production, this would be backed by Redis or similar.
# ──────────────────────────────────────────────────────────────────────
_sessions: dict[str, InterviewState] = {}


def create_session(candidate_data: dict[str, Any]) -> InterviewState:
    """Create a new interview session and return its state."""
    session_id = str(uuid4())
    state = InterviewState(session_id, candidate_data)
    _sessions[session_id] = state
    return state


def get_session(session_id: str) -> InterviewState | None:
    return _sessions.get(session_id)


def generate_first_message(state: InterviewState) -> str:
    """Generate the interviewer's opening message for Phase 1."""
    resume_sections = state.candidate.get("resume_sections", {})
    name = state.candidate.get("name", "the candidate")

    prompt = PHASE1_BACKGROUND.format(
        resume_sections=json.dumps(resume_sections, indent=2),
        max_questions=PHASE_CONFIG[1]["max_questions"],
        question_number=1,
    )

    conversation = [
        {
            "role": "user",
            "content": (
                f"Begin the interview. The candidate's name is {name}. "
                "Start with a brief greeting and your first question."
            ),
        }
    ]

    response = _call_llm(SYSTEM_PROMPT + "\n\n" + prompt, conversation)
    state.question_count[1] = 1
    state.phase_conversations[1].append({"role": "assistant", "content": response})
    state.conversation.append({"role": "assistant", "content": response})

    return response


def process_candidate_response(
    state: InterviewState,
    candidate_text: str,
    anxiety_detected_voice: bool = False,
) -> dict[str, Any]:
    """Process a candidate's response and return the next interviewer message.

    Returns a dict with:
        - message: the interviewer's next message
        - phase: current phase number
        - phase_name: current phase name
        - depth_level: current depth (phases 2/3)
        - is_hint: whether the message is a hint
        - anxiety_break: whether we're pausing for anxiety
        - interview_complete: whether the interview is finished
        - evaluation: the eval scores for this response
    """
    phase = state.current_phase

    # Record candidate message
    state.conversation.append({"role": "user", "content": candidate_text})
    state.phase_conversations[phase].append({"role": "user", "content": candidate_text})

    # ── Anxiety check ──
    if state.anxiety_break_active:
        state.anxiety_break_active = False
        # Resume from where we left off — re-ask the last question
        return _continue_phase(state)

    # ── Evaluate the candidate's response ──
    last_question = ""
    for msg in reversed(state.phase_conversations[phase]):
        if msg["role"] == "assistant":
            last_question = msg["content"]
            break

    ground_truth = None
    if phase == 4 and state.factual_index > 0:
        idx = state.factual_index - 1
        if idx < len(state.factual_questions):
            ground_truth = state.factual_questions[idx].get("answer")

    evaluation = _evaluate_response_llm(
        phase=phase,
        depth_level=state.current_depth if phase in (2, 3) else 0,
        question=last_question,
        response=candidate_text,
        ground_truth=ground_truth,
    )
    state.response_evaluations.append(evaluation)

    # Check for anxiety (from voice analysis or LLM detection)
    if anxiety_detected_voice or evaluation.get("anxiety_detected", False):
        state.anxiety_break_active = True
        pause_msg = (
            "Let's take a moment. Take a deep breath — there's no rush. "
            "We can continue whenever you're ready."
        )
        state.conversation.append({"role": "assistant", "content": pause_msg})
        state.phase_conversations[phase].append(
            {"role": "assistant", "content": pause_msg}
        )
        return {
            "message": pause_msg,
            "phase": phase,
            "phase_name": state.phase_name,
            "depth_level": state.current_depth if phase in (2, 3) else None,
            "is_hint": False,
            "anxiety_break": True,
            "interview_complete": False,
            "evaluation": evaluation,
        }

    # ── Hint recovery tracking ──
    if state.last_was_hint and phase in (2, 3):
        if evaluation.get("understanding_score", 0) >= 5:
            state.hints_recovered[phase] += 1
        state.last_was_hint = False

    # ── Phase 4 factual scoring ──
    if phase == 4 and ground_truth:
        if evaluation.get("accuracy_score", 0) >= 6:
            state.factual_correct += 1
        state.factual_evaluations.append(evaluation)

    # ── Check if we should give a hint (phases 2/3) ──
    if phase in (2, 3) and evaluation.get("should_give_hint", False):
        return _generate_hint(state, last_question, candidate_text, evaluation)

    # ── Check if we should go deeper (phases 2/3) ──
    if phase in (2, 3) and evaluation.get("should_go_deeper", False):
        state.current_depth = min(state.current_depth + 1, 5)
        state.questions_at_depth = 0
        state.max_depth_reached[phase] = max(
            state.max_depth_reached[phase], state.current_depth
        )

    # ── Check phase completion and transition ──
    if state.is_phase_complete():
        return _advance_phase(state)

    # ── Generate next question ──
    return _continue_phase(state)


def _generate_hint(
    state: InterviewState,
    question: str,
    response: str,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """Generate a hint for the candidate."""
    phase = state.current_phase

    hint_prompt = HINT_TEMPLATE.format(
        phase=phase,
        current_question=question,
        last_response=response,
        depth_level=state.current_depth,
    )

    hint = _call_llm(SYSTEM_PROMPT, [{"role": "user", "content": hint_prompt}])

    state.hints_given[phase] = state.hints_given.get(phase, 0) + 1
    state.last_was_hint = True

    state.conversation.append({"role": "assistant", "content": hint})
    state.phase_conversations[phase].append({"role": "assistant", "content": hint})

    return {
        "message": hint,
        "phase": phase,
        "phase_name": state.phase_name,
        "depth_level": state.current_depth,
        "is_hint": True,
        "anxiety_break": False,
        "interview_complete": False,
        "evaluation": evaluation,
    }


def _continue_phase(state: InterviewState) -> dict[str, Any]:
    """Generate the next question within the current phase."""
    phase = state.current_phase
    state.question_count[phase] += 1

    if phase == 1:
        return _phase1_next(state)
    elif phase == 2:
        return _phase2_next(state)
    elif phase == 3:
        return _phase3_next(state)
    elif phase == 4:
        return _phase4_next(state)
    elif phase == 5:
        return _phase5_next(state)

    return _advance_phase(state)


def _phase1_next(state: InterviewState) -> dict[str, Any]:
    """Generate next Phase 1 question."""
    resume_sections = state.candidate.get("resume_sections", {})
    prompt = PHASE1_BACKGROUND.format(
        resume_sections=json.dumps(resume_sections, indent=2),
        max_questions=PHASE_CONFIG[1]["max_questions"],
        question_number=state.question_count[1],
    )

    response = _call_llm(
        SYSTEM_PROMPT + "\n\n" + prompt,
        state.phase_conversations[1],
    )

    state.conversation.append({"role": "assistant", "content": response})
    state.phase_conversations[1].append({"role": "assistant", "content": response})

    return _make_response(state, response)


def _phase2_next(state: InterviewState) -> dict[str, Any]:
    """Generate next Phase 2 question (primary project deep-dive)."""
    project = state.candidate.get("primary_project", {})
    state.questions_at_depth += 1

    prompt = PHASE2_PROJECT_DEEP_DIVE.format(
        project_title=project.get("title", "Unknown"),
        project_description=project.get("description", ""),
        project_technologies=", ".join(project.get("technologies", [])),
        current_depth=state.current_depth,
        questions_at_depth=state.questions_at_depth,
        max_questions=PHASE_CONFIG[2]["max_questions"],
        question_number=state.question_count[2],
    )

    response = _call_llm(
        SYSTEM_PROMPT + "\n\n" + prompt,
        state.phase_conversations[2],
    )

    state.conversation.append({"role": "assistant", "content": response})
    state.phase_conversations[2].append({"role": "assistant", "content": response})

    return _make_response(state, response)


def _phase3_next(state: InterviewState) -> dict[str, Any]:
    """Generate next Phase 3 question (secondary project deep-dive)."""
    project = state.candidate.get("secondary_project", {})

    # Reset depth tracking for phase 3
    if state.question_count[3] == 1:
        state.current_depth = 1
        state.questions_at_depth = 0

    state.questions_at_depth += 1

    prompt = PHASE3_PROJECT_DEEP_DIVE_2.format(
        project_title=project.get("title", "Unknown"),
        project_description=project.get("description", ""),
        project_technologies=", ".join(project.get("technologies", [])),
        current_depth=state.current_depth,
        questions_at_depth=state.questions_at_depth,
        max_questions=PHASE_CONFIG[3]["max_questions"],
        question_number=state.question_count[3],
    )

    response = _call_llm(
        SYSTEM_PROMPT + "\n\n" + prompt,
        state.phase_conversations[3],
    )

    state.conversation.append({"role": "assistant", "content": response})
    state.phase_conversations[3].append({"role": "assistant", "content": response})

    return _make_response(state, response)


def _phase4_next(state: InterviewState) -> dict[str, Any]:
    """Generate next Phase 4 question (factual ML knowledge)."""
    # Load questions on first call
    if not state.factual_questions:
        field = state.candidate.get("identified_field", "Machine Learning")
        state.factual_questions = retrieve_questions_by_field(
            field, num_questions=PHASE_CONFIG[4]["max_questions"]
        )

    if state.factual_index >= len(state.factual_questions):
        return _advance_phase(state)

    q = state.factual_questions[state.factual_index]
    state.factual_index += 1

    prompt = PHASE4_FACTUAL.format(
        question=q["question"],
        ground_truth_answer=q["answer"],
        category=q.get("category", "General ML"),
        question_number=state.factual_index,
        max_questions=len(state.factual_questions),
    )

    response = _call_llm(
        SYSTEM_PROMPT + "\n\n" + prompt,
        state.phase_conversations[4],
    )

    state.conversation.append({"role": "assistant", "content": response})
    state.phase_conversations[4].append({"role": "assistant", "content": response})

    return _make_response(state, response)


def _phase5_next(state: InterviewState) -> dict[str, Any]:
    """Generate next Phase 5 question (behavioral)."""
    if state.behavioral_index >= len(BEHAVIORAL_QUESTIONS):
        return _advance_phase(state)

    question = BEHAVIORAL_QUESTIONS[state.behavioral_index]
    state.behavioral_index += 1

    prompt = PHASE5_BEHAVIORAL.format(
        question=question,
        question_number=state.behavioral_index,
        max_questions=len(BEHAVIORAL_QUESTIONS),
    )

    response = _call_llm(
        SYSTEM_PROMPT + "\n\n" + prompt,
        state.phase_conversations[5],
    )

    state.conversation.append({"role": "assistant", "content": response})
    state.phase_conversations[5].append({"role": "assistant", "content": response})

    return _make_response(state, response)


def _advance_phase(state: InterviewState) -> dict[str, Any]:
    """Move to the next phase or end the interview."""
    if state.current_phase >= 5:
        closing = (
            "That concludes our interview. Thank you for your time. "
            "We will compile your evaluation report shortly."
        )
        state.conversation.append({"role": "assistant", "content": closing})
        return {
            "message": closing,
            "phase": state.current_phase,
            "phase_name": state.phase_name,
            "depth_level": None,
            "is_hint": False,
            "anxiety_break": False,
            "interview_complete": True,
            "evaluation": None,
        }

    state.current_phase += 1
    state.question_count[state.current_phase] = 0

    # Reset depth for project phases
    if state.current_phase in (2, 3):
        state.current_depth = 1
        state.questions_at_depth = 0

    return _continue_phase(state)


def _make_response(
    state: InterviewState, message: str
) -> dict[str, Any]:
    """Build the standard response dict."""
    return {
        "message": message,
        "phase": state.current_phase,
        "phase_name": state.phase_name,
        "depth_level": state.current_depth if state.current_phase in (2, 3) else None,
        "is_hint": False,
        "anxiety_break": False,
        "interview_complete": False,
        "evaluation": (
            state.response_evaluations[-1]
            if state.response_evaluations
            else None
        ),
    }
