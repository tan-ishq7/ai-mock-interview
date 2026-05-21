# Ideas v2 — Second Session

## Setup / Fresher Onboarding
- Fresher asked: what to install on laptop? → Python, VS Code, Node.js is the full answer
- Need to make this clear in SETUP.md (added)

## RAG Status — Is It Actually Working?
- Issue 5 (Pydantic missing embedding field) does NOT break retrieval — Pydantic model not used for queries
- Real problem: the 18 SQL-seeded questions have NULL embeddings → vector search returns 0 results → falls back to text (ILIKE category match)
- To enable real vector RAG: must run `python -m backend.knowledge.question_indexer` after setup
- The indexer reads from ml_questions.md (markdown file), generates embeddings, inserts into Supabase
- The SQL schema seeds 18 questions WITHOUT embeddings (SQL can't run sentence-transformers)
- Fix needed: add indexer step to SETUP.md

## Question Bank Design Questions
- Only 5 of the 18 questions are asked per interview (PHASE_CONFIG phase 4 max_questions = 5)
- Selection is by relevance to candidate's identified_field (vector search or text fallback)
- LLM has nuance in Phase 4: partial answers get a follow-up, wrong answers just move on (no reveal)
- 18 questions is sparse — especially for niche fields like "Agentic AI" (only 3 questions in that category)
- Idea: expand the ml_questions.md file with more questions per category
- Idea: add more categories aligned with common resume fields

## Potential Future Work
- Run question_indexer after Supabase setup to enable real vector RAG
- Expand ml_questions.md
- Write conversation_messages to DB (currently lost)
- Write interview_sessions to DB (currently not written)
