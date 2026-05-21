# Tech Foundations — Backend, SQL, DSA, and What Else to Know
> Mainly backend and data. OS/networking at the end — just topics, not deep dives.

---

## 1. FastAPI — The Backend Framework Used Here

FastAPI is what runs this server. It's a Python web framework built on top of Starlette (async web toolkit) and Pydantic (data validation).

### Why FastAPI Over Flask or Django
| | FastAPI | Flask | Django |
|--|---------|-------|--------|
| Speed | Async, fast | Sync by default | Sync by default |
| Auto docs | Yes (OpenAPI at /docs) | No | No |
| Validation | Built-in (Pydantic) | Manual | Forms-based |
| Best for | APIs, ML backends | Simple apps | Full-stack web |

### How It Works in This Project
```python
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    ...

app.include_router(router, prefix="/api/resume")
```

- `@router.post("/upload")` — registers an HTTP POST endpoint
- `async def` — non-blocking, can handle multiple requests without waiting
- `UploadFile` — Pydantic type that FastAPI automatically validates for you
- `include_router` — modular structure: each feature has its own router file

### Pydantic — Data Validation
Every request and response is validated by Pydantic models. If the data doesn't match the schema, FastAPI returns a 422 error automatically — before your code even runs.

```python
class Candidate(BaseModel):
    name: str
    email: str
    resume_sections: dict[str, Any]
```

This is why `models.py` exists — those Pydantic models are the type contract between the database and the rest of the code.

### REST API Conventions Used Here
| Method | Path | What it does |
|--------|------|-------------|
| POST | /api/resume/upload | Upload PDF, parse, store |
| POST | /api/interview/start | Create new session |
| POST | /api/interview/respond | Send candidate answer |
| GET | /api/evaluation/report/{id} | Get final report |
| GET | /api/health | Server liveness check |

**Status codes to know:** 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 422 Unprocessable Entity, 500 Internal Server Error.

---

## 2. Supabase + PostgreSQL

Supabase is a hosted Postgres database with extras: REST API (PostgREST), auth, realtime, and pgvector.

### How the Python Code Talks to Supabase
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Insert
supabase.table("candidates").insert({"name": "Sarthak", ...}).execute()

# Select
result = supabase.table("candidates").select("*").eq("id", some_id).execute()
rows = result.data  # list of dicts

# RPC (call a Postgres function)
supabase.rpc("match_ml_questions", {"query_embedding": [...], "match_count": 5}).execute()
```

This is PostgREST — it generates a REST API from the Postgres schema automatically. Under the hood it's still SQL.

### pgvector — Vector Search in Postgres
pgvector is a Postgres extension that adds a `VECTOR(n)` column type and similarity operators.

```sql
-- Find 5 most similar questions to a query embedding
SELECT question, answer, category
FROM ml_questions
ORDER BY embedding <=> '[0.1, -0.4, 0.8, ...]'::vector
LIMIT 5;
```

`<=>` is cosine distance (lower = more similar). pgvector also supports `<->` (L2/Euclidean) and `<#>` (negative inner product).

The index type for production scale: **HNSW** (Hierarchical Navigable Small World) — approximate nearest neighbor, much faster than exact search at scale.

```sql
CREATE INDEX ON ml_questions USING hnsw (embedding vector_cosine_ops);
```

---

## 3. SQL — Topics That Actually Come Up

You need SQL for: reading this project's data, understanding what DBT does, building LLM agents that query databases.

### Must Know
```sql
-- Basic SELECT
SELECT name, email FROM candidates WHERE identified_field = 'NLP';

-- JOIN (get sessions for a candidate)
SELECT s.id, s.status, s.started_at
FROM interview_sessions s
JOIN candidates c ON s.candidate_id = c.id
WHERE c.name = 'Sarthak';

-- Aggregation
SELECT phase, AVG(score), COUNT(*) 
FROM evaluations 
GROUP BY phase
HAVING AVG(score) < 50;  -- HAVING filters on aggregated result, WHERE filters on rows

-- Subquery
SELECT * FROM candidates
WHERE id IN (
    SELECT candidate_id FROM reports WHERE overall_score > 75
);

-- JSONB queries (Postgres specific — relevant for this project)
SELECT name, resume_sections->>'about_me' AS summary
FROM candidates;

SELECT * FROM candidates
WHERE resume_sections->'education' @> '[{"institution": "SRM"}]';
```

### Window Functions (Important for Analytics)
```sql
-- Rank candidates by score
SELECT 
    c.name,
    r.overall_score,
    RANK() OVER (ORDER BY r.overall_score DESC) as rank
FROM reports r
JOIN candidates c ON r.candidate_id = c.id;

-- Running average score
SELECT 
    session_id,
    phase,
    score,
    AVG(score) OVER (PARTITION BY session_id ORDER BY phase) as running_avg
FROM evaluations;
```

