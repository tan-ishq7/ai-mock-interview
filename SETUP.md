# Setup Guide — AI Mock Interview System

## Prerequisites
- Python 3.11 or 3.12
- pip
- A Supabase account (free at supabase.com)
- An Anthropic API key (free $5 credit at console.anthropic.com)

---

## Step 1 — Get the Code

Unzip `april-mock-interview.zip` into a folder of your choice.

---

## Step 2 — Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python -m venv venv
source venv/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

> **Warning:** `sentence-transformers` pulls in PyTorch (~2GB). First install is slow. Make sure you have disk space and a stable connection.

---

## Step 4 — Set Up Supabase

1. Go to [supabase.com](https://supabase.com) → sign up → **New project**
2. Give it a name, set a database password, choose a region close to you
3. Wait ~2 minutes for it to provision
4. Go to **SQL Editor** (left sidebar) → **New query**
5. Open `supabase_schema.sql` from this folder, paste the entire contents, click **Run**
6. You should see "Success" and 18 rows in `ml_questions`

---

## Step 5 — Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   # Windows
   copy .env.example .env

   # Mac / Linux
   cp .env.example .env
   ```

2. Open `.env` and fill in your keys:
   - **ANTHROPIC_API_KEY** → [console.anthropic.com](https://console.anthropic.com) → API Keys
   - **SUPABASE_URL** → Supabase project → Settings → API → Project URL
   - **SUPABASE_ANON_KEY** → same page → anon public key
   - **SUPABASE_SERVICE_ROLE_KEY** → same page → service_role key
   - **ELEVENLABS_API_KEY** → [elevenlabs.io](https://elevenlabs.io) → Profile → API Keys
   - **ELEVENLABS_VOICE_ID** → Voice Library → pick a voice → copy its ID

   > Gemini and OpenAI keys are optional. Claude is the active default.

---

## Step 6 — Generate Embeddings for Phase 4 RAG (Important)

The Supabase schema seeds 18 ML questions but without embeddings (SQL can't run ML models).
To enable proper vector search, run the indexer once after setup:

```bash
python -m backend.knowledge.question_indexer
```

This downloads `all-MiniLM-L6-v2` locally, generates 384-dim embeddings for each question,
and uploads them to Supabase. Takes ~30 seconds. Only needs to be run once.

> If you skip this, Phase 4 still works via text-based fallback (category keyword match)
> but won't use semantic similarity to pick the most relevant questions for each candidate.

## Step 7 — Run the Server

```bash
python -m uvicorn backend.main:app --port 8000 --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) — you should see the Swagger UI with all endpoints.

---

## Step 7 — Test It

### Upload a resume:
In the Swagger UI → `/api/resume/upload` → try it → upload a PDF resume.

You should get back a `candidate_id` and structured JSON of the resume.

### Start an interview:
POST `/api/interview/start` with the `candidate_id` from above.

### Send a response:
POST `/api/interview/respond` with the `session_id` and your answer text.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `getaddrinfo failed` | Supabase project paused | Go to supabase.com → your project → Restore |
| `ANTHROPIC_API_KEY must be set` | .env not loaded | Make sure .env is in the project root, not inside backend/ |
| `torch` install fails | Disk space / network | Try `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| `422 Unprocessable Entity` on upload | Not a PDF file | Only PDF files are accepted |
| Port 8000 already in use | Another process running | Use `--port 8001` or kill the other process |

---

## Supabase Free Tier Note

Projects **pause after 7 days of no activity**. To restore:
1. Go to [supabase.com](https://supabase.com) → your project (shows "Paused")
2. Click **Restore project** → wait ~2 minutes
3. No data loss, no schema recreation needed

---

## Project Structure (Quick Reference)

```
backend/
  main.py              FastAPI app entry point
  config.py            Reads .env, exposes settings object
  database/
    supabase_client.py Supabase connection (cached)
    models.py          Pydantic models (Python types for DB tables)
  resume/
    parser.py          PDF → structured JSON via LLM
    router.py          POST /api/resume/upload
  interview/
    engine.py          5-phase state machine (core logic)
    prompt_templates.py All LLM prompts
    router.py          /api/interview/* endpoints
  voice/
    stt.py             Speech-to-text (Whisper)
    tts.py             Text-to-speech (ElevenLabs)
    anxiety_detector.py Rule-based anxiety detection
    router.py          /api/voice/* endpoints
  evaluation/
    report_generator.py Final report (LLM narrative + scores)
    socratic_metric.py  Phase 2/3 scoring
    factual_scorer.py   Phase 4 scoring
    behavioral_scorer.py Phase 5 scoring
    router.py           /api/evaluation/* endpoints
  knowledge/
    question_indexer.py  Load ML questions into Supabase with embeddings
    question_retriever.py Vector search for Phase 4 questions
```

---

## Documentation (read these)

| File | What it covers |
|------|---------------|
| `docs/1-project-architecture.md` | Code structure, request flow, ER diagram, schema bugs |
| `docs/2-ai-ml-masterclass.md` | RAG, MCP, orchestration, transformers, prompt engineering |
| `docs/3-tech-foundations.md` | FastAPI, SQL, data warehousing, DSA, OS/networking basics |
| `candidates/sarthak-chaudhary/interview-prep.md` | Personalized prep for Sarthak's resume |
| `answer-sheet-1.md` | Minimum passing bar answers |
| `answer-sheet-2.md` | Solid fresher answers |
| `answer-sheet-3.md` | Strong candidate answers + how to present THIS project |
| `cheatsheet-fresher.md` | API costs, model breakdown, interview questions |
