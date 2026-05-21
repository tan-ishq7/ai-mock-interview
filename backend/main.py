"""
AI Mock Interview Agent - FastAPI application entry point.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.resume.router import router as resume_router
from backend.interview.router import router as interview_router
from backend.voice.router import router as voice_router
from backend.evaluation.router import router as evaluation_router

app = FastAPI(
    title="AI Mock Interview Agent",
    version="1.0.0",
    description="Backend API for an AI-powered mock interview platform.",
)

# ---------------------------------------------------------------------------
# CORS – allow the Vite dev server during local development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(resume_router, prefix="/api/resume", tags=["Resume"])
app.include_router(interview_router, prefix="/api/interview", tags=["Interview"])
app.include_router(voice_router, prefix="/api/voice", tags=["Voice"])
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["Evaluation"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok", "service": "AI Mock Interview Agent"}