### Indexes
An index is a data structure that speeds up lookups at the cost of write speed and storage.

```sql
CREATE INDEX idx_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX idx_evals_session ON evaluations(session_id);
```

Without these, every `JOIN` on `candidate_id` does a full table scan — fine for 100 rows, terrible for 100,000.

---

## 4. Data Warehousing — The Big Picture

### Why a Separate Warehouse?
Your production database (Supabase) handles live transactions. Running heavy analytics on it can:
- Slow down live requests
- Lock rows during long queries
- Expose production data to analysts

A warehouse is a separate copy, optimized for reads.

### The Modern Data Stack (What Sarthak's Travel Copilot Used)
```
Source (Supabase) → Extract → Transform → Load → Warehouse → Visualize/Query

Tools:
Extract/Load: Airbyte, Fivetran, custom scripts
Transform: DBT (SQL-based transformations)
Warehouse: BigQuery, Snowflake, Redshift, DuckDB
Visualize: Tableau, Looker, Metabase
Orchestrate: Airflow (schedules the whole pipeline)
```

### DBT in Plain English
DBT (Data Build Tool) lets you write SQL `SELECT` statements that become tables/views in your warehouse. It handles dependency ordering, testing, and documentation.

```sql
-- models/candidate_scores.sql
SELECT 
    c.name,
    c.identified_field,
    r.overall_score,
    r.created_at
FROM {{ ref('candidates') }} c
JOIN {{ ref('reports') }} r ON c.id = r.candidate_id
WHERE r.overall_score IS NOT NULL
```

DBT compiles this into the right SQL for your warehouse and creates the `candidate_scores` table. `{{ ref() }}` ensures DBT knows the dependency order.

### Star Schema (Warehouse Design Pattern)
```
          FACT TABLE
         ┌──────────────┐
         │  fact_evals  │
         │  session_id  │──── dim_sessions ──── dim_candidates
         │  phase       │
         │  score       │──── dim_phases
         │  date_key    │──── dim_date
         └──────────────┘
```

Facts are measurable events (a score, a transaction). Dimensions describe them (who, when, what phase). This structure makes GROUP BY queries fast and intuitive.

---

## 5. DSA — What's Actually Relevant Here

You don't need LeetCode hard for an ML/AI role. Focus on these:

### Data Structures You'll Actually Use
| Structure | Where It Appears |
|-----------|-----------------|
| Dict / HashMap | `_sessions` in engine.py — O(1) session lookup by ID |
| List | `conversation[]` — ordered message history |
| Queue | If you added async job processing for LLM calls |
| Graph | LangGraph's state machine IS a directed graph |
| Min-heap | Priority queues for ranking candidates in Sarthak's copilot |

### Algorithms You Should Know
- **Binary search** — O(log n) lookup in sorted lists
- **BFS/DFS** — traversing agent graphs, dependency resolution in DBT
- **Sorting** — ranking candidates by score, sorting retrieved embeddings
- **Cosine similarity** — already covered, but know the formula

### Time Complexity That Comes Up in Interviews
- Brute-force vector search: O(n × d) where n = number of vectors, d = dimensions — this is why HNSW index matters
- Dict lookup: O(1) average
- Sorting: O(n log n)

**Don't over-prepare DSA for an AI/ML backend role.** One or two LeetCode easy/medium questions max. The real signal is system design and ML knowledge.

---

## 6. Python Specifics Used in This Project

### Async (Critical for FastAPI)
```python
# Synchronous - blocks the server while waiting
def get_data():
    result = database.query()  # blocks here
    return result

# Async - yields control while waiting, handles other requests
async def get_data():
    result = await database.query()  # non-blocking
    return result
```

The LLM calls in this project are actually **synchronous** (the Anthropic SDK's `.create()` is sync). This means each LLM call blocks the server thread. For production, you'd use the async Anthropic client or a background task queue.

### Decorators
```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

`@lru_cache` memoizes the function — it calls it once and returns the cached result every subsequent time. Used here so the `.env` file is read once, not on every request.

### Dataclasses
```python
@dataclass
class AnxietyAnalysis:
    is_anxious: bool
    confidence: float
    reasons: list[str]
```

Used in `anxiety_detector.py`. Dataclasses auto-generate `__init__`, `__repr__`, etc. They're typed, lightweight, and cleaner than plain dicts for structured return values.

### f-strings and .format()
Both used in this project:
```python
# f-string (newer, preferred)
query = f"Machine learning questions about {field}"

# .format() (used for the prompt templates)
prompt = PHASE2_PROJECT_DEEP_DIVE.format(
    project_title="My Project",
    current_depth=2,
)
```

---

## 7. Docker — What It Does and Why

Sarthak's resume lists Docker. Here's what matters:

### The Problem Docker Solves
"It works on my machine" → Docker packages the app AND its environment together, so it runs identically everywhere.

### Key Concepts
```dockerfile
FROM python:3.12-slim          # base image
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- **Image** = the recipe (Dockerfile)
- **Container** = a running instance of the image
- **Volume** = persistent storage that survives container restarts
- **docker-compose** = run multiple containers together (app + database + redis)

### For This Project
This project doesn't have a Dockerfile yet — it runs directly with `python -m uvicorn`. Adding Docker would make it deployable to AWS Lambda (like Sarthak's copilot) or any container service.

