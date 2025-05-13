from unittest.mock import patch

import pytest

from app.services.ai_integrations.perplexity_client import (
    PerplexityClient,
)


@pytest.fixture
def mock_settings_perplexity():  # Renamed fixture
    with patch(
        "app.services.ai_integrations.perplexity_client.settings"
    ) as mock_settings_obj:
        mock_settings_obj.PERPLEXITY_API_KEY = "test_api_key"
        yield mock_settings_obj


@pytest.mark.asyncio
async def test_perplexity_client_init_success(mock_settings_perplexity):
    client = PerplexityClient(api_key="explicit_key")
    assert client.api_key == "explicit_key"
    assert client.model == "sonar-medium-online"
    assert client.headers["Authorization"] == "Bearer explicit_key"


@pytest.mark.asyncio
async def test_perplexity_client_init_no_key(mock_settings_perplexity):
    mock_settings_perplexity.PERPLEXITY_API_KEY = None
    with pytest.raises(ValueError, match="Perplexity API key is required"):
        PerplexityClient(api_key=None)


@pytest.mark.asyncio
@patch(
    "app.services.ai_integrations.perplexity_client.PerplexityClient._make_perplexity_request"
)
async def test_refine_query_success(mock_make_request, mock_settings_perplexity):
    client = PerplexityClient(api_key="test_key_refine")
    raw_query = "Test query"
    expected_refined = "Refined test query"
    mock_make_request.return_value = {
        "choices": [{"message": {"content": expected_refined}}]
    }

    refined_query = await client.refine_query(raw_query)
    assert refined_query == expected_refined
    mock_make_request.assert_called_once()

    # The _make_perplexity_request is called with (self, payload)
    # The URL is handled internally by the method being patched.
    called_payload = mock_make_request.call_args[0][
        0
    ]  # First positional arg to the mock
    assert called_payload["messages"][1]["content"] == raw_query
    assert called_payload["model"] == client.model


@pytest.mark.asyncio
@patch(
    "app.services.ai_integrations.perplexity_client.PerplexityClient._make_perplexity_request"
)
async def test_refine_query_api_error(mock_make_request, mock_settings_perplexity):
    client = PerplexityClient(api_key="test_key_refine_err")
    raw_query = "Test query error"
    mock_make_request.side_effect = ConnectionError("Simulated API error")

    with pytest.raises(ConnectionError, match="Simulated API error"):
        await client.refine_query(raw_query)


@pytest.mark.asyncio
@patch(
    "app.services.ai_integrations.perplexity_client.PerplexityClient._make_perplexity_request"
)
async def test_refine_query_malformed_response(
    mock_make_request, mock_settings_perplexity
):
    client = PerplexityClient(api_key="test_key_refine_malformed")
    raw_query = "Malformed query"
    mock_make_request.return_value = {"invalid": "structure"}

    with pytest.raises(
        ValueError,
        match="Invalid response structure from Perplexity API for refine_query",
    ):
        await client.refine_query(raw_query)


@pytest.mark.asyncio
@patch(
    "app.services.ai_integrations.perplexity_client.PerplexityClient._make_perplexity_request"
)
async def test_identify_sources_success(mock_make_request, mock_settings_perplexity):
    client = PerplexityClient(api_key="test_key_identify")
    refined_query = "Refined query for sources"
    expected_urls = ["https://example.com/source1", "http://anothersource.org"]
    mock_response_content_string = "\n".join(expected_urls)
    mock_make_request.return_value = {
        "choices": [{"message": {"content": mock_response_content_string}}]
    }

    sources = await client.identify_sources(refined_query)
    assert sources == expected_urls


@pytest.mark.asyncio
@patch(
    "app.services.ai_integrations.perplexity_client.PerplexityClient._make_perplexity_request"
)
async def test_identify_sources_empty_response(
    mock_make_request, mock_settings_perplexity
):
    client = PerplexityClient(api_key="test_key_identify_empty")
    refined_query = "Empty response query"
    mock_make_request.return_value = {"choices": [{"message": {"content": "  \n  "}}]}

    sources = await client.identify_sources(refined_query)
    assert sources == []


@pytest.mark.asyncio
@patch(
    "app.services.ai_integrations.perplexity_client.PerplexityClient._make_perplexity_request"
)
async def test_identify_sources_malformed_response(
    mock_make_request, mock_settings_perplexity
):
    client = PerplexityClient(api_key="test_key_identify_malformed")
    refined_query = "Malformed response query"
    mock_make_request.return_value = {"invalid": "structure"}

    with pytest.raises(
        ValueError,
        match="Invalid response structure from Perplexity API for identify_sources",
    ):
        await client.identify_sources(refined_query)


@pytest.mark.asyncio
async def test_generate_embeddings_not_implemented(mock_settings_perplexity):
    client = PerplexityClient()
    with pytest.raises(NotImplementedError):
        await client.generate_embeddings(["text"])


@pytest.mark.asyncio
async def test_analyze_diff_not_implemented(mock_settings_perplexity):
    client = PerplexityClient()
    with pytest.raises(NotImplementedError):
        await client.analyze_diff("old", "new")
