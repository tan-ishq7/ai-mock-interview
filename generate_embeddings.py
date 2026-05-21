"""
Run this once after setting up Supabase to generate embeddings for all ML questions.

    python generate_embeddings.py

What it does:
  1. Reads all questions from Supabase that have no embedding yet
  2. Generates 384-dim embeddings using all-MiniLM-L6-v2 (already on your machine)
  3. Updates each row in Supabase with its embedding
  4. Vector search (RAG) in Phase 4 then works properly
"""

import sys
from sentence_transformers import SentenceTransformer
from backend.database.supabase_client import get_supabase

def main():
    print("Connecting to Supabase...")
    supabase = get_supabase()

    print("Fetching questions without embeddings...")
    result = supabase.table("ml_questions").select("id, question").execute()
    questions = result.data

    if not questions:
        print("No questions found. Did you run supabase_schema.sql first?")
        sys.exit(1)

    print(f"Found {len(questions)} questions. Generating embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [q["question"] for q in questions]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    print("Uploading embeddings to Supabase...")
    for q, emb in zip(questions, embeddings):
        supabase.table("ml_questions").update(
            {"embedding": emb.tolist()}
        ).eq("id", q["id"]).execute()

    print(f"\nDone. {len(questions)} questions now have embeddings.")
    print("Phase 4 RAG vector search is active.")

if __name__ == "__main__":
    main()
