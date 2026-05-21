"""Voice endpoints: TTS (ElevenLabs) + STT (Whisper) + anxiety detection."""

import base64

from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from backend.voice.stt import transcribe_audio
from backend.voice.tts import synthesize_speech as tts_synthesize
from backend.voice.anxiety_detector import analyze_anxiety

router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str


@router.post("/synthesize")
async def synthesize_speech_endpoint(body: SynthesizeRequest):
    """Convert text to speech using ElevenLabs. Returns base64 audio."""
    try:
        audio_bytes = await tts_synthesize(body.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}") from exc

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {
        "status": "ok",
        "audio_base64": audio_b64,
        "format": "mp3",
    }


@router.post("/synthesize-raw")
async def synthesize_speech_raw(body: SynthesizeRequest):
    """Convert text to speech, returning raw MP3 bytes for direct playback."""
    try:
        audio_bytes = await tts_synthesize(body.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}") from exc

    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio using Whisper + run anxiety detection."""
    audio_bytes = await file.read()

    try:
        result = await transcribe_audio(audio_bytes, filename=file.filename or "audio.webm")
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Transcription failed: {exc}"
        ) from exc

    # Run anxiety analysis
    anxiety = analyze_anxiety(
        text=result.text,
        words_per_minute=result.words_per_minute,
        duration_seconds=result.duration_seconds,
    )

    return {
        "status": "ok",
        "text": result.text,
        "duration_seconds": result.duration_seconds,
        "words_per_minute": result.words_per_minute,
        "word_count": result.word_count,
        "anxiety_detected": anxiety.is_anxious,
        "anxiety_confidence": anxiety.confidence,
        "anxiety_reasons": anxiety.reasons,
    }
