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

    voice_id = settings.ELEVENLABS_VOICE_ID
    try:
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
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
        audio_bytes = b""
        for chunk in audio_generator:
            audio_bytes += chunk
        return audio_bytes
    except Exception as exc:
        logger.warning("Primary voice %s failed (%s), attempting fallback voice...", voice_id, exc)
        try:
            voices = client.voices.get_all().voices
            if voices:
                fallback_voice_id = voices[0].voice_id
                audio_generator = client.text_to_speech.convert(
                    voice_id=fallback_voice_id,
                    text=text,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128",
                )
                audio_bytes = b""
                for chunk in audio_generator:
                    audio_bytes += chunk
                return audio_bytes
        except Exception:
            pass
        raise exc
