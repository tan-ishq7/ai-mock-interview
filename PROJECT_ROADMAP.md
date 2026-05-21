# AI Mock Interview Agent — Project Roadmap

## 1. Product Overview

An AI-powered mock interview system that simulates a realistic ML engineering interview. The system parses a candidate's resume PDF, conducts a structured 5-phase interview with voice interaction, evaluates performance using custom metrics, and generates a detailed report.

**Target Role:** Machine Learning Engineer
**Tone:** Professional, concise, no over-enthusiasm. Process answers and move to next question. Never use words like "incredible", "great answer". Never agree too much with the student.

---

## 2. System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend    │────▶│  Backend API │────▶│  GPT-5.4        │
│  (React)    │◀────│  (FastAPI)   │◀────│  (Reasoning)    │
└──────┬──────┘     └──────┬───────┘     └─────────────────┘
       │                   │
       │            ┌──────┴───────┐
       │            │   Supabase   │
       │            │  (Database)  │
       │            └──────────────┘
       │
  ┌────┴─────┐     ┌──────────────┐
  │ Whisper  │     │  ElevenLabs  │
  │ (STT)    │     │  (TTS)       │
  └──────────┘     └──────────────┘
```

### Tech Stack
| Component          | Technology                                      |
|--------------------|--------------------------------------------------|
| LLM                | OpenAI GPT-5.4 (reasoning model)                 |
| Speech-to-Text     | OpenAI Whisper                                   |
| Text-to-Speech     | ElevenLabs (Voice ID: `lZORFNDokoBmfd0S06vf`)   |
| Resume Parsing     | OpenAI GPT-5.4 (not pymupdf/pdfplumber)          |
| Database           | Supabase (PostgreSQL)                            |
| Embedding Model    | 384-dimensional model (all-MiniLM-L6-v2)        |
| Backend            | Python + FastAPI                                 |
| Frontend           | React (Vite + TailwindCSS)                       |
| ML Questions Bank  | GitHub: andrewekhalel/MLQuestions + self-generated|

---

## 3. Interview Phases

### Phase 1: Background & Introduction
- Parse resume "About Me" / "Education" / summary sections
- Ask warm-up questions: "Tell me about yourself", "Walk me through your background", "Why ML?"
- **Evaluation:** No scoring (ice-breaker phase)

### Phase 2: Deep-Dive Project #1 (Russian Doll / Socratic Method)
- Identify the most important project from resume (first in Experience or Projects section)
- **Drilling Strategy:**
  1. "What exactly did you build?"
  2. "How does this work end-to-end?"
  3. Drill into specific ML concepts used
  4. Drill into implementation choices (why X over Y?)
  5. Drill into limitations, alternatives, tradeoffs
  6. Continue until the candidate cannot answer
- **Hints:** If candidate is stuck, provide a nudge/hint and track whether they recover
- **Evaluation:** Socratic Depth Metric (how many levels deep before failure) + Hint Recovery Rate

### Phase 3: Deep-Dive Project #2 (Russian Doll / Socratic Method)
- Pick a different project (e.g., research internship, different domain)
- Same drilling methodology as Phase 2
- **Evaluation:** Same as Phase 2

### Phase 4: Factual ML Knowledge Questions
- Use ML questions from GitHub repo (andrewekhalel/MLQuestions) stored in markdown
- Use 384-dim embedding model to match questions to candidate's field (NLP, CV, etc.)
- If insufficient questions found, generate custom factual questions with verified answers
- Ask 4-5 questions minimum
- **Evaluation:** Accuracy score (correct/total), partial credit for close answers

### Phase 5: Behavioral Questions
- Standard behavioral questions:
  - "Where do you see yourself in five years?"
  - "What are the most important challenges you have faced?"
  - "How do you work in a team?"
  - "Do you have any questions for me?"
- **Evaluation:** Visionary thinking + Groundedness/Realism + Team Player assessment

---

## 4. Evaluation Framework

### Phase 1: No Evaluation
Ice-breaker, no scoring.

### Phase 2 & 3: Socratic Depth Metric
```
Socratic Depth Score = (Max depth reached before failure) / (Total questions asked)

Levels:
  Level 1: Surface-level description (what they built)
  Level 2: Architecture/workflow explanation
  Level 3: Core ML concept understanding
  Level 4: Implementation tradeoffs and alternatives
  Level 5: Edge cases, failure modes, mathematical foundations

