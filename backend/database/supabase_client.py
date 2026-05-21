"""
Supabase client initialisation.

Usage:
    from backend.database.supabase_client import get_supabase
    supabase = get_supabase()
"""

from functools import lru_cache

from supabase import create_client, Client

from backend.config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client.

    Prefers service-role key; falls back to anon key for development.
    """
    if not settings.SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL must be set in the .env file.")

    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    if not key:
        raise RuntimeError(
            "Either SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set."
        )
    return create_client(settings.SUPABASE_URL, key)
