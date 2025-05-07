import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.embedding_service import EmbeddingService


@pytest.fixture
def embedding_service():
    """Pytest fixture to create an EmbeddingService instance."""
    return EmbeddingService()


# --- Tests for compare_embeddings ---


@pytest.mark.asyncio
async def test_compare_embeddings_identical(embedding_service):
    """Test comparing identical embeddings (similarity should be ~1.0)."""
    vec = [1.0, 0.0]
    embedding_json = json.dumps(vec)
    similarity = await embedding_service.compare_embeddings(
        embedding_json, embedding_json
    )
    assert isinstance(similarity, float)
    assert np.isclose(similarity, 1.0)


@pytest.mark.asyncio
async def test_compare_embeddings_orthogonal(embedding_service):
    """Test comparing orthogonal embeddings (similarity should be ~0.0)."""
    vec1 = [1.0, 0.0]
    vec2 = [0.0, 1.0]
    embedding1_json = json.dumps(vec1)
    embedding2_json = json.dumps(vec2)
    similarity = await embedding_service.compare_embeddings(
        embedding1_json, embedding2_json
    )
    assert isinstance(similarity, float)
    assert np.isclose(similarity, 0.0)


@pytest.mark.asyncio
async def test_compare_embeddings_opposite(embedding_service):
    """Test comparing opposite embeddings (similarity should be ~-1.0)."""
    vec1 = [1.0, 0.0]
    vec2 = [-1.0, 0.0]
    embedding1_json = json.dumps(vec1)
    embedding2_json = json.dumps(vec2)
    similarity = await embedding_service.compare_embeddings(
        embedding1_json, embedding2_json
    )
    assert isinstance(similarity, float)
    assert np.isclose(similarity, -1.0)


# --- Tests for generate_embedding (with mocking) ---


@pytest.mark.asyncio
@patch("app.services.embedding_service.SentenceTransformer")  # Mock the class
async def test_generate_embedding_mocked(mock_sentence_transformer):
    """Test generate_embedding with a mocked SentenceTransformer."""
    # Configure the mock model and its encode method
    mock_model_instance = MagicMock()
    mock_encode_return_value = np.array([0.1, 0.2, 0.3])
    mock_model_instance.encode.return_value = mock_encode_return_value
    mock_sentence_transformer.return_value = mock_model_instance

    # Create the service *inside* the test where the patch is active
    service_under_test = EmbeddingService()

    test_text = "This is a test"
    expected_json_output = json.dumps(mock_encode_return_value.tolist())

    # Act
    result_json = await service_under_test.generate_embedding(test_text)

    # Assert
    # Check that the mocked encode method was called correctly
    mock_model_instance.encode.assert_called_once_with(test_text)

    # Check that the output is the correctly JSON-ified mock return value
    assert result_json == expected_json_output