Hint Recovery Rate = (Questions answered correctly after hint) / (Total hints given)
```

Scoring rubric:
| Depth Level | Score | Description                              |
|-------------|-------|------------------------------------------|
| 1           | 20%   | Can describe what they built              |
| 2           | 40%   | Can explain how it works                  |
| 3           | 60%   | Understands underlying ML concepts        |
| 4           | 80%   | Can discuss tradeoffs and alternatives    |
| 5           | 100%  | Deep theoretical + practical mastery      |

### Phase 4: Factual Accuracy
```
Score = (Correct answers / Total questions) * 100
Partial credit via LLM-judged semantic similarity to ground truth
```

### Phase 5: Behavioral Assessment
Three sub-scores (each 1-5 scale):
- **Visionary Thinking:** Does the candidate have clear long-term goals?
- **Groundedness:** Are their answers realistic and self-aware?
- **Team Player:** Do they demonstrate collaboration skills?

```
Behavioral Score = (Visionary + Grounded + TeamPlayer) / 15 * 100
```

---

## 5. Voice & Empathy System

### Speech Pipeline
1. **Candidate speaks** → Audio captured in browser
2. **Whisper STT** → Transcribes to text
3. **GPT-5.4** → Processes response, generates next question
4. **ElevenLabs TTS** → Synthesizes interviewer voice (Dr. Raj Dandekar clone)
5. **Audio plays** → Candidate hears the question

### Anxiety Detection (Voice-Based)
Monitor candidate's speech patterns:
- **Speech rate** (words per minute) — too fast indicates anxiety
- **Stuttering/hesitation** detection — repeated words, long pauses, filler words
- **Voice tremor** — pitch variability analysis

When anxiety detected:
1. Pause the interview
2. Say: "Let's take a moment. Take a deep breath, there's no rush. We can continue whenever you're ready."
3. Resume questioning chain from where it was paused

### Future Version: Video Analysis
- Facial expression analysis for anxiety/stress detection
- Eye contact tracking
- Body language assessment

---

## 6. Database Schema (Supabase)

### Tables

```sql
-- Candidates
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    name TEXT NOT NULL,
    email TEXT,
    resume_raw_text TEXT,
    resume_sections JSONB,  -- parsed sections
    identified_field TEXT,   -- NLP, CV, etc.
    primary_project JSONB,
    secondary_project JSONB
);

-- Interview Sessions
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id),
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    current_phase INTEGER DEFAULT 1,
    status TEXT DEFAULT 'in_progress'  -- in_progress, completed, paused
);

-- Conversation History
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id),
    phase INTEGER NOT NULL,
    role TEXT NOT NULL,          -- interviewer / candidate
    content TEXT NOT NULL,
    depth_level INTEGER,         -- for phase 2/3 drill-down tracking
    is_hint BOOLEAN DEFAULT false,
    hint_recovery BOOLEAN,       -- did candidate recover after hint?
    anxiety_detected BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ML Questions Bank
CREATE TABLE ml_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,               -- NLP, CV, Core ML, etc.
    embedding VECTOR(384),       -- for similarity search
    source TEXT DEFAULT 'github' -- github or generated
);

-- Evaluation Results
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id),
    phase INTEGER NOT NULL,
    score FLOAT,
    max_depth_reached INTEGER,   -- phase 2/3
    hints_given INTEGER,
    hints_recovered INTEGER,
    factual_correct INTEGER,     -- phase 4
    factual_total INTEGER,
    behavioral_visionary FLOAT,  -- phase 5
    behavioral_grounded FLOAT,
    behavioral_teamplayer FLOAT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Final Reports
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES interview_sessions(id),
    candidate_id UUID REFERENCES candidates(id),
    overall_score FLOAT,
    phase_scores JSONB,
    strengths TEXT[],
    weaknesses TEXT[],
    recommendations TEXT[],
    report_text TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 7. Project Structure

```
April_I_love_you_2/
├── .env                        # API keys (gitignored)
├── .gitignore
├── requirements.txt
├── PROJECT_ROADMAP.md
│
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings & env vars
│   │
│   ├── resume/
│   │   ├── __init__.py
│   │   ├── parser.py           # OpenAI-based PDF parser
│   │   └── section_extractor.py # Extract structured sections
│   │
│   ├── interview/
│   │   ├── __init__.py
│   │   ├── engine.py           # Main interview orchestrator
│   │   ├── phase1_background.py
│   │   ├── phase2_project_deep_dive.py
│   │   ├── phase3_project_deep_dive_2.py
│   │   ├── phase4_factual.py
│   │   ├── phase5_behavioral.py
│   │   ├── prompt_templates.py  # All LLM prompt templates
│   │   └── hint_system.py       # Hint generation & tracking
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt.py              # Whisper speech-to-text
│   │   ├── tts.py              # ElevenLabs text-to-speech
│   │   └── anxiety_detector.py  # Voice pattern analysis
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── socratic_metric.py   # Phase 2/3 depth scoring
│   │   ├── factual_scorer.py    # Phase 4 accuracy scoring
│   │   ├── behavioral_scorer.py # Phase 5 behavioral scoring
│   │   └── report_generator.py  # Final report creation
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── ml_questions.md      # Downloaded from GitHub
│   │   ├── question_indexer.py  # Embed & index questions
│   │   └── question_retriever.py # Similarity search
│   │
│   └── database/
│       ├── __init__.py
│       ├── supabase_client.py   # Supabase connection
│       ├── models.py            # Pydantic models
│       └── schema.sql           # Table creation SQL
│
├── frontend/                    # React (Vite + TailwindCSS)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── pages/
│       │   ├── UploadResume.tsx  # PDF upload + preview
│       │   ├── Interview.tsx     # Chat + voice UI
│       │   └── Report.tsx        # Final evaluation report
│       ├── components/
│       │   ├── AudioRecorder.tsx  # Browser mic capture
│       │   ├── ChatBubble.tsx     # Message display
│       │   └── PhaseIndicator.tsx # Shows current phase
│       ├── hooks/
│       │   ├── useAudioRecorder.ts
│       │   └── useInterview.ts
│       └── services/
│           └── api.ts            # Backend API client
│
└── tests/
    ├── test_parser.py
    ├── test_interview_engine.py
    └── test_evaluation.py
```

