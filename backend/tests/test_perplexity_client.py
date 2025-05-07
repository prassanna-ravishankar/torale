import pytest
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.ai_integrations.perplexity_client import (
    PerplexityClient, 
    PERPLEXITY_API_URL,
    SYSTEM_PROMPT_REFINE_QUERY,
    SYSTEM_PROMPT_IDENTIFY_SOURCES
)
from app.core.config import Settings

# Fixture for settings, potentially overridden for tests
@pytest.fixture
def test_settings():
    # Provide minimal settings needed for the client
    return Settings(PERPLEXITY_API_KEY="test_pplx_key") 

@pytest.fixture
def perplexity_client(test_settings): 
    return PerplexityClient(api_key=test_settings.PERPLEXITY_API_KEY)

# --- Helper for Mocking aiohttp responses ---
def _get_mock_aiohttp_session_cm(status_code, json_payload, raise_for_status_effect=None):
    # 1. The actual response object
    mock_response_obj = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response_obj.status = status_code
    mock_response_obj.json = AsyncMock(return_value=json_payload)
    if raise_for_status_effect:
        mock_response_obj.raise_for_status = MagicMock(side_effect=raise_for_status_effect)
    else:
        mock_response_obj.raise_for_status = MagicMock() # Does nothing by default

    # 2. The context manager for the response object (returned by session.post())
    #    In aiohttp, session.post() is awaitable and directly returns the response object,
    #    not a context manager for the response.
    #    So session.post() should directly return mock_response_obj.

    # 3. The session instance (returned by ClientSession context manager's __aenter__)
    mock_session_instance = AsyncMock(spec=aiohttp.ClientSession)
    # session.post is an async method that returns the response object
    mock_session_instance.post = AsyncMock(return_value=mock_response_obj)

    # 4. The ClientSession context manager itself (returned by aiohttp.ClientSession())
    mock_session_cm_constructor_return = AsyncMock()
    mock_session_cm_constructor_return.__aenter__.return_value = mock_session_instance
    # __aexit__ should also be an AsyncMock if it's awaited or does async operations
    mock_session_cm_constructor_return.__aexit__ = AsyncMock(return_value=None)
    
    return mock_session_cm_constructor_return, mock_session_instance # Return instance for assertions

# --- Tests for refine_query ---

@pytest.mark.asyncio
async def test_refine_query_success(perplexity_client):
    raw_query = "test query"
    expected_refined = "refined test query"
    mock_response_payload = {
        "choices": [{"message": {"content": expected_refined}}]
    }
    
    mock_session_cm, mock_session_instance = _get_mock_aiohttp_session_cm(200, mock_response_payload)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        refined_query = await perplexity_client.refine_query(raw_query)
        
    assert refined_query == expected_refined
    mock_session_instance.post.assert_called_once()
    call_args, call_kwargs = mock_session_instance.post.call_args
    assert call_args[0] == PERPLEXITY_API_URL
    assert call_kwargs["json"]["messages"][0]["content"] == SYSTEM_PROMPT_REFINE_QUERY
    assert call_kwargs["json"]["messages"][1]["content"] == raw_query

@pytest.mark.asyncio
async def test_refine_query_api_error(perplexity_client):
    raw_query = "test query"
    error_effect = aiohttp.ClientResponseError(MagicMock(), ())
    mock_session_cm, _ = _get_mock_aiohttp_session_cm(500, {}, raise_for_status_effect=error_effect)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        with pytest.raises(ConnectionError, match="Failed to connect to Perplexity API"):
            await perplexity_client.refine_query(raw_query)

@pytest.mark.asyncio
async def test_refine_query_bad_response_structure(perplexity_client):
    raw_query = "test query"
    mock_response_payload = {"invalid": "structure"}
    mock_session_cm, _ = _get_mock_aiohttp_session_cm(200, mock_response_payload)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        with pytest.raises(ValueError, match="Invalid response structure from Perplexity API for refine_query"):
            await perplexity_client.refine_query(raw_query)

# --- Tests for identify_sources ---

@pytest.mark.asyncio
async def test_identify_sources_success(perplexity_client):
    refined_query = "refined query"
    api_response_content = "https://example.com/source1\nhttps://example.com/source2"
    expected_urls = ["https://example.com/source1", "https://example.com/source2"]
    mock_response_payload = {
        "choices": [{"message": {"content": api_response_content}}]
    }
    mock_session_cm, mock_session_instance = _get_mock_aiohttp_session_cm(200, mock_response_payload)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        identified_urls = await perplexity_client.identify_sources(refined_query)
        
    assert identified_urls == expected_urls
    mock_session_instance.post.assert_called_once()
    call_args, call_kwargs = mock_session_instance.post.call_args
    assert call_kwargs["json"]["messages"][0]["content"] == SYSTEM_PROMPT_IDENTIFY_SOURCES
    assert call_kwargs["json"]["messages"][1]["content"] == refined_query

@pytest.mark.asyncio
async def test_identify_sources_empty_response(perplexity_client):
    refined_query = "query with no results"
    api_response_content = " "
    mock_response_payload = {
        "choices": [{"message": {"content": api_response_content}}]
    }
    mock_session_cm, _ = _get_mock_aiohttp_session_cm(200, mock_response_payload)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        identified_urls = await perplexity_client.identify_sources(refined_query)
        
    assert identified_urls == []

# --- Tests for unimplemented methods ---

@pytest.mark.asyncio
async def test_generate_embeddings_not_implemented(perplexity_client):
    with pytest.raises(NotImplementedError):
        await perplexity_client.generate_embeddings(["test"])

@pytest.mark.asyncio
async def test_analyze_diff_not_implemented(perplexity_client):
    with pytest.raises(NotImplementedError):
        await perplexity_client.analyze_diff("old", "new") 