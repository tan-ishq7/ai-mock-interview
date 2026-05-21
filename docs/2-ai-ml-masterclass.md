# AI/ML Masterclass — What a Fresher Needs to Know in 2025
> Focus: where AI is used IN THIS PROJECT, how prompts work, RAG, MCP, orchestration, transformers vs CNNs.

---

## 1. Where AI Is Used in This Project (Every Single Call)

There are **~58 LLM calls per complete interview**. Here's exactly where:

| Step | File | What the LLM Does | Input | Output |
|------|------|-------------------|-------|--------|
| Resume parse | `resume/parser.py` | Read PDF, extract structured JSON | PDF bytes + extraction prompt | JSON with name, projects, field |
| Phase 1 questions | `interview/engine.py` | Generate background questions from resume | Resume sections + conversation history | Interview question text |
| Phase 2/3 questions | `interview/engine.py` | Generate project deep-dive at current depth | Project details + depth level + history | Question text |
| Phase 4 questions | `interview/engine.py` | Ask factual ML question (without revealing answer) | Question + ground truth + history | Question framing text |
| Phase 5 questions | `interview/engine.py` | Ask behavioral question | Question text + history | Behaviorally framed question |
| Response evaluation | `interview/engine.py` | Score every candidate answer | Question + answer + ground truth | JSON with 8 fields |
| Hint generation | `interview/engine.py` | Generate a non-answer nudge | Stuck question + bad response | Hint text |
| Report narrative | `evaluation/report_generator.py` | Write full evaluation report | All scores + candidate info | Multi-section report text |

**The LLM is the brain for everything.** Logic that a traditional system would hardcode (is this answer good? should I go deeper?) is delegated to the LLM.

---

## 2. Prompt Engineering — How It Works in This Project

Prompt engineering is writing instructions to LLMs so they behave exactly how you want. This project uses four distinct patterns:

### Pattern 1: System Prompt Persona
```python
SYSTEM_PROMPT = """
You are a senior ML engineering interviewer conducting a structured technical interview.
1. Be professional, direct, and concise.
2. NEVER use superlatives: "incredible", "great answer", "amazing"...
3. Acknowledge answers neutrally: "Understood.", "Noted.", "I see."
...
"""
```
This is injected into EVERY LLM call as the `system` parameter (in Claude's API). It's like a permanent personality layer. The LLM never forgets it because it's always in the context.

**Why no superlatives?** Without this constraint, LLMs default to enthusiastic affirmation ("Great answer! Now let's move on..."). That's fine for a chatbot but breaks the neutral interviewer illusion.

### Pattern 2: Dynamic Context Injection
```python
PHASE2_PROJECT_DEEP_DIVE = """
You are in Phase 2: Primary Project Deep Dive.
Title: {project_title}
Description: {project_description}
Technologies: {project_technologies}
Current depth level: {current_depth}
Question number: {question_number} of {max_questions}.
"""
```
The `{placeholders}` are filled at runtime with the candidate's actual data. The same template produces different questions for every candidate because the project details are injected dynamically.

This is **context engineering** — constructing the context window deliberately so the LLM has exactly the information it needs and nothing it doesn't.

### Pattern 3: Structured Output (JSON)
```python
EVALUATE_RESPONSE = """
...
Provide your evaluation as a JSON object:
{
    "understanding_score": <float 0-10>,
    "should_go_deeper": <bool>,
    "anxiety_detected": <bool>,
    ...
}
Return ONLY the JSON object with no additional text.
"""
```
The LLM is instructed to return machine-readable JSON. This output drives the state machine — if `should_give_hint` is `true`, the code generates a hint. If it's `false`, the code asks the next question.

**This is the bridge between LLM reasoning and program logic.** The LLM makes a judgment call; the JSON is how that judgment is communicated to the Python code.

After the call, the code does:
```python
raw = _call_llm(...)
if raw.startswith("```"):     # strip markdown fences if model added them
    raw = "\n".join(raw.split("\n")[1:-1])
result = json.loads(raw)      # parse into Python dict
```

### Pattern 4: Conversation History as Memory
```python
messages = []
for msg in conversation:
    messages.append({"role": msg["role"], "content": msg["content"]})

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=system_prompt,
    messages=messages,          # ← full history every time
)
```
The LLM has no memory between API calls. The entire conversation is re-sent every time. This is how the interviewer "remembers" what was discussed earlier — it's reading the transcript, not remembering.

**Implication:** As the interview gets longer, each call gets more expensive (more input tokens). A 90-minute interview with 30 exchanges might have 15,000+ tokens of history by the end.

---

## 3. Context Engineering vs Prompt Engineering

These are related but distinct:

| | Prompt Engineering | Context Engineering |
|--|-------------------|---------------------|
| **What** | Writing the instructions/persona | Deciding WHAT information goes into the context window |
| **Example** | "Be neutral, use JSON output" | Including the resume but NOT the ground-truth answer in the candidate-facing call |
| **Challenge** | Getting the right tone/format | Managing what fits in the context window, what to exclude |

**In this project:**
- Phase 4 prompt includes the ground truth answer — but with explicit instruction: "DO NOT reveal this to the candidate." The LLM uses it to compare, not to share.
- The hint template includes only the stuck question and last response — not the full conversation. This focuses the hint generation without overloading it.
- The evaluation prompt doesn't include the full resume — just the current question and answer. Smaller = cheaper + faster.

---

## 4. RAG — Retrieval Augmented Generation

### The Core Problem RAG Solves
LLMs have two limitations:
1. **Knowledge cutoff** — they don't know things after training
2. **Hallucination** — they confidently make up specific facts

RAG fixes both by fetching real, up-to-date, specific information and injecting it into the prompt.

### How RAG Works (Step by Step)
```
User query: "Tell me about candidate Sarthak's background in NLP"
           ↓
