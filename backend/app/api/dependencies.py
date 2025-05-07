import logging
from fastapi import Depends, HTTPException

from app.services.ai_integrations.interface import AIModelInterface
from app.services.ai_integrations.openai_client import OpenAIClient
from app.services.ai_integrations.perplexity_client import PerplexityClient
from app.core.config import get_settings, Settings

logger = logging.getLogger(__name__)

# This file can house common dependencies, especially for AI model provisioning.

async def get_embedding_ai_model(
    s: Settings = Depends(get_settings)
) -> AIModelInterface:
    """Provides an AIModelInterface instance configured for embedding generation."""
    # Plan: OpenAI for embeddings
    if s.AI_PROVIDER_FOR_GENERATE_EMBEDDINGS and s.AI_PROVIDER_FOR_GENERATE_EMBEDDINGS.lower() == "openai":
        if not s.OPENAI_API_KEY:
            logger.critical("OpenAI API key not configured, but OpenAI is set for embeddings.")
            raise HTTPException(status_code=503, detail="Embeddings service not configured (AI provider API key missing).")
        logger.info("Using OpenAIClient for embedding generation.")
        return OpenAIClient(api_key=s.OPENAI_API_KEY)
    
    # Add other providers here if they support embeddings and are configured
    # elif s.AI_PROVIDER_FOR_GENERATE_EMBEDDINGS.lower() == "some_other_provider":
    #     # ... return SomeOtherProviderClient(...)

    logger.critical(f"No suitable AI provider configured for embedding generation. Config: {s.AI_PROVIDER_FOR_GENERATE_EMBEDDINGS}")
    raise HTTPException(status_code=503, detail="Embeddings service not configured (no suitable AI provider).")

async def get_analysis_ai_model(
    s: Settings = Depends(get_settings)
) -> AIModelInterface:
    """Provides an AIModelInterface instance configured for diff analysis."""
    # Plan: OpenAI for diff analysis
    if s.AI_PROVIDER_FOR_ANALYZE_DIFF and s.AI_PROVIDER_FOR_ANALYZE_DIFF.lower() == "openai":
        if not s.OPENAI_API_KEY:
            logger.critical("OpenAI API key not configured, but OpenAI is set for analysis.")
            raise HTTPException(status_code=503, detail="Analysis service not configured (AI provider API key missing).")
        logger.info("Using OpenAIClient for diff analysis.")
        return OpenAIClient(api_key=s.OPENAI_API_KEY)

    # Add other providers here if they support analysis and are configured

    logger.critical(f"No suitable AI provider configured for diff analysis. Config: {s.AI_PROVIDER_FOR_ANALYZE_DIFF}")
    raise HTTPException(status_code=503, detail="Analysis service not configured (no suitable AI provider).")


async def get_source_discovery_ai_model(
    s: Settings = Depends(get_settings)
) -> AIModelInterface:
    """Provides an AIModelInterface for source discovery (refine_query, identify_sources)."""
    # Plan: Perplexity for source discovery
    # This function is similar to the one in source_discovery.py, centralized here.
    if s.AI_PROVIDER_FOR_REFINE_QUERY and s.AI_PROVIDER_FOR_REFINE_QUERY.lower() == "perplexity" and \
       s.AI_PROVIDER_FOR_IDENTIFY_SOURCES and s.AI_PROVIDER_FOR_IDENTIFY_SOURCES.lower() == "perplexity":
        if not s.PERPLEXITY_API_KEY:
            logger.critical("Perplexity API key not configured, but Perplexity is set for source discovery.")
            raise HTTPException(status_code=503, detail="Source discovery service not configured (AI provider API key missing).")
        logger.info("Using PerplexityClient for source discovery.")
        # One could also pass the specific model from settings to the client constructor here
        # e.g., PerplexityClient(api_key=s.PERPLEXITY_API_KEY, model=s.PERPLEXITY_SOURCE_DISCOVERY_MODEL)
        return PerplexityClient(api_key=s.PERPLEXITY_API_KEY)
    
    # Add other provider logic if, for example, OpenAI was configured for these tasks.

    logger.critical(f"No suitable AI provider configured for source discovery. Config refine: {s.AI_PROVIDER_FOR_REFINE_QUERY}, identify: {s.AI_PROVIDER_FOR_IDENTIFY_SOURCES}")
    raise HTTPException(status_code=503, detail="Source discovery service not configured (no suitable AI provider).") 