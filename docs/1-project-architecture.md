# Project Architecture — AI Mock Interview System
> How the code is organized, how data flows, the ER diagram, and what's wrong with it.

---

## 1. Directory Structure (How the Code Is Saved)

```
April_I_love_you_2/
│
├── backend/                        ← All Python server code
│   ├── main.py                     ← FastAPI app entry point. Registers all routers.
│   ├── config.py                   ← Reads .env file. Single Settings object used everywhere.
│   │
│   ├── database/
│   │   ├── models.py               ← Pydantic models (Python types that mirror DB tables)
│   │   └── supabase_client.py      ← Creates and caches the Supabase connection
│   │
│   ├── resume/
│   │   ├── parser.py               ← Sends PDF to Claude/Gemini, gets structured JSON back
│   │   └── router.py               ← POST /api/resume/upload endpoint
│   │
│   ├── interview/
│   │   ├── engine.py               ← The interview state machine (CORE of the system)
│   │   ├── prompt_templates.py     ← All LLM prompts (system, phase 1-5, hint, eval)
│   │   └── router.py               ← /api/interview/* endpoints
│   │
│   ├── voice/
│   │   ├── stt.py                  ← Speech-to-text via Whisper
│   │   ├── tts.py                  ← Text-to-speech via ElevenLabs
│   │   ├── anxiety_detector.py     ← Rule-based anxiety detection on transcripts
│   │   └── router.py               ← /api/voice/* endpoints
│   │
│   ├── evaluation/
│   │   ├── socratic_metric.py      ← Scores depth + hint usage for phases 2/3
│   │   ├── factual_scorer.py       ← Scores factual Q accuracy for phase 4
│   │   ├── behavioral_scorer.py    ← Scores behavioral phase 5
│   │   ├── report_generator.py     ← Assembles final report, calls LLM for narrative
│   │   └── router.py               ← /api/evaluation/* endpoints
│   │
│   └── knowledge/
│       ├── question_indexer.py     ← Inserts ML questions + embeddings into Supabase
│       └── question_retriever.py  ← Embeds field query, retrieves relevant questions via vector search
│
├── candidates/                     ← Candidate resumes and prep docs (local, not served)
│   └── sarthak-chaudhary/
│       ├── resume.pdf
│       └── interview-prep.md
│
├── docs/                           ← Documentation (this file and others)
│
├── .env                            ← API keys (NEVER commit this)
├── ideas-v1.md
├── feedback-v1.md
└── answer-sheet-*.md
```

### How a Request Flows Through the Code

```
User uploads PDF
    ↓
POST /api/resume/upload          [resume/router.py]
    ↓
parse_resume_pdf(bytes)          [resume/parser.py]
    → Sends PDF to Claude/Gemini
    → Gets JSON back (name, email, projects, skills, identified_field)
    ↓
_store_candidate(parsed)         [resume/router.py]
    → Writes to Supabase `candidates` table
    → Returns candidate_id (UUID)
    ↓
Returns: { candidate_id, data }  ← Front end stores this

User starts interview
    ↓
POST /api/interview/start        [interview/router.py]
    → Calls create_session(candidate_data) [engine.py]
    → Creates InterviewState in memory
    → Calls generate_first_message(state)
    → LLM generates opening greeting + Phase 1 question
    ↓
Returns: { session_id, message }

User sends answer
    ↓
POST /api/interview/respond      [interview/router.py]
    → Calls process_candidate_response(state, text)  [engine.py]
    → LLM evaluates response (scores + flags)
    → Engine decides: hint? deeper? advance phase? anxiety break?
    → LLM generates next question
    ↓
Returns: { message, phase, depth_level, is_hint, anxiety_break, evaluation }

After Phase 5 completes
    ↓
POST /api/evaluation/report      [evaluation/router.py]
    → generate_report(session_id)  [report_generator.py]
    → Compute scores for all phases
    → LLM generates narrative report text
    → Store in Supabase (evaluations + reports tables)
    ↓
Returns: full report with scores and text
```

---

## 2. The Interview Engine — State Machine

This is the most important part of the codebase. It's in `backend/interview/engine.py`.

```
InterviewState (lives in memory, one per active session)
│
├── session_id, candidate data
├── current_phase (1-5)
├── conversation[] — full history
├── phase_conversations{1..5}[] — per-phase history
│
├── Depth tracking (phases 2/3):
│   ├── current_depth (1-5)
│   ├── questions_at_depth
│   └── max_depth_reached{2,3}
│
├── Hint tracking:
│   ├── hints_given{2,3}
│   └── hints_recovered{2,3}
│
├── Phase 4 (factual):
│   ├── factual_questions[] — retrieved from Supabase
│   ├── factual_index
│   └── factual_evaluations[]
│
└── Phase 5 (behavioral):
    ├── behavioral_index
    └── behavioral_scores[]
```

### Decision Loop (happens after EVERY candidate response)