1. EMBED the query
   query_vector = embedding_model.encode("NLP machine learning questions")
   # → [0.23, -0.41, 0.87, ...] (384 numbers)
           ↓
2. RETRIEVE from vector store
   results = supabase.rpc("match_ml_questions", {
       "query_embedding": query_vector,
       "match_count": 5
   })
   # Returns 5 most similar questions from the database
           ↓
3. INJECT into prompt
   prompt = f"Ask the candidate these questions:\n{retrieved_questions}"
           ↓
4. GENERATE answer
   response = llm.generate(prompt)
```

### How RAG Is Used in This Project
Phase 4 (Factual ML Questions) is a RAG pipeline:
- **Retrieval model:** `all-MiniLM-L6-v2` (384-dim sentence transformer, runs locally)
- **Vector store:** Supabase + pgvector extension
- **Query:** `f"Machine learning questions about {field}"` where field = candidate's domain
- **Retrieved:** Top 5 most semantically similar questions with ground-truth answers
- **Injection:** The question is injected into the Phase 4 prompt template

**This is lightweight RAG** — the "document" is just a question bank, not a full knowledge base. But the principle is identical to enterprise RAG over thousands of PDFs.

### RAG vs Fine-tuning
| | RAG | Fine-tuning |
|--|-----|-------------|
| **Cost** | Low (vector search is cheap) | High (GPU training) |
| **Update speed** | Instant (add to vector store) | Slow (retrain model) |
| **Knowledge type** | Factual, specific, up-to-date | Style, tone, domain adaptation |
| **Hallucination** | Reduced (grounded in retrieved docs) | Still possible |
| **When to use** | Domain-specific knowledge retrieval | Behavior/tone changes |

**For this project:** RAG is the right call. You want the interview questions to be factually accurate and updatable without retraining anything.

### Embeddings — The Math You Need to Know
An embedding converts text into a vector (list of numbers) where meaning is encoded as direction.

```
"machine learning" → [0.2, -0.4, 0.8, ...]
"deep learning"    → [0.19, -0.38, 0.75, ...]  ← similar direction
"cooking recipes"  → [-0.6, 0.3, -0.1, ...]    ← very different direction
```

**Cosine similarity:** cos(θ) = (A·B) / (|A| × |B|)
- Result of 1.0 = identical meaning
- Result of 0.0 = unrelated
- Result of -1.0 = opposite meaning

You don't need to compute this manually — `sentence-transformers` and Supabase's pgvector `<=>` operator handle it.

---

## 5. MCP — Model Context Protocol

### What It Is
MCP (Model Context Protocol, by Anthropic) is a standard for connecting LLMs to external tools and data. Think of it as a USB standard — instead of every AI app building custom integrations for every tool, MCP provides one protocol that works everywhere.

**Before MCP:**
```
App → custom code → Database
App → custom code → File system
App → custom code → API
```

**With MCP:**
```
LLM ← MCP → Database server
LLM ← MCP → File server
LLM ← MCP → API server
```

### How It Works Technically
MCP uses JSON-RPC over stdio or HTTP/SSE. An MCP server exposes "tools" — each with:
- `name`: identifier
- `description`: tells the LLM WHEN to use it (this is itself a prompt)
- `inputSchema`: what arguments it accepts
- `outputSchema`: what it returns

The LLM decides to call a tool by outputting a structured tool-call block. The MCP client executes it and returns the result.

### Why It's on Sarthak's Resume
The **Agentic AI Recruitment Copilot** uses MCP tools for automated parsing of resumes and job descriptions. This means:
- There's an MCP server that exposes a `parse_resume(pdf_bytes)` tool
- There's an MCP server that exposes a `parse_job_description(text)` tool
- The agents call these tools via MCP instead of having the LLM try to parse inline

**This is the right use of MCP:** structured, deterministic operations (parsing, formatting, DB queries) should be tools. Open-ended reasoning should be the LLM.

### Where MCP Could Be Added to THIS Project
Currently the project has no MCP integration. Opportunities:
1. **Expose the interview engine as an MCP server** — any Claude agent could trigger an interview session as a tool call
2. **Supabase as an MCP data source** — instead of calling Supabase directly, expose it as an MCP server with typed operations
3. **Resume parser as MCP tool** — the parsing function becomes a callable tool, reusable across different agent workflows

---

## 6. Orchestration — What It Means in Practice

Orchestration = coordinating multiple AI calls, tools, and state to accomplish a multi-step task.

### This Project's Orchestration Layer
The `InterviewState` + `process_candidate_response()` in `engine.py` IS the orchestrator. It:
1. Receives candidate input
2. Calls LLM evaluation tool
3. Reads the JSON result
4. Decides which action to take (hint, deeper, advance, pause)
5. Calls appropriate LLM tool (hint generator, question generator, phase transition)
6. Updates state
7. Returns structured response

This is a **reactive orchestration loop** — it reacts to each input based on current state.

### Orchestration Frameworks (What the Field Looks Like)

| Framework | Style | Best For |
|-----------|-------|----------|
| **LangGraph** (Sarthak uses) | Graph-based state machine | Complex conditional flows, cycles |
| **AutoGen** (Sarthak uses) | Multi-agent conversation | Agents talking to each other |
| **LangChain** | Linear chains | Simple sequential pipelines |
| **CrewAI** | Role-based agents | Team simulations |
| **Raw code** (this project) | Custom state machine | Full control, no framework overhead |

This project uses raw Python (no framework) — which is actually fine for a controlled, well-defined workflow. LangGraph would add value if the interview flow needed more complex conditional branching or cycles.

### Agent Loop Pattern (ReAct)
```
Reason → Act → Observe → Reason → Act → Observe → ...
```

This is what the evaluation-then-question loop in this project implements manually:
- **Reason:** LLM evaluates response (internal reasoning)
- **Act:** Choose next action (hint / deeper / advance)
- **Observe:** Candidate responds
- Repeat

---

## 7. Transformers vs CNNs — What to Know in 2025

### CNNs (Convolutional Neural Networks)
- Designed for **spatial data** (images, audio spectrograms)
- Apply learned filters over local regions (convolution)
- Built-in translation invariance — a cat in the corner = a cat in the center
- Still heavily used for: image classification, object detection, image segmentation, medical imaging
- **NOT old news for vision** — CNNs are still SOTA for many vision tasks, especially on edge devices

**Sarthak's IEEE paper used CNNs for plant disease detection.** This is a classic, correct application.

**Know this:** ResNet, VGG, EfficientNet are CNN architectures. Transfer learning on pretrained CNNs is the standard approach for computer vision problems with limited data.

### Transformers
- Originally designed for **sequential data** (text), now used for almost everything
- The core mechanism: **self-attention** — every token looks at every other token to determine what to focus on
- Not built into transformers: no local bias, no translation invariance → need more data and compute than CNNs for small vision tasks
- Modern vision: **ViT (Vision Transformer)** treats image patches like tokens, outperforms CNNs on large datasets
- For text: BERT (encoder), GPT (decoder), T5 (encoder-decoder)

### The Attention Mechanism (Intuition, Not Math)
Imagine reading the sentence: "The animal didn't cross the street because it was too tired."

What does "it" refer to? You need to look at other words in the sentence to figure out it's the animal, not the street. Self-attention does exactly this — for each word, it computes a weighted relevance score against every other word and uses those weights to build a richer representation.

```
Q (query): what am I looking for?
K (key):   what do I offer to queries?
V (value): what information do I carry?

Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) × V
```

The `/sqrt(d_k)` scaling prevents the dot products from getting too large in high dimensions (which would kill the softmax gradients).

### When to Use What
| Task | Use |
|------|-----|
| Image classification (limited data) | CNN with transfer learning |
| Image classification (large data) | ViT or hybrid |
| Object detection | CNN-based (YOLO, Faster-RCNN) |
| NLP (understanding) | BERT-family |
| NLP (generation) | GPT-family / Claude / Gemini |
| Time series | Transformers or LSTM |
| Resume parsing in this project | LLM (Claude/Gemini = transformer) |

### Why Not CNN for This Project?
Resume parsing needs language understanding — semantic meaning of text. CNNs work on local spatial patterns (edges, textures in images). They don't capture the meaning of "5 years of Python experience." Transformers (LLMs) are the right tool.

---

## 8. Data Warehousing — Why It Matters for AI

### What It Is
A data warehouse is a centralized store optimized for **analytical queries** (not transactional writes). Instead of querying your production database for reports (which is slow and dangerous), you move data to a warehouse where it can be aggregated, joined, and analyzed freely.

### Relevance to This Project
Sarthak's **Business Travel AI Copilot** uses:
- **Airflow** — schedules ETL pipelines (Extract, Transform, Load data into warehouse)
- **DBT** (Data Build Tool) — transforms raw warehouse data into clean, query-ready tables via SQL
- **Tableau** — visualizes warehouse data
- **SQL Agent** — lets the LLM query the warehouse in natural language

This is a real modern data stack. The LLM doesn't replace SQL — it generates SQL. The warehouse runs the SQL.

### OLTP vs OLAP
| | OLTP (Transactional) | OLAP (Analytical) |
|--|---------------------|-------------------|
| Example | Supabase in this project | Data warehouse |
| Optimized for | Many small reads/writes | Few large aggregate queries |
| Schema | Normalized (no redundancy) | Denormalized (star/snowflake schema) |
| Query type | `SELECT * WHERE id = ?` | `GROUP BY, JOIN, WINDOW functions` |
| Tools | Postgres, MySQL | BigQuery, Snowflake, Redshift |

### SQL Is Not Optional
Even in an AI-first world, SQL is critical because:
1. **LLMs generate SQL** — if you can't read it, you can't verify it
2. **Vector databases are built on SQL databases** (pgvector is Postgres)
3. **DBT models are SQL** — the standard for data transformation
4. **Evaluation and scoring data** is inherently relational

Know: SELECT, JOIN (INNER, LEFT, RIGHT), GROUP BY, WHERE, subqueries, window functions (ROW_NUMBER, RANK, LAG, LEAD), aggregates (COUNT, SUM, AVG). Know the difference between WHERE and HAVING.

---

## 9. MLOps — Deploying ML in the Real World

Sarthak's resume lists MLOps, Kubernetes, CI/CD. Here's what matters:

### The ML Lifecycle
```
Data Collection → Feature Engineering → Training → Evaluation → Deployment → Monitoring → Retrain
```

### Key MLOps Concepts
- **Model versioning:** Track which model version produced which predictions (MLflow, Weights & Biases)
- **Feature store:** Centralized place to define and serve features consistently between training and inference
- **Model drift:** Production data distribution changes over time → model accuracy degrades → trigger retrain
- **A/B testing:** Run two model versions simultaneously, measure which performs better in production
- **Containerization (Docker):** Package model + dependencies into a container so it runs identically everywhere
- **Orchestration (Kubernetes):** Manage many containers at scale — auto-scaling, health checks, rolling deploys

### How This Project Relates
This project IS a deployment — FastAPI + Uvicorn serves the model. What's missing for production MLOps:
- No model versioning (which version of Claude prompt is running?)
- No monitoring (are evaluation scores drifting? Are users getting stuck more in phase 3?)
- No A/B testing (which prompt template produces better interview quality?)

These are real gaps you can mention in an interview as "what I'd add next."
