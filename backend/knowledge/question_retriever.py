"""
Retrieve ML questions from Supabase using vector similarity search.

Matches questions relevant to the candidate's identified field (NLP, CV, etc.)
using cosine similarity on 384-dim embeddings.
"""

import logging
from typing import Any

from sentence_transformers import SentenceTransformer

from backend.database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Lazy-loaded singleton
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def retrieve_questions_by_field(
    field: str,
    num_questions: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve ML questions most relevant to the candidate's field.

    Uses the field name (e.g. "NLP", "Computer Vision") to generate a query
    embedding and finds the closest questions via cosine similarity.

    Parameters
    ----------
    field:
        The candidate's primary ML field.
    num_questions:
        Number of questions to retrieve.

    Returns
    -------
    list of dicts with keys: question, answer, category.
    """
    model = _get_model()
    query = f"Machine learning questions about {field}"
    query_embedding = model.encode(query, normalize_embeddings=True).tolist()

    supabase = get_supabase()

    # Use Supabase RPC for vector similarity search
    # This requires a Postgres function — fall back to category filter if unavailable
    try:
        result = supabase.rpc(
            "match_ml_questions",
            {
                "query_embedding": query_embedding,
                "match_count": num_questions,
            },
        ).execute()

        if result.data:
            return [
                {
                    "question": r["question"],
                    "answer": r["answer"],
                    "category": r["category"],
                }
                for r in result.data
            ]
    except Exception:
        logger.warning("RPC match_ml_questions not available, using category fallback")

    # Fallback: filter by category text match
    result = (
        supabase.table("ml_questions")
        .select("question, answer, category")
        .ilike("category", f"%{field}%")
        .limit(num_questions)
        .execute()
    )

    questions = result.data if result.data else []

    # If not enough questions from category match, get general ones
    if len(questions) < num_questions:
        remaining = num_questions - len(questions)
        existing_ids = {q["question"] for q in questions}
        general = (
            supabase.table("ml_questions")
            .select("question, answer, category")
            .limit(remaining + 5)
            .execute()
        )
        for q in general.data or []:
            if q["question"] not in existing_ids and len(questions) < num_questions:
                questions.append(q)

    return questions
