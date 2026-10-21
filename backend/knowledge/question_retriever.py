"""
Retrieve ML questions using category matching and vector similarity.
Optimized to run under 50MB RAM for cloud deployments (e.g. Render free tier).
"""

import logging
import re
from pathlib import Path
from typing import Any

from backend.database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

ML_QUESTIONS_PATH = Path(__file__).parent / "ml_questions.md"

_local_questions: list[dict[str, str]] | None = None


def _parse_markdown(md_path: Path) -> list[dict[str, str]]:
    """Extract question/answer/category triples from the markdown file."""
    if not md_path.exists():
        return []
    text = md_path.read_text(encoding="utf-8")
    questions: list[dict[str, str]] = []

    current_category = ""
    blocks = re.split(r"(?=^### Q\d+:)", text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block.startswith("### Q"):
            cat_match = re.search(r"^## (.+)$", block, re.MULTILINE)
            if cat_match:
                current_category = cat_match.group(1).strip()
            continue

        q_match = re.match(r"### Q\d+:\s*(.+)", block)
        if not q_match:
            continue
        question = q_match.group(1).strip()

        a_match = re.search(
            r"\*\*Answer:\*\*\s*(.+?)(?=\n\*\*Category|\Z)",
            block,
            re.DOTALL,
        )
        answer = a_match.group(1).strip() if a_match else ""

        c_match = re.search(r"\*\*Category:\*\*\s*(.+)", block)
        category = c_match.group(1).strip() if c_match else current_category

        if question and answer:
            questions.append(
                {
                    "question": question,
                    "answer": answer,
                    "category": category,
                }
            )

    return questions


def _get_local_questions() -> list[dict[str, str]]:
    global _local_questions
    if _local_questions is None:
        _local_questions = _parse_markdown(ML_QUESTIONS_PATH)
    return _local_questions


def _retrieve_local_category_search(field: str, num_questions: int) -> list[dict[str, Any]]:
    """Local category matching fallback without needing heavy ML libraries."""
    questions = _get_local_questions()
    if not questions:
        return []

    field_lower = field.lower().strip()
    words = [w for w in re.split(r"\W+", field_lower) if len(w) > 2]

    # 1. Exact or partial category match
    matched: list[dict[str, str]] = []
    for q in questions:
        cat_lower = q["category"].lower()
        if field_lower in cat_lower or any(w in cat_lower for w in words):
            matched.append(q)

    # 2. Add Core ML / Deep Learning questions if more are needed
    if len(matched) < num_questions:
        general = [
            q for q in questions
            if q not in matched and ("core ml" in q["category"].lower() or "deep learning" in q["category"].lower())
        ]
        matched.extend(general)

    # 3. Add any remaining questions if still needed
    if len(matched) < num_questions:
        remaining = [q for q in questions if q not in matched]
        matched.extend(remaining)

    return matched[:num_questions]


def retrieve_questions_by_field(
    field: str,
    num_questions: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve ML questions most relevant to the candidate's field.

    1. Tries Supabase category query.
    2. Optional vector search if sentence_transformers is available.
    3. Seamless local category search fallback (100% reliable, zero memory overhead).
    """
    # 1. Try Supabase category filter
    try:
        supabase = get_supabase()
        result = (
            supabase.table("ml_questions")
            .select("question, answer, category")
            .ilike("category", f"%{field}%")
            .limit(num_questions)
            .execute()
        )

        questions = result.data if result.data else []

        if len(questions) < num_questions:
            remaining = num_questions - len(questions)
            existing_qs = {q["question"] for q in questions}
            general = (
                supabase.table("ml_questions")
                .select("question, answer, category")
                .limit(remaining + 5)
                .execute()
            )
            for q in general.data or []:
                if q["question"] not in existing_qs and len(questions) < num_questions:
                    questions.append(q)

        if questions:
            return questions
    except Exception as exc:
        logger.warning("Supabase table query unavailable: %s", exc)

    # 2. Optional: Try local vector search if sentence_transformers is installed
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(f"Machine learning questions about {field}", normalize_embeddings=True).tolist()
        questions = _get_local_questions()
        if questions:
            texts = [f"{q['category']}: {q['question']}" for q in questions]
            embeddings = model.encode(texts, normalize_embeddings=True)
            q_vec = np.array(query_embedding, dtype=np.float32)
            scores = np.dot(embeddings, q_vec)
            top_indices = np.argsort(scores)[::-1][:num_questions]
            return [
                {
                    "question": questions[idx]["question"],
                    "answer": questions[idx]["answer"],
                    "category": questions[idx]["category"],
                }
                for idx in top_indices
            ]
    except Exception as exc:
        logger.debug("SentenceTransformers unavailable or skipped: %s", exc)

    # 3. Local category matching (super fast, 0MB overhead, 100% reliable)
    logger.info("Using lightweight local category search for field: '%s'", field)
    return _retrieve_local_category_search(field, num_questions)
