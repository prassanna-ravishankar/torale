from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()

# Create Supabase client using URL and service key
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)

def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return supabase 