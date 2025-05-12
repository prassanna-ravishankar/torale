import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
import os
import json

from app.services.ai_integrations.openai_client import (
    OpenAIClient, DEFAULT_EMBEDDING_MODEL, DEFAULT_CHAT_MODEL, 
    OPENAI_API_URL_EMBEDDINGS, OPENAI_API_URL_CHAT_COMPLETIONS
)
from app.core.config import Settings

@pytest.fixture
def mock_settings_openai(): # Renamed to avoid conflict if conftest has similar
    with patch('app.services.ai_integrations.openai_client.settings') as mock_settings_obj:
        mock_settings_obj.OPENAI_API_KEY = "test_openai_key"
        yield mock_settings_obj

@pytest.mark.asyncio
async def test_openai_client_init_success(mock_settings_openai):
    client = OpenAIClient(api_key="explicit_test_key")
    assert client.api_key == "explicit_test_key"
    assert client.model_name == "openai"
    assert client.headers["Authorization"] == "Bearer explicit_test_key"

@pytest.mark.asyncio
async def test_openai_client_init_no_key(mock_settings_openai):
    mock_settings_openai.OPENAI_API_KEY = None
    with pytest.raises(ValueError, match="OpenAI API key is required"):
        OpenAIClient(api_key=None)

@pytest.mark.asyncio
@patch('app.services.ai_integrations.openai_client.OpenAIClient._make_openai_request')
async def test_generate_embeddings_success(mock_make_request, mock_settings_openai):
    client = OpenAIClient(api_key="test_key_for_embeddings")
    texts = ["text 1", "text 2"]
    expected_embeddings = [[0.1, 0.2], [0.3, 0.4]]
    mock_response_data = {
        "data": [
            {"embedding": expected_embeddings[0], "index": 0, "object": "embedding"},
            {"embedding": expected_embeddings[1], "index": 1, "object": "embedding"}
        ],
        "model": DEFAULT_EMBEDDING_MODEL,
        "object": "list", "usage": {"prompt_tokens": 0, "total_tokens": 0}
    }
    mock_make_request.return_value = mock_response_data

    embeddings = await client.generate_embeddings(texts)
    assert embeddings == expected_embeddings
    mock_make_request.assert_called_once()
    args, kwargs = mock_make_request.call_args
    assert args[0] == OPENAI_API_URL_EMBEDDINGS
    assert args[1]["input"] == texts

@pytest.mark.asyncio
@patch('app.services.ai_integrations.openai_client.OpenAIClient._make_openai_request')
async def test_generate_embeddings_api_error(mock_make_request, mock_settings_openai):
    client = OpenAIClient(api_key="test_key_for_emb_error")
    texts = ["error text"]
    mock_make_request.side_effect = ConnectionError("Simulated API error")

    with pytest.raises(ConnectionError, match="Simulated API error"):
        await client.generate_embeddings(texts)

@pytest.mark.asyncio
@patch('app.services.ai_integrations.openai_client.OpenAIClient._make_openai_request')
async def test_generate_embeddings_malformed_response(mock_make_request, mock_settings_openai):
    client = OpenAIClient(api_key="test_key_for_emb_malformed")
    texts = ["bad response text"]
    mock_make_request.return_value = {"invalid": "structure"} # Malformed

    with pytest.raises(ValueError, match="Invalid response structure from OpenAI API for generate_embeddings"):
        await client.generate_embeddings(texts)

@pytest.mark.asyncio
@patch('app.services.ai_integrations.openai_client.OpenAIClient._make_openai_request')
async def test_analyze_diff_success_json(mock_make_request, mock_settings_openai):
    client = OpenAIClient(api_key="test_key_for_diff_json")
    old_rep, new_rep = "Old", "New"
    expected_analysis = {"summary": "Changes", "details": {}}
    mock_content_string = json.dumps(expected_analysis)
    mock_make_request.return_value = {"choices": [{"message": {"content": mock_content_string}}]}

    analysis = await client.analyze_diff(old_rep, new_rep, api_params={"response_format": {"type": "json_object"}})
    assert analysis == expected_analysis

@pytest.mark.asyncio
@patch('app.services.ai_integrations.openai_client.OpenAIClient._make_openai_request')
async def test_analyze_diff_success_text(mock_make_request, mock_settings_openai):
    client = OpenAIClient(api_key="test_key_for_diff_text")
    old_rep, new_rep = "Old", "New"
    expected_summary = "Text summary"
    mock_make_request.return_value = {"choices": [{"message": {"content": expected_summary}}]}

    analysis = await client.analyze_diff(old_rep, new_rep) # No JSON requested
    assert analysis["summary"] == expected_summary
    assert analysis["details"] == {}

@pytest.mark.asyncio
@patch('app.services.ai_integrations.openai_client.OpenAIClient._make_openai_request')
async def test_analyze_diff_invalid_json_response(mock_make_request, mock_settings_openai):
    client = OpenAIClient(api_key="test_key_for_diff_invalid")
    old_rep, new_rep = "Old", "New"
    invalid_json_content = "not json"
    mock_make_request.return_value = {"choices": [{"message": {"content": invalid_json_content}}]}

    analysis = await client.analyze_diff(old_rep, new_rep, api_params={"response_format": {"type": "json_object"}})
    assert "AI response was not valid JSON" in analysis["summary"]

@pytest.mark.asyncio
async def test_refine_query_not_implemented(mock_settings_openai):
    client = OpenAIClient(api_key="test_key_refine_ni")
    with pytest.raises(NotImplementedError):
        await client.refine_query("query")

@pytest.mark.asyncio
async def test_identify_sources_not_implemented(mock_settings_openai):
    client = OpenAIClient(api_key="test_key_identify_ni")
    with pytest.raises(NotImplementedError):
        await client.identify_sources("query") 