```
Candidate sends response
         ↓
Append to conversation[]
         ↓
_evaluate_response_llm()   ← LLM call #1: scores + flags
         ↓
    ┌────┴─────────────────────────────┐
    │  anxiety_detected?               │
    │  (from LLM or voice)             │
    └──── YES → send pause message     │
               set anxiety_break flag  │
               on next message, resume │
         ↓ NO                          │
    ┌────┴──────────────┐              │
    │  should_give_hint?│              │
    └── YES → _generate_hint()         │
              LLM call #2: hint text   │
         ↓ NO                          │
    ┌────┴──────────────┐
    │ should_go_deeper? │
    └── YES → increment current_depth  │
         ↓ NO/done depth               │
    is_phase_complete?
         ↓ YES → _advance_phase()
         ↓ NO  → _continue_phase()
                 LLM call #2: next question
```

---

## 3. The LLM Layer — Provider Abstraction

```python
# In engine.py
def _call_llm(system_prompt, conversation):
    if provider == "claude":   → _call_claude()
    if provider == "gemini":   → _call_gemini()
    # openai: commented out
```

Every LLM call takes:
- `system_prompt`: who the LLM is (persona + phase instructions)
- `conversation`: full list of `{role, content}` dicts so far

This means the LLM has full memory of the interview — it re-reads the entire conversation history on every call. This is stateless on the LLM side (no built-in memory) but the server maintains state.

**Cost implication:** Conversation grows over time → input tokens grow → cost grows. A 28-question interview might have 10,000 tokens of conversation history by the end, passed on every call.

---

## 4. The Database — ER Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           candidates                                 │
├──────────────────────────────────────────────────────────────────────┤
│ id                UUID        PK                                     │
│ name              TEXT                                               │
│ email             TEXT                                               │
│ resume_raw_text   TEXT        Full LLM-parsed JSON as string        │
│ resume_sections   JSONB       {about_me, education, work_exp...}    │
│ identified_field  TEXT        "Agentic AI", "NLP", "CV"...          │
│ primary_project   JSONB       {title, description, technologies[]}  │
│ secondary_project JSONB       same structure                        │
└──────────────────────────────────────────────────────────────────────┘
                        │
                        │ 1:N (one candidate → many sessions)
                        ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        interview_sessions                            │
├──────────────────────────────────────────────────────────────────────┤
│ id                UUID        PK                                     │
│ candidate_id      UUID        FK → candidates.id                    │
│ started_at        TIMESTAMP                                          │
│ ended_at          TIMESTAMP   NULL until complete                   │
│ current_phase     INT         1-5                                   │
│ status            TEXT        in_progress | completed | cancelled   │
└──────────────────────────────────────────────────────────────────────┘
          │                              │
          │ 1:N                          │ 1:N
          ↓                             ↓
┌──────────────────────┐    ┌─────────────────────────────────────────┐
│  conversation_msgs   │    │              evaluations                 │
├──────────────────────┤    ├─────────────────────────────────────────┤
│ id          UUID PK  │    │ id              UUID      PK            │
│ session_id  UUID FK  │    │ session_id      UUID      FK            │
│ phase       INT      │    │ phase           INT       1-5           │
│ role        TEXT     │    │ score           FLOAT                   │
│ content     TEXT     │    │ max_depth_reached INT                   │
│ depth_level INT      │    │ hints_given     INT                     │
│ is_hint     BOOL     │    │ hints_recovered INT                     │
│ hint_recovery BOOL   │    │ factual_correct INT                     │
│ anxiety_detected BOOL│    │ factual_total   INT                     │
└──────────────────────┘    │ behavioral_visionary FLOAT             │
                            │ behavioral_grounded  FLOAT             │
                            │ behavioral_teamplayer FLOAT            │
                            │ details         JSONB                  │
                            └─────────────────────────────────────────┘
          │
          │ 1:1 (one session → one report)
          ↓
┌─────────────────────────────────────────────────────────────────────┐
│                              reports                                 │
├──────────────────────────────────────────────────────────────────────┤
│ id                UUID        PK                                     │
│ session_id        UUID        FK → interview_sessions.id            │
│ candidate_id      UUID        FK → candidates.id  (denormalized)    │
│ overall_score     FLOAT       0-100                                 │
│ phase_scores      JSONB       breakdown per phase                   │
│ strengths         TEXT[]      list of bullet strings                │
│ weaknesses        TEXT[]                                            │
│ recommendations   TEXT[]                                            │
│ report_text       TEXT        full LLM narrative                    │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           ml_questions                               │
├──────────────────────────────────────────────────────────────────────┤
│ id          UUID     PK                                              │
│ question    TEXT                                                     │
│ answer      TEXT     ground truth (never shown to candidate)        │
│ category    TEXT     "NLP", "Computer Vision", "Reinforcement..."   │
│ source      TEXT     where the question came from                   │
│ embedding   VECTOR(384)  pgvector column for similarity search      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Why the Schema Is Designed This Way

### JSONB for resume_sections, projects
**Why:** Resume structure is highly variable. One candidate has 5 projects, another has 1. One has publications, another doesn't. JSONB lets you store arbitrary structured data without needing a separate table for each resume field. You query it in Postgres like: `resume_sections->>'about_me'`.

**Trade-off:** You lose type validation at the DB level. Postgres doesn't enforce that `resume_sections.education` is always an array. That validation lives in the Python Pydantic models instead.

### All evaluation fields in one `evaluations` table
**Why:** Simple — one row per phase per session. The phase number tells you which columns are relevant (phase 4 → factual_correct/factual_total, phase 5 → behavioral_* columns).

**Trade-off:** Every row has many NULL columns. This is called a "wide table with sparse columns" — it works but is inelegant.

### `reports.candidate_id` is a denormalization
**Why:** You could always get candidate_id by joining reports → interview_sessions → candidates. But having it directly in reports makes queries faster and simpler: `SELECT * FROM reports WHERE candidate_id = ?` without a join.

**This is intentional.** In data warehousing, this pattern (repeating data to avoid joins) is called denormalization and is standard in analytics tables.

### `ml_questions` has a `VECTOR(384)` column
**Why:** This is pgvector — Postgres's extension for storing and searching embedding vectors. The number 384 matches the output dimension of `all-MiniLM-L6-v2`. You search it like: `ORDER BY embedding <=> query_vector LIMIT 5`. This is how the system finds relevant questions for a candidate's field without doing keyword matching.

---

## 6. Schema Issues — What's Actually Wrong

### Issue 1 (CRITICAL): conversation_messages is never written to
The `ConversationMessage` Pydantic model exists in `database/models.py`. The table is in the schema. But **nowhere in the code does anything write to this table**. The conversation is stored only in `InterviewState` in memory and lost when the server restarts.

**What should happen:** After every LLM response, write it to `conversation_messages`. This gives you a permanent audit trail and lets interviews resume after reconnection.

**Real-world consequence:** You cannot replay, audit, or analyze conversations. Hiring systems that can't audit decisions are a compliance problem.

### Issue 2 (CRITICAL): interview_sessions table is never written to either
Same problem. The session exists in Python memory but nothing in the code calls `supabase.table("interview_sessions").insert(...)`. So the table exists but is always empty.

### Issue 3 (DESIGN): Evaluations table has sparse columns per phase
Phase 4 rows have NULL for all the behavioral columns. Phase 5 rows have NULL for all the depth/hint columns. This is a "polymorphic table" anti-pattern.

**Better design:** Separate tables — `socratic_evaluations`, `factual_evaluations`, `behavioral_evaluations` — each with exactly the columns they need. Join via session_id and phase.

### Issue 4 (DESIGN): No created_at / updated_at timestamps
None of the tables have timestamp columns (except `interview_sessions.started_at`). You can't tell when a candidate was added, when a report was generated, or track trends over time. Always add `created_at TIMESTAMP DEFAULT now()` to every table.

### Issue 5 (MINOR): ml_questions.embedding not in Pydantic model
The `MLQuestion` Pydantic model in `models.py` doesn't have an `embedding` field. The actual Postgres table needs a `VECTOR(384)` column for pgvector to work. This creates a gap between the Python model and the actual DB schema — they're out of sync.

### Issue 6 (DESIGN): reports.candidate_id could drift
If a candidate's data is updated, `reports.candidate_id` still points to the right candidate, but `reports.phase_scores` is a snapshot at the time of the interview. This is fine — it's intentional denormalization — but should be documented. If you add a "recalculate report" feature later, you need to be careful about what's canonical.

---

## 7. What the Ideal Schema Would Look Like

```
candidates         → same (JSONB for resume is fine)
interview_sessions → SAME + actually write to it
conversation_messages → SAME + actually write to it
ml_questions       → add embedding to Pydantic model, document pgvector requirement
evaluations        → SPLIT into: socratic_evals, factual_evals, behavioral_evals
reports            → SAME
+ add created_at to ALL tables
```

The biggest structural win would be writing conversations to the DB. Right now the most valuable data (what was asked, what was answered, word for word) is being thrown away.

---

## 8. How to Think About This Architecture (The Mental Model)

```
STATELESS LAYER (LLM + Supabase)
    ← Claude/Gemini: doesn't remember anything between calls
    ← Supabase: permanent storage, queries, vector search

STATEFUL LAYER (Python server memory)
    ← InterviewState: holds the entire session in RAM
    ← _sessions dict: maps session_id → InterviewState
    ← Lives only while the server process is alive

TRANSPORT LAYER (FastAPI + REST)
    ← HTTP endpoints that bridge the frontend ↔ server
    ← Stateless HTTP: each request carries the session_id to identify the state
```

The server is stateful (it holds session state in RAM), but the LLM is stateless (you send the full conversation each time). This is the standard pattern for LLM-based applications.

**Redis** is what you'd add to make the server stateful-but-persistent: serialize `InterviewState` to Redis with TTL, so server restarts don't kill active sessions.
