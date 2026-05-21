"""
Application configuration loaded from environment variables.

Expects a .env file in the project root (one directory above backend/).
"""

from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Load .env into os.environ BEFORE pydantic-settings reads them.
# This avoids a pydantic-settings bug where certain keys (e.g. ANTHROPIC_API_KEY)
# are silently dropped when loaded via env_file.
load_dotenv(_ENV_FILE, override=True)


class Settings(BaseSettings):
    """Central configuration sourced from environment / .env file."""

    # --- OpenAI (commented out — uncomment when you have credits) --------
    OPENAI_API_KEY: str = ""

    # --- Gemini ------------------------------------------------------------
    GEMINI_API_KEY: str = ""

    # --- Claude / Anthropic (active provider) ------------------------------
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "claude"  # "claude", "gemini", or "openai"

    # --- ElevenLabs -----------------------------------------------------
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "lZORFNDokoBmfd0S06vf"

    # --- Supabase -------------------------------------------------------
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()


settings: Settings = get_settings()