---

## 8. V1 Task Breakdown (9 Tasks)

| # | Task | What Gets Built | Key Deliverables |
|---|------|----------------|------------------|
| 1 | **Project Setup + Supabase** | Scaffold project (backend + React frontend), create .env/.gitignore, create all Supabase tables, configure clients | Working project skeleton, DB ready |
| 2 | **Resume Parser** | Upload PDF → send to GPT-5.4 for parsing → extract structured sections (About, Education, Experience, Projects, Skills) → store in Supabase | `/api/upload-resume` endpoint, parsed JSON in DB |
| 3 | **ML Questions Bank** | Download questions from GitHub repo → embed with all-MiniLM-L6-v2 → store in Supabase with vector embeddings → similarity search by candidate field | Seeded question bank, `/api/search-questions` endpoint |
| 4 | **Interview Engine (All 5 Phases)** | Build the core interview orchestrator: Phase 1 (background), Phase 2/3 (Russian Doll deep-dives with hints), Phase 4 (factual from question bank), Phase 5 (behavioral). State machine for phase transitions. All prompt templates. | `/api/interview/next` endpoint, full conversation flow |
| 5 | **Voice System** | Whisper STT (audio→text), ElevenLabs TTS with Dr. Raj voice clone (text→speech), audio streaming endpoints | `/api/voice/transcribe`, `/api/voice/speak` endpoints |
| 6 | **Anxiety Detection + Break System** | Analyze speech rate, stuttering, filler words from Whisper output. Auto-pause interview when anxiety detected, comfort message, resume. | Anxiety flag in conversation history, break triggers |
| 7 | **Evaluation + Scoring System** | Socratic Depth Metric (Phase 2/3), Hint Recovery Rate, Factual Accuracy (Phase 4), Behavioral scores (Phase 5). All computed via GPT-5.4 as judge. | `/api/evaluate` endpoint, scores in DB |
| 8 | **Final Report Generator** | Compile all phase scores → generate comprehensive report with strengths, weaknesses, recommendations → store in Supabase | `/api/report/{session_id}` endpoint, PDF-style report |
| 9 | **React Frontend** | 3 pages: Resume Upload (drag-drop PDF), Interview (chat UI + mic record/playback + phase indicator), Report (score dashboard with per-phase breakdown) | Full working UI connected to all backend APIs |

---

## 9. Key Prompt Template Design Principles

1. **System prompt enforces tone:** "You are a senior ML engineering interviewer. Be professional and concise. Never use words like 'incredible', 'great answer', 'amazing'. Never agree enthusiastically. Process the answer and ask the next question."

2. **Russian Doll prompting:** Each follow-up question is generated with full conversation context + instruction to go one level deeper into the ML concept.

3. **Hint prompting:** When candidate is stuck (detected by vague/short answers or explicit "I don't know"), generate a nudge that points them in the right direction without giving the answer.

4. **Phase transition:** Managed by the orchestrator based on depth exhaustion (Phase 2/3), question count (Phase 4), or question completion (Phase 5).

---

## 10. Security & Configuration

- All API keys stored in `.env` file
- `.env` added to `.gitignore` — never committed
- Supabase Row Level Security enabled
- No keys hardcoded anywhere in source

---

## 11. Future Versions (Not in Current Scope)

- [ ] CI/CD pipeline → GitHub Actions → AWS Deploy
- [ ] Anti-cheating system (tab-switch detection, copy-paste monitoring)
- [ ] Video-based anxiety detection (facial expressions, eye contact)
- [ ] Multi-role support (Data Scientist, SWE, etc.)
- [ ] Interview recording & playback
