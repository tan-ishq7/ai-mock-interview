# Ideas v1 — Raw Dump from User (First Post-Build Session)

> These are unfiltered ideas, wants, and directions expressed by the user. Treat as backlog.

## UX / Difficulty
- Difficulty level felt too high for someone who knows their resume only loosely
- Want the difficulty to stay high BUT add scaffolding so answers can be prepared
- Anxiety breaks are firing too often — likely because of short/hedging answers on topics user didn't know deeply

## Answer Sheet Feature
- 3 sample answer sheets showing: what answers are "accepted" and graded well
- Show the minimum bar to pass each phase without triggering hints or anxiety breaks
- Fresher presenting project should know EXACTLY what level of answer is expected

## Project Handoff / Fresher Prep
- If a fresher presents this project in their own interview, what will they face?
- Questions about: why each API key, what each model does, cost estimates
- Heavy AI/ML focus: RAG, MCP, orchestration, multi-modal (text + audio), fundamentals
- People right now are very interested in multi-modal — this project has text + audio = strong talking point

## Data / Persistence
- User is not sure if their answers are being saved (they are NOT persistently — in-memory only, Supabase broken)
- Supabase was paused (free tier 7-day inactivity pause) — user wants to know if restore = tables recreation or not

## Content Ideas
- Multiple cheatsheets, PRDs, whatever is useful — not limited to one doc
- Keep ideas-v1, v2, v3... and feedback-v1, v2, v3... as running logs

## MCP / RAG / Orchestration Opportunities
- RAG is already partially here (vector search in question_retriever.py with all-MiniLM-L6-v2)
- Orchestration is the 5-phase engine — worth calling out explicitly
- MCP: not yet integrated — opportunity for tool-use / function calling layer
- Multi-modal is a strong differentiator: voice (ElevenLabs TTS, Whisper STT) + LLM text

## Monetization / Cost Awareness
- User wants to know what this costs to run per interview
- Claude Sonnet 4 + ElevenLabs are the main cost drivers
