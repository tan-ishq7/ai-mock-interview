# Answer Sheet 3 — Strong Candidate (Depth 4-5, Score 80%+)
> "I know this project inside out and I know ML theory well."
> This level pushes the interviewer to depth 4-5, scores 8-9/10 on factual, and targets 80%+ overall.
> Use this if you're presenting the AI Mock Interview project itself as your own project.

---

## Special Section: Presenting THIS Project (the AI Mock Interview App)

If a fresher is presenting this project in an interview, here's exactly what to say at each depth.

### Depth 1 — What it is
"This is a multi-modal AI mock interview system. It takes a candidate's PDF resume, parses it using a vision-capable LLM to extract structured data, then conducts a five-phase structured interview. The system handles both text and voice — the interviewer's questions are synthesized to audio via ElevenLabs TTS, and candidate speech is transcribed via Whisper STT. It also does real-time anxiety detection from voice patterns and LLM text analysis. The backend is FastAPI, data is stored in Supabase Postgres, and the LLM layer supports Claude, Gemini, and OpenAI interchangeably."

### Depth 2 — Technical Decisions
"The key architectural decision was the provider abstraction layer — a single `_call_llm()` function that dispatches to Claude, Gemini, or OpenAI based on an env variable. This lets us swap models without changing business logic. The interview engine uses a 5-phase state machine stored in memory per session — which is simple and fast but means session state is lost on restart. For production we'd replace that with Redis.

The resume parser uses LLM-native PDF parsing: with Claude it uses the `document` content block type which sends the PDF bytes directly; with Gemini it uses `inline_data` with base64. No PDF-to-text preprocessing needed — the model reads the document natively.

For question retrieval in Phase 4, we use a sentence-transformer model (all-MiniLM-L6-v2) to embed the candidate's field and do cosine similarity search against a Supabase vector store using pgvector. This is a lightweight RAG pattern."

### Depth 3 — Implementation Details
"The evaluation system is the most interesting part technically. After every response, the engine makes an additional LLM call to evaluate the response — returning JSON with scores for understanding, completeness, accuracy, and communication, plus boolean flags: `should_go_deeper`, `should_give_hint`, `anxiety_detected`. The Socratic drill (Phase 2/3) is driven entirely by these flags: good answer → increment depth, bad answer → generate hint, stuck → anxiety break.

The anxiety detection is dual-signal: the LLM evaluation sets `anxiety_detected` based on language analysis (hedging, explicit uncertainty), and separately the STT pipeline runs a rule-based detector on speech metrics — WPM, filler word ratio (threshold 12%), word repetitions via regex, response length. Both signals independently can trigger a pause message.

The prompt architecture uses a layered system: a fixed `SYSTEM_PROMPT` persona (professional, no superlatives, neutral tone), plus a phase-specific template injected with runtime data (resume, project, depth level, question number). This keeps the interviewer persona consistent across all LLM calls."

### Depth 4 — Failure Modes & What I'd Fix
"Three main failure modes. First, the session state is entirely in-memory — if the server restarts mid-interview, all state is lost. Fix: serialize `InterviewState` to Redis with TTL.

Second, the evaluation LLM call after every response doubles latency — each candidate message triggers two LLM round-trips (evaluation + next question). Fix: either run evaluation async in the background or merge the evaluation and next-question prompts into one call.

Third, the factual knowledge base (Phase 4) depends on Supabase being alive. When Supabase is down, Phase 4 silently gets zero questions and immediately advances to Phase 5. This means candidates don't get ML knowledge assessed if the DB is unavailable. Fix: bundle a fallback question set in the codebase.

For the resume upload, I added a graceful degradation — if Supabase is unreachable, we generate a local UUID and continue. The data isn't persisted but the parsing pipeline still works."

### Depth 5 — Theory / Extensions
"The core LLM interaction pattern here is multi-turn, system-prompted conversation. The system prompt acts as a persistent persona instruction — in Claude's API, this is passed as the `system` parameter, separate from the message array. The conversation array maintains full dialogue history, which means the interviewer has full context of the interview so far.

The Russian Doll methodology (depth 1→5) is essentially a scaffolded Socratic dialogue — the system operationalizes the philosophical Socratic method into discrete depth levels with explicit advancement conditions. Academically, this maps to Bloom's taxonomy: depth 1 is recall/understanding, depth 3 is application, depth 5 is synthesis/evaluation.

Extensions I'd add: (1) Multi-modal output — instead of just TTS, generate visual aids or diagrams when explaining technical concepts. (2) MCP integration — expose the interview engine as an MCP server so external Claude instances can orchestrate interviews as a tool. (3) Streaming responses — the current API uses non-streaming LLM calls; adding `stream=True` to Claude/Gemini calls would cut perceived latency significantly for long responses. (4) Embedding-based session memory — rather than passing full conversation history each call, compress older context into a memory embedding to handle long interviews within context window limits."

