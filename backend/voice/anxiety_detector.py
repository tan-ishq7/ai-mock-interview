"""
Voice-based anxiety detection.

Analyzes speech patterns to detect candidate anxiety:
- Speech rate (words per minute) — too fast indicates nervousness
- Filler words / stuttering — excessive "um", "uh", repeated words
- Very short responses — may indicate being stuck or stressed
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Thresholds for anxiety detection
FAST_SPEECH_WPM = 180  # above this = speaking too fast
SLOW_SPEECH_WPM = 60   # below this = hesitant / stuck
FILLER_WORD_RATIO_THRESHOLD = 0.12  # more than 12% filler words = anxious
MIN_RESPONSE_WORDS = 5  # fewer words = possibly stuck

FILLER_WORDS = {
    "um", "uh", "er", "ah", "like", "you know", "basically",
    "actually", "sort of", "kind of", "i mean", "well",
}

# Pattern for detecting word repetitions (stuttering): "the the", "I I I"
STUTTER_PATTERN = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


@dataclass
class AnxietyAnalysis:
    is_anxious: bool
    confidence: float  # 0.0 to 1.0
    reasons: list[str]
    speech_rate_wpm: float
    filler_ratio: float
    stutter_count: int


def analyze_anxiety(
    text: str,
    words_per_minute: float,
    duration_seconds: float,
) -> AnxietyAnalysis:
    """Analyze transcribed text and speech metrics for anxiety signals.

    Parameters
    ----------
    text:
        Transcribed candidate response.
    words_per_minute:
        Measured speech rate from Whisper.
    duration_seconds:
        Total duration of the audio clip.

    Returns
    -------
    AnxietyAnalysis with detection result and supporting evidence.
    """
    reasons: list[str] = []
    anxiety_score = 0.0
    words = text.lower().split()
    word_count = len(words)

    # 1. Speech rate check
    if words_per_minute > FAST_SPEECH_WPM:
        reasons.append(f"Speaking very fast ({words_per_minute:.0f} WPM)")
        anxiety_score += 0.35
    elif words_per_minute < SLOW_SPEECH_WPM and duration_seconds > 3:
        reasons.append(f"Speaking very slowly/hesitantly ({words_per_minute:.0f} WPM)")
        anxiety_score += 0.2

    # 2. Filler word analysis
    filler_count = 0
    for filler in FILLER_WORDS:
        filler_parts = filler.split()
        if len(filler_parts) == 1:
            filler_count += words.count(filler)
        else:
            # Multi-word fillers
            text_lower = text.lower()
            filler_count += text_lower.count(filler)

    filler_ratio = filler_count / max(word_count, 1)
    if filler_ratio > FILLER_WORD_RATIO_THRESHOLD:
        reasons.append(
            f"High filler word usage ({filler_ratio:.0%} of words)"
        )
        anxiety_score += 0.3

    # 3. Stuttering / word repetition
    stutter_matches = STUTTER_PATTERN.findall(text)
    stutter_count = len(stutter_matches)
    if stutter_count >= 2:
        reasons.append(f"Word repetitions detected ({stutter_count} instances)")
        anxiety_score += 0.25

    # 4. Very short response
    if word_count < MIN_RESPONSE_WORDS and duration_seconds > 2:
        reasons.append(
            f"Very short response ({word_count} words) — may be stuck"
        )
        anxiety_score += 0.15

    # Cap at 1.0
    anxiety_score = min(anxiety_score, 1.0)
    is_anxious = anxiety_score >= 0.45

    return AnxietyAnalysis(
        is_anxious=is_anxious,
        confidence=anxiety_score,
        reasons=reasons,
        speech_rate_wpm=words_per_minute,
        filler_ratio=filler_ratio,
        stutter_count=stutter_count,
    )
