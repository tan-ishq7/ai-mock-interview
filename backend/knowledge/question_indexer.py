"""
Parse the ML questions markdown file, generate embeddings, and store in Supabase.

Run this module directly to seed the question bank:
    python -m backend.knowledge.question_indexer
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

from backend.database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

ML_QUESTIONS_PATH = Path(__file__).parent / "ml_questions.md"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def _parse_markdown(md_path: Path) -> list[dict[str, str]]:
    """Extract question/answer/category triples from the markdown file."""
    text = md_path.read_text(encoding="utf-8")
    questions: list[dict[str, str]] = []

    current_category = ""
    blocks = re.split(r"(?=^### Q\d+:)", text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block.startswith("### Q"):
            # Check if this block sets a category header
            cat_match = re.search(r"^## (.+)$", block, re.MULTILINE)
            if cat_match:
                current_category = cat_match.group(1).strip()
            continue

        # Extract question
        q_match = re.match(r"### Q\d+:\s*(.+)", block)
        if not q_match:
            continue
        question = q_match.group(1).strip()

        # Extract answer
        a_match = re.search(
            r"\*\*Answer:\*\*\s*(.+?)(?=\n\*\*Category|\Z)",
            block,
            re.DOTALL,
        )
        answer = a_match.group(1).strip() if a_match else ""

        # Extract category from the block itself
        c_match = re.search(r"\*\*Category:\*\*\s*(.+)", block)
        category = c_match.group(1).strip() if c_match else current_category

        if question and answer:
            questions.append(
                {"question": question, "answer": answer, "category": category}
            )

    return questions


def _generate_embeddings(
    questions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Add 384-dim embeddings to each question dict."""
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    texts = [q["question"] for q in questions]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    enriched = []
    for q, emb in zip(questions, embeddings):
        enriched.append(
            {
                **q,
                "embedding": emb.tolist(),
                "source": "github",
            }
        )
    return enriched


def seed_question_bank() -> int:
    """Parse, embed, and upsert all ML questions into Supabase.

    Returns the number of questions inserted.
    """
    questions = _parse_markdown(ML_QUESTIONS_PATH)
    logger.info("Parsed %d questions from %s", len(questions), ML_QUESTIONS_PATH)

    enriched = _generate_embeddings(questions)
    logger.info("Generated embeddings for %d questions", len(enriched))

    supabase = get_supabase()

    # Clear existing github-sourced questions to avoid duplicates
    supabase.table("ml_questions").delete().eq("source", "github").execute()

    # Insert in batches of 10
    for i in range(0, len(enriched), 10):
        batch = enriched[i : i + 10]
        supabase.table("ml_questions").insert(batch).execute()

    logger.info("Seeded %d questions into Supabase", len(enriched))
    return len(enriched)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = seed_question_bank()
    print(f"Done — seeded {count} questions.")
