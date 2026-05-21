"""
Text-to-Speech using ElevenLabs.

Synthesizes interviewer speech using Dr. Raj Dandekar's cloned voice.
"""

import logging

from elevenlabs import ElevenLabs

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> ElevenLabs:
    if not settings.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY must be set in the .env file.")
    return ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)


async def synthesize_speech(text: str) -> bytes:
    """Convert text to speech using ElevenLabs with the cloned voice.

    Parameters
    ----------
    text:
        The interviewer's message to synthesize.

    Returns
    -------
    Raw audio bytes (mp3 format).
    """
    client = _get_client()

    audio_generator = client.text_to_speech.convert(
        voice_id=settings.ELEVENLABS_VOICE_ID,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.7,
            "similarity_boost": 0.8,
            "style": 0.15,
            "use_speaker_boost": True,
        },
    )

    # Collect all chunks into bytes
    audio_bytes = b""
    for chunk in audio_generator:
        audio_bytes += chunk

    return audio_bytes