---

## Phase 4 — Factual ML (Expert Level)

**Explain attention mechanisms from first principles.**
"The core idea is computing a soft, differentiable lookup: for each query vector q, compute compatibility with all key vectors K as scores = q·K^T / sqrt(d_k). The sqrt scaling prevents dot products from growing large in high dimensions, which would push softmax into saturation and kill gradients. Applying softmax gives attention weights, which are used to form a weighted sum of value vectors V. The result is a context-aware representation of q that selectively incorporates information from the sequence. Multi-head attention runs h parallel attention functions with different learned W_Q, W_K, W_V projections, then concatenates and projects the results — letting each head specialize in different relationship types."

**What is the difference between batch norm and layer norm? When do you use each?**
"Batch norm normalizes across the batch dimension — for each feature, compute mean and variance across all samples in the batch. This makes statistics data-dependent, which creates issues: different behavior at train vs. inference (need running statistics), and instability with small batches. Layer norm normalizes across the feature dimension for each sample independently — no batch dependency. For transformers, layer norm is preferred because: (1) sequence lengths vary, making batch statistics unstable; (2) autoregressive inference processes one token at a time, making batch size effectively 1. For CNNs processing images in large batches, batch norm often works better because the batch provides stable statistics."

**What is RLHF and why is it used for LLMs?**
"Reinforcement Learning from Human Feedback is a fine-tuning technique that trains a reward model on human preference data, then uses that reward model to fine-tune the base LLM via PPO (Proximal Policy Optimization). The motivation: you can't write a loss function that captures 'this response is helpful, harmless, and honest' — it's too nuanced. But humans can easily rank two responses. RLHF converts those rankings into a reward signal. The base LLM's log-probability of the original SFT model is used as a KL penalty to prevent the policy from drifting too far and degenerating. Claude uses Constitutional AI as an extension — the model uses a written constitution to self-critique and revise responses before the RL stage."

**What is RAG and what problem does it solve?**
"RAG — Retrieval Augmented Generation — addresses two LLM limitations: knowledge cutoff and hallucination on domain-specific facts. Instead of relying purely on what's encoded in weights, RAG retrieves relevant context from an external store at inference time and conditions generation on it. The pipeline: encode the query using an embedding model → retrieve the k most similar document chunks via vector similarity → inject retrieved text into the prompt → generate. The key design choices are: chunking strategy, embedding model quality, retrieval metric (cosine vs. dot product), and how to rerank retrieved results. In this project, Phase 4 uses a lightweight version: the candidate's field name is embedded, matched against a question bank, and the matching questions are retrieved to ask in the interview."

---

## Phase 5 — Behavioral (Strong Candidate)

### Where do you see yourself in five years?
"I want to be in a role where I'm making technical decisions that affect how ML systems are designed and operated — not just implementing them. The work I find most interesting is at the boundary between ML research and engineering: taking a research result and figuring out how to make it reliable, fast, and maintainable in production. In five years, I'd want to have shipped multiple systems where I can point to the production metrics and say I own that. If that leads toward a staff or tech lead path, great — but the driver is the quality of the technical problem, not the title."

### Most important challenge?
"The hardest thing I've dealt with was debugging a training instability that only appeared at larger batch sizes. The loss would diverge after about 3 epochs when training with batch size 128, but was stable at 32. After two days of investigation, the root cause was a learning rate that wasn't scaling with batch size — following the linear scaling rule (multiply LR by k when multiplying batch size by k) fixed it. The lesson was that hyperparameters don't transfer between training configurations — you need to reason about what each hyperparameter is actually controlling."

### Team dynamics?
"I'm most effective when I own a component end-to-end with a clear interface to the rest of the team. I've found that ambiguity about ownership is the main source of friction in technical teams — either two people build the same thing, or nobody does. In the mock interview project, I deliberately structured it as a set of independent modules with typed interfaces between them: the parser returns a typed dict, the engine consumes it, the router wraps both. That let different parts be worked on or replaced without ripple effects. I think good system design and good team coordination are the same thing at different scales."

### Questions for the interviewer?
"Three things I'm genuinely curious about. One: in the project deep-dive, what's your read on depth 4 versus depth 5 answers — is reaching depth 5 expected, or is it more of a signal you use to differentiate top candidates from strong ones? Two: where does this system's evaluation most diverge from how a human interviewer would assess the same candidate? I'm curious where the LLM-based evaluation has blind spots. Three: what's the one thing you'd change about this system if you had two weeks?"
