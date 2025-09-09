from supabase import Client, create_client

from torale.core.config import settings


def get_supabase_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key or settings.supabase_anon_key,
    )