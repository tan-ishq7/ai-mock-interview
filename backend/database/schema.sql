-- ==========================================================================
-- AI Mock Interview Agent – Supabase / PostgreSQL schema
-- ==========================================================================
-- Run this file once against your Supabase SQL editor to bootstrap the DB.

-- Extensions -----------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";   -- pgvector for ML question embeddings


-- 1. candidates --------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidates (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name             TEXT NOT NULL,
    email            TEXT NOT NULL UNIQUE,
    resume_raw_text  TEXT DEFAULT '',
    resume_sections  JSONB DEFAULT '{}',
    identified_field TEXT DEFAULT '',
    primary_project  JSONB DEFAULT '{}',
    secondary_project JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT now()
);


-- 2. interview_sessions ------------------------------------------------
CREATE TABLE IF NOT EXISTS interview_sessions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id  UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    started_at    TIMESTAMPTZ DEFAULT now(),
    ended_at      TIMESTAMPTZ,
    current_phase INT DEFAULT 1,
    status        TEXT DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_candidate
    ON interview_sessions(candidate_id);


-- 3. conversation_history ----------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_history (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id       UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    phase            INT NOT NULL,
    role             TEXT NOT NULL CHECK (role IN ('system', 'assistant', 'user')),
    content          TEXT NOT NULL,
    depth_level      INT,
    is_hint          BOOLEAN DEFAULT FALSE,
    hint_recovery    BOOLEAN,
    anxiety_detected BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_convo_session
    ON conversation_history(session_id);

CREATE INDEX IF NOT EXISTS idx_convo_session_phase
    ON conversation_history(session_id, phase);


-- 4. ml_questions (knowledge base with vector embeddings) --------------
CREATE TABLE IF NOT EXISTS ml_questions (
    id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question  TEXT NOT NULL,
    answer    TEXT NOT NULL,
    category  TEXT DEFAULT '',
    source    TEXT DEFAULT '',
    embedding VECTOR(384)      -- sentence-transformers all-MiniLM-L6-v2 output dim
);

CREATE INDEX IF NOT EXISTS idx_ml_questions_category
    ON ml_questions(category);

-- Approximate-nearest-neighbour index for similarity search
CREATE INDEX IF NOT EXISTS idx_ml_questions_embedding
    ON ml_questions
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);


-- 5. evaluations (per-phase scoring) -----------------------------------
CREATE TABLE IF NOT EXISTS evaluations (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id            UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    phase                 INT NOT NULL,
    score                 REAL DEFAULT 0,
    max_depth_reached     INT DEFAULT 0,
    hints_given           INT DEFAULT 0,
    hints_recovered       INT DEFAULT 0,
    factual_correct       INT DEFAULT 0,
    factual_total         INT DEFAULT 0,
    behavioral_visionary  REAL DEFAULT 0,
    behavioral_grounded   REAL DEFAULT 0,
    behavioral_teamplayer REAL DEFAULT 0,
    details               JSONB DEFAULT '{}',
    created_at            TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evaluations_session
    ON evaluations(session_id);


-- 6. reports (final interview report) ----------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    candidate_id    UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    overall_score   REAL DEFAULT 0,
    phase_scores    JSONB DEFAULT '{}',
    strengths       JSONB DEFAULT '[]',
    weaknesses      JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    report_text     TEXT DEFAULT '',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reports_session
    ON reports(session_id);

CREATE INDEX IF NOT EXISTS idx_reports_candidate
    ON reports(candidate_id);
