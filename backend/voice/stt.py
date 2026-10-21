"""
Speech-to-Text using OpenAI Whisper.

Transcribes candidate audio and returns text + speech metadata
for anxiety detection.
"""

import io
import logging
from dataclasses import dataclass

from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    duration_seconds: float
    word_count: int
    words_per_minute: float


def _get_openai_client():
    if settings.GROQ_API_KEY:
        return OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        ), "whisper-large-v3-turbo"
    if settings.OPENAI_API_KEY:
        return OpenAI(api_key=settings.OPENAI_API_KEY), "whisper-1"
    return None, None


async def _transcribe_with_gemini(audio_bytes: bytes, filename: str) -> str:
    """Fallback transcription using Google Gemini 2.0 Flash."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    mime = "audio/webm"
    if filename.endswith(".mp3"):
        mime = "audio/mp3"
    elif filename.endswith(".wav"):
        mime = "audio/wav"
    elif filename.endswith(".m4a") or filename.endswith(".mp4"):
        mime = "audio/mp4"

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime),
            (
                "You are a speech-to-text transcriber. Transcribe the audio verbatim. "
                "Output ONLY the transcribed spoken text. Do not add explanations, conversational remarks, or markdown."
            ),
        ],
    )
    return (response.text or "").strip()


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> TranscriptionResult:
    """Transcribe audio using Groq, OpenAI Whisper, or Gemini.

    Parameters
    ----------
    audio_bytes:
        Raw audio file bytes (webm, mp3, wav, etc.)
    filename:
        Original filename with extension for format detection.

    Returns
    -------
    TranscriptionResult with text and speech rate metrics.
    """
    client, model_name = _get_openai_client()

    if client and model_name:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        try:
            response = client.audio.transcriptions.create(
                model=model_name,
                file=audio_file,
                response_format="verbose_json",
            )
            text = response.text.strip()
            duration = float(getattr(response, "duration", 0.0) or 5.0)
        except Exception as exc:
            logger.warning("Whisper transcription failed (%s), attempting Gemini...", exc)
            if settings.GEMINI_API_KEY:
                text = await _transcribe_with_gemini(audio_bytes, filename)
                duration = 5.0
            else:
                raise exc
    elif settings.GEMINI_API_KEY:
        text = await _transcribe_with_gemini(audio_bytes, filename)
        duration = 5.0
    else:
        raise ValueError(
            "No voice transcription API key found. Please add GEMINI_API_KEY (free), "
            "GROQ_API_KEY (free), or OPENAI_API_KEY to your Render Environment Variables."
        )

    words = text.split()
    word_count = len(words)
    wpm = (word_count / duration * 60) if duration > 0 else 0.0

    return TranscriptionResult(
        text=text,
        duration_seconds=duration,
        word_count=word_count,
        words_per_minute=wpm,
    )
