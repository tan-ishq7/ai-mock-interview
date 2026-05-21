# Feedback v1 — First User Feedback After Launch

**Date:** 2026-05-16
**Session context:** First time using the app after it was built

## What Worked
- Server starts and runs after Supabase fix
- Resume parsing pipeline (Claude or Gemini) is functional
- Docs page (/docs) loads

## Issues Reported

### 1. Supabase DNS Failure → 500 on Resume Upload
- Error: `getaddrinfo failed` — Supabase project was paused (free tier 7-day inactivity)
- Fix applied: Resume upload now degrades gracefully — generates local UUID, continues without storage
- User question: Does restore = recreate tables? Answer: NO. Just click Restore in dashboard. Schema and data preserved.

### 2. Difficulty Level Too High for Self-Demo
- The LLM evaluates responses strictly and fires `should_give_hint` and `anxiety_detected` frequently
- User knows their own resume loosely → gets paused at almost every question
- Requested: sample answer sheets (3 levels) to understand what answer quality passes each phase

### 3. Answers Not Being Saved (User Not Aware)
- Answers are stored in-memory in `InterviewState` during session
- With Supabase broken, report data is NOT persisted to database
- User was not aware of this — needs to be clearly surfaced in the UI or API response

## Requests Made This Session
- [x] Fix Supabase 500 error (done)
- [ ] 3 sample answer sheets
- [ ] Cheatsheet for fresher presenting this project
- [ ] Cost/model/API breakdown
- [ ] Supabase restore instructions

## Tone Notes
- User is comfortable with raw/direct communication
- Doesn't need formal language — conversational is fine
- Wants to understand the project deeply, not just use it
