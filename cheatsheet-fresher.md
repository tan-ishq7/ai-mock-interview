# Fresher Cheatsheet — AI Mock Interview Project
> For someone presenting this project in an interview. Covers: what each API does, cost, models, AI/ML concepts to know, and expected questions.

---

## 1. What Each API Key Does and Why

### ANTHROPIC_API_KEY (Claude) — Active Primary LLM
**Used for:**
- Resume parsing: sends PDF bytes directly to Claude's `document` content block, gets structured JSON back
- Interview question generation: generates all 5 phases of questions based on resume + prompt templates
- Response evaluation: after every candidate answer, makes a separate LLM call to score it (returns JSON)
- Report generation: writes the final evaluation report narrative

**Model:** `claude-sonnet-4-20250514`
**Why Claude:** Handles PDF natively (no need to extract text first), excellent at structured JSON output, strong instruction-following for the neutral interviewer persona

**SDK used:**
```python
import anthropic
client = anthropic.Anthropic(api_key=...)
response = client.messages.create(model=..., max_tokens=..., system=..., messages=[...])
```

---

### GEMINI_API_KEY (Google Gemini) — Alternative LLM Provider
**Used for:** Same tasks as Claude (resume parsing, question generation, evaluation, report)
**Models:** `gemini-2.5-flash` (primary), fallback to `gemini-2.0-flash` if 503
**Why Gemini:** Free tier is generous, supports native PDF via `inline_data` base64, fast inference
**Switch via:** Set `LLM_PROVIDER=gemini` in `.env`

---

### OPENAI_API_KEY — Commented Out (Not Active)
**Would be used for:** Same pipeline, `gpt-5.4` via Responses API
**Status:** Inactive — no credits available at time of build

---

### ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID — Text-to-Speech
**Used for:** Converting the interviewer's generated text questions into audio
**Why:** Makes the interview feel like a real voice interview, not just a chatbot
**Multi-modal significance:** This is where "text + audio" comes in — the same LLM output is delivered both as text (for reading) and audio (for listening)
**Voice ID:** Picks a specific ElevenLabs voice character for the interviewer

---

### SUPABASE_URL + SUPABASE_ANON_KEY + SUPABASE_SERVICE_ROLE_KEY — Database
**Used for:**
- Storing parsed candidate profiles (candidates table)
- Storing evaluation scores per phase (evaluations table)
- Storing final interview reports (reports table)
- Storing ML knowledge questions with vector embeddings (ml_questions table with pgvector)
- Vector similarity search for Phase 4 questions

**Why Supabase (not plain Postgres):** Built-in pgvector support for embeddings, REST API out of the box via PostgREST, free tier, easy auth management

**Service role key vs anon key:** Service role key bypasses Row Level Security — used server-side only (never expose to frontend). Anon key is safe for client-side.

**Free tier note:** Projects pause after 7 days of inactivity. To restore: dashboard → your project → "Restore project". Takes ~1-2 minutes. No data loss, no table recreation needed.

---

## 2. Model & Library Inventory

| Component | Model/Library | Purpose |
|-----------|--------------|---------|
| Resume parsing | `claude-sonnet-4-20250514` or `gemini-2.5-flash` | PDF → structured JSON |
| Interview engine | Same LLM | Question generation per phase |
| Response evaluation | Same LLM | Per-answer scoring (JSON output) |
| Report generation | Same LLM | Final narrative report |
| Factual Q retrieval | `all-MiniLM-L6-v2` (SentenceTransformers) | Encode candidate field → vector search |
| Text-to-speech | ElevenLabs API | LLM text → audio |
| Speech-to-text | Whisper (OpenAI open-source) | Audio → transcribed text |
| Anxiety detection | Rule-based + LLM | WPM, filler words, hedging language |
| Database | Supabase (Postgres + pgvector) | Persistence + vector search |
| Backend framework | FastAPI | REST API |

---

## 3. Cost Estimation Per Interview

### Claude Sonnet 4 Pricing (as of mid-2025)
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

### Per Interview Breakdown
| Task | Calls | Avg Input Tokens | Avg Output Tokens |
|------|-------|-----------------|-------------------|
| Resume parsing | 1 | ~2,000 (PDF) | ~500 |
| Phase 1 Q gen (3) | 3 | ~800 each | ~200 each |
| Phase 1 evaluation (3) | 3 | ~500 each | ~150 each |
| Phase 2+3 Q gen (16) | 16 | ~900 each | ~200 each |
| Phase 2+3 evaluation (16) | 16 | ~600 each | ~150 each |
| Phase 4 Q gen (5) | 5 | ~700 each | ~150 each |
| Phase 4 evaluation (5) | 5 | ~500 each | ~150 each |
| Phase 5 Q gen (4) | 4 | ~600 each | ~200 each |
| Phase 5 evaluation (4) | 4 | ~500 each | ~150 each |
| Report generation | 1 | ~800 | ~1,500 |

**Totals (approximate):**
- Total LLM calls: ~58 per complete interview
- Total input tokens: ~35,000
- Total output tokens: ~9,000
- Claude cost: (35k × $3/M) + (9k × $15/M) ≈ $0.105 + $0.135 = **~$0.24 per interview**
- ElevenLabs: ~2,000 chars of TTS ≈ **~$0.03** (Creator plan = $0.18/1k chars)
- **Total per interview: ~$0.25-0.30**

At 100 interviews/month: ~$25-30/month on AI APIs alone.

---

## 4. AI/ML Concepts to Know (Interview-Ready)

### RAG — Retrieval Augmented Generation
**What it is:** Fetch relevant context from a database at inference time, inject into LLM prompt. Solves: knowledge cutoff, hallucination on specific facts.
**In this project:** Phase 4 uses RAG. `all-MiniLM-L6-v2` embeds the candidate's field → cosine similarity search against `ml_questions` table (pgvector) → top-k questions retrieved and asked.
**Talk point:** "We use a lightweight RAG pipeline for the factual phase — no fine-tuning needed, just a vector store of ML questions with ground-truth answers."

### MCP — Model Context Protocol (Anthropic)
**What it is:** An open protocol that standardizes how LLMs connect to external tools, data sources, and APIs. Like a "USB-C for AI" — instead of every tool having its own integration, MCP provides a standard interface.
**In this project:** NOT yet integrated — big opportunity.
**Where you'd add it:** Expose the interview engine as an MCP server. Then any Claude-powered agent could run interviews as a tool call. Or use MCP to connect to a calendar tool to schedule real interviews.
**How to frame it in interview:** "MCP would let us decouple the interview orchestration from the frontend — any MCP client could trigger an interview session, and we'd get tool-use natively instead of building custom integrations."

### Orchestration / Agent Loops
**What it is:** Coordinating multiple LLM calls, tools, and state machines to accomplish a multi-step task.
**In this project:** The `InterviewState` class + `process_candidate_response()` function IS the orchestration layer. It manages 5 phases, depth tracking, hint generation, anxiety detection, and phase transitions — all driven by LLM outputs.
**Key pattern:** After every candidate response, the engine evaluates it → decides which tool to call next (go deeper, give hint, advance phase, pause for anxiety) → calls the LLM → returns a structured response dict. This is a classic agentic loop.

### Multi-Modal Systems
**What it is:** Systems that process/generate multiple types of data (text, audio, image, video).
**In this project:**
- Input modalities: PDF (resume), audio (candidate speech via Whisper STT)
- Output modalities: text (question, evaluation), audio (interviewer voice via ElevenLabs TTS)
- The LLM itself is text-in/text-out, but the system wraps it with audio I/O
**Why it matters:** Interviewers in 2025 are heavily focused on multi-modal — voice + text is a realistic first step. Future extension: video analysis (eye contact, body language detection).

### Prompt Engineering Patterns Used in This Project
1. **System prompt persona:** Fixed interviewer persona injected into every call (`SYSTEM_PROMPT`). Controls tone, prohibits enthusiasm, enforces neutral assessment.
2. **Structured output prompting:** Asking the LLM to return JSON only, with explicit schema. Used for evaluation calls.
3. **Dynamic context injection:** Phase-specific prompts include runtime data (resume sections, project details, current depth level, question number). This is how the same prompt template produces contextually relevant questions.
4. **Chain of evaluation → action:** Each response triggers an evaluation LLM call whose output directly drives the next action (hint vs. deeper vs. advance). This is a simple form of tool-use routing.

### Embeddings and Vector Search
**What it is:** Converting text to a numeric vector representation. Similar texts → close vectors. Used for semantic search, retrieval, clustering.
**In this project:** `all-MiniLM-L6-v2` (384-dimensional) embeds the candidate's field. Supabase pgvector extension stores pre-computed question embeddings. At query time: encode field → cosine similarity against all stored embeddings → return top-k questions.
**Key concepts:** Cosine similarity, embedding dimensions, normalization, HNSW index (for approximate nearest neighbor search at scale).

### Anxiety Detection — Multi-Signal Classification
**Rule-based signals:**
- Speech rate: <60 WPM or >180 WPM flags as anxious
- Filler words: >12% of total words (um, uh, like, basically, you know, sort of...)
- Stuttering: regex detects word repetitions ("the the", "I I")
- Short response: <5 words in >2 second audio clip

**LLM-based signal:**
- Evaluation prompt includes `anxiety_detected` field: fires for hedging language ("I think maybe", "I'm not sure"), very short answers, explicit "I don't know"

Either signal independently triggers a pause message.

---

## 5. Questions a Fresher Presenting This Project Will Face

### Architecture Questions
- "Why did you use an in-memory session store? What are the risks?"
  → Sessions lost on server restart. In production: Redis with TTL.
- "Why FastAPI over Flask/Django?"
  → Native async support, auto-generated OpenAPI docs, Pydantic validation out of the box.
- "How would you scale this to 1000 concurrent users?"
  → Stateless LLM calls scale horizontally. Session state needs Redis. LLM calls need rate-limit handling and queuing (Celery/BullMQ). ElevenLabs TTS would be the bottleneck — cache common phrases.

### LLM / AI Questions
- "Why not fine-tune a model instead of prompting?"
  → Fine-tuning is expensive, requires labeled interview data, and doesn't generalize to new resume types easily. Prompting with a capable base model is faster to iterate and works well here.
- "How does the depth system decide when to go deeper?"
  → The evaluation LLM call returns `should_go_deeper: true/false`. The engine reads this flag and increments `current_depth` accordingly. It's an LLM-driven state machine.
- "What's the cold start problem for the factual questions?"
  → Phase 4 depends on questions being pre-loaded in Supabase with embeddings. If the DB is empty or down, Phase 4 silently skips. Fix: fallback hardcoded question set.

### Cost / Business Questions
- "How much does one interview cost?"
  → ~$0.25-0.30 in API costs (Claude ~$0.24 + ElevenLabs ~$0.03).
- "How would you reduce cost without killing quality?"
  → Cache evaluation results for repeated question patterns. Use Haiku for the evaluation step (cheaper, still JSON-capable). Batch questions into a single prompt where possible.

### Security / Privacy Questions
- "You're storing resumes in Supabase — how do you handle PII?"
  → Currently no encryption at rest beyond Supabase's default. Need: field-level encryption for name/email, row-level security policies, and a data retention policy.
- "The service role key bypasses RLS — is it safe?"
  → Yes on the server side. Never expose it to the client. The backend reads it from env vars only.

### What You'd Add / Improve
Good answers that show initiative:
- Stream LLM responses instead of waiting for full output (cuts perceived latency)
- Add MCP server layer so the interview engine can be used as a tool by external agents
- Add video analysis (webcam) for body language and eye contact signals
- Add session persistence (Redis) so interviews can be resumed after a disconnect
- Add an "interviewer memory" embedding — compress old turns instead of passing full history

---

## 6. The Socratic Depth System Explained Simply

The interviewer drills your project like peeling an onion:

| Depth | What They Ask | Example for "you built a chatbot" |
|-------|--------------|-----------------------------------|
| 1 | What is it and why? | "What does it do and who uses it?" |
| 2 | Why these choices? | "Why did you choose transformer over LSTM?" |
| 3 | How did you build it? | "What training setup, what metrics, what edge cases?" |
| 4 | What broke and what's production-hard? | "What failure modes did you find? How would you monitor it?" |
| 5 | What's the theory? | "Explain attention mathematically. What are the complexity trade-offs?" |

**How the system decides to go deeper:** The LLM evaluates your answer and returns `should_go_deeper`. If your scores are high (typically understanding + accuracy both >6), it advances depth. If scores are low, you get a hint or stay at the same depth.

**To stay at depth 2-3 (comfortable zone):** Give complete answers but don't demonstrate complete mastery. Acknowledge gaps constructively.
**To reach depth 4-5:** Show you've thought beyond implementation — production concerns, failure modes, theory.

---

## 7. Multi-Modal Talking Points (Strong Interview Signal)

This is what interviewers in 2025 care about. Use these:

"This system is multi-modal in two distinct ways: the input is both a document (PDF resume) and audio (voice responses), and the output is both structured text (evaluation JSON) and synthesized audio (TTS questions). The LLM layer itself is text-only, but the system wraps it with audio I/O — Whisper STT converts voice to text, the LLM processes text, and ElevenLabs converts text back to speech. This architecture means you could swap any single modality without touching the others."

"The anxiety detection is a fusion of two modalities — acoustic features (WPM, filler word rate measured on audio) combined with semantic features (hedging language analyzed by the LLM on the transcript). Neither alone is sufficient: you can speak confidently but write uncertainly, or stutter physically while writing clearly. Fusing both gives better signal."

---

## 8. Supabase Restore — Simple Instructions

Your free Supabase project pauses after 7 days of no activity.

**To restore:**
1. Go to supabase.com → Dashboard
2. Click your project (it shows "Paused")
3. Click "Restore project"
4. Wait ~1-2 minutes

**That's it.** All your tables, data, functions, and pgvector extension are preserved exactly as they were. You don't recreate anything. The only thing lost is the compute that was running — the database storage is untouched.

If your project was deleted (not paused), that's different — then you'd need to recreate the schema. But a pause is just hibernation.