---

## 8. OS & Networking — Just the Topics

These will rarely be your primary interview topic for an AI/ML backend role, but you might get 1-2 questions. Know the concept, not the depth.

### Operating Systems — Topics to Skim
- **Process vs Thread:** A process has its own memory space. Threads share memory within a process. Python's GIL (Global Interpreter Lock) means only one thread runs Python at a time → use multiprocessing or async for CPU-bound work.
- **Deadlock:** Two processes waiting for each other forever. Understand the four conditions (mutual exclusion, hold and wait, no preemption, circular wait).
- **Virtual memory / paging:** OS gives each process the illusion of its own memory space. Not critical for your role.
- **File descriptors:** Everything in Linux is a file. Network sockets, actual files, stdin/stdout are all file descriptors. Relevant when debugging "too many open files" errors.

### Networking — Topics to Skim
- **HTTP vs HTTPS:** HTTP is plaintext, HTTPS adds TLS encryption. All production APIs use HTTPS.
- **TCP vs UDP:** TCP guarantees delivery and order (used by HTTP, databases). UDP is fire-and-forget, faster (used by video, DNS). HTTP/3 uses UDP under the hood via QUIC.
- **REST vs WebSocket:** REST is request/response (client asks, server answers). WebSocket is bidirectional, persistent connection (used for real-time chat, streaming LLM responses).
- **DNS:** Translates domain names to IP addresses. The `getaddrinfo failed` error you saw with Supabase is a DNS failure — the hostname couldn't be resolved.
- **Status codes:** 2xx success, 3xx redirect, 4xx client error, 5xx server error.
- **CORS:** Cross-Origin Resource Sharing. The backend has `CORSMiddleware` configured to allow requests from `localhost:5173` (the Vite dev server). Without CORS headers, browsers block cross-origin requests.

### One Real Interview Question You Might Get
**"What happens when you type google.com in a browser?"**

1. DNS lookup: resolve `google.com` → IP address
2. TCP connection: 3-way handshake (SYN → SYN-ACK → ACK)
3. TLS handshake: exchange certificates, agree on encryption
4. HTTP GET request sent
5. Server processes request, sends HTTP response
6. Browser renders HTML/CSS/JS

You don't need to know every detail — knowing the sequence and being able to explain DNS + TCP + TLS at a high level is enough.

---

## 9. Git — The One Tool You Must Know Cold

```bash
git init                          # start a repo
git add backend/resume/router.py  # stage specific file
git commit -m "fix: graceful Supabase degradation"
git branch feature/streaming      # create branch
git checkout feature/streaming    # switch to branch
git merge main                    # merge main into current branch
git stash                         # save uncommitted work temporarily
git log --oneline                 # see commit history
git diff HEAD~1 HEAD              # see what changed in last commit
```

**Commit message conventions (Conventional Commits):**
- `feat:` new feature
- `fix:` bug fix
- `refactor:` code restructure, no behavior change
- `docs:` documentation
- `chore:` tooling, dependencies

This project uses these conventions (see `git-workflow.md`).

---

## 10. Interview Questions Across All These Topics

### FastAPI/Backend
- "What's the difference between `async def` and `def` in FastAPI?"
- "What does Pydantic do and why is it useful?"
- "What is middleware? What does the CORS middleware in this project do?"
- "How would you add authentication to this API?"

### SQL/Data
- "What's the difference between WHERE and HAVING?"
- "Write a query to get the top 3 candidates by overall score."
- "What is a JOIN? Explain INNER vs LEFT."
- "What is an index and when would you add one?"
- "What is JSONB in Postgres? How do you query inside it?"

### Docker/Deployment
- "What is the difference between an image and a container?"
- "Why would you containerize an application?"
- "What is docker-compose used for?"

### Python
- "What is a decorator? Give an example."
- "What is the difference between a list and a generator?"
- "What does `@lru_cache` do?"
- "What is the GIL and why does it matter for concurrency?"

### OS/Networking (Light)
- "What's the difference between TCP and UDP?"
- "What is CORS and why does it exist?"
- "What happens during a DNS lookup?"
- "What does a 502 Bad Gateway error mean?" (the upstream server — e.g., Supabase — failed to respond)
