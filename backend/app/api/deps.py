from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.supabase_client import get_supabase_client
from supabase import Client
from app.services.ai_integrations.interface import AIModelInterface
from app.services.ai_integrations.openai_client import OpenAIClient
from app.services.ai_integrations.perplexity_client import PerplexityClient

settings = get_settings()
security = HTTPBearer()


def get_ai_model(provider: str) -> AIModelInterface:
    """Get AI model instance based on provider name."""
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        return OpenAIClient(api_key=settings.OPENAI_API_KEY)
    elif provider == "perplexity":
        if not settings.PERPLEXITY_API_KEY:
            raise ValueError("Perplexity API key not configured")
        return PerplexityClient(api_key=settings.PERPLEXITY_API_KEY)
    else:
        raise ValueError(f"Unknown AI provider: {provider}")


async def get_ai_model_for_task(task: str) -> AIModelInterface:
    """Get AI model for a specific task based on configuration."""
    provider_mapping = {
        "refine_query": settings.AI_PROVIDER_FOR_REFINE_QUERY,
        "identify_sources": settings.AI_PROVIDER_FOR_IDENTIFY_SOURCES,
        "generate_embeddings": settings.AI_PROVIDER_FOR_GENERATE_EMBEDDINGS,
        "analyze_diff": settings.AI_PROVIDER_FOR_ANALYZE_DIFF,
    }
    
    provider = provider_mapping.get(task)
    if not provider:
        raise ValueError(f"No AI provider configured for task: {task}")
    
    return get_ai_model(provider)


class User:
    """Simple user model for authentication."""
    def __init__(self, id: str, email: str = None):
        self.id = id
        self.email = email


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> User:
    """Get current authenticated user from Supabase JWT token."""
    try:
        # Get user from Supabase using the JWT token
        auth_response = supabase.auth.get_user(credentials.credentials)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return User(id=auth_response.user.id, email=auth_response.user.email)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None


def get_supabase_with_auth(
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
) -> Client:
    """Get Supabase client with user authentication context set."""
    # Set the auth context for RLS (Row Level Security)
    # The Supabase client will automatically handle RLS based on the authenticated user
    return supabase


def get_supabase_with_optional_auth(
    current_user: Optional[User] = Depends(get_optional_current_user),
    supabase: Client = Depends(get_supabase_client)
) -> Client:
    """Get Supabase client with optional user authentication context."""
    return supabase


# Re-export commonly used dependencies
__all__ = [
    "get_current_user",
    "get_optional_current_user", 
    "get_ai_model_for_task",
    "User",
    "get_supabase_with_auth",
    "get_supabase_with_optional_auth",
    "get_supabase_client"
]