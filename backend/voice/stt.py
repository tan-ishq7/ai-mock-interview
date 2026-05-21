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


def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> TranscriptionResult:
    """Transcribe audio using Whisper and compute speech metrics.

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
    client = _get_client()

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    # Use verbose_json to get timing information
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    text = response.text.strip()
    words = text.split()
    word_count = len(words)

    # Calculate duration from word timestamps
    duration = 0.0
    if hasattr(response, "duration") and response.duration:
        duration = float(response.duration)
    elif hasattr(response, "words") and response.words:
        last_word = response.words[-1]
        duration = float(last_word.get("end", 0))

    # Words per minute
    wpm = (word_count / duration * 60) if duration > 0 else 0.0

    return TranscriptionResult(
        text=text,
        duration_seconds=duration,
        word_count=word_count,
        words_per_minute=wpm,
    )
