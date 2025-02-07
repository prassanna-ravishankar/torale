"""Tests for the alerting module."""

from unittest.mock import AsyncMock, patch

import pytest

from ambi_alert.alerting import AlertManager, EmailAlertBackend, MockAlertBackend


@pytest.mark.asyncio
async def test_mock_alert_backend():
    """Test the mock alert backend."""
    backend = MockAlertBackend()
    with patch("builtins.print") as mock_print:
        result = await backend.send_alert("Test Subject", "Test Message")
        assert result is True
        mock_print.assert_called()


@pytest.mark.asyncio
async def test_email_alert_backend():
    """Test the email alert backend."""
    backend = EmailAlertBackend(
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password",  # noqa: S106
        from_email="from@example.com",
        to_email="to@example.com",
    )

    # Mock SMTP client
    mock_smtp = AsyncMock()
    mock_smtp.is_connected = True
    mock_smtp.send_message = AsyncMock(return_value=True)
    backend._client = mock_smtp

    # Test sending alert
    result = await backend.send_alert("Test Subject", "Test Message")
    assert result is True
    mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_email_alert_backend_connection_error():
    """Test email backend handling of connection errors."""
    backend = EmailAlertBackend(
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password",  # noqa: S106
        from_email="from@example.com",
        to_email="to@example.com",
    )

    # Mock SMTP client that raises an exception
    mock_smtp = AsyncMock()
    mock_smtp.send_message = AsyncMock(side_effect=Exception("Connection error"))
    backend._client = mock_smtp

    # Test sending alert with error
    result = await backend.send_alert("Test Subject", "Test Message")
    assert result is False


@pytest.mark.asyncio
async def test_email_alert_backend_context_manager():
    """Test email backend context manager."""
    backend = EmailAlertBackend(
        smtp_server="localhost",  # Use localhost to avoid DNS lookup
        smtp_port=587,
        username="test@example.com",
        password="password",  # noqa: S106
        from_email="from@example.com",
        to_email="to@example.com",
    )

    # Mock the SMTP client creation
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.quit = AsyncMock()

    with patch("aiosmtplib.SMTP", return_value=mock_smtp):
        async with backend:
            assert backend._client is not None

        assert backend._client is None
        mock_smtp.quit.assert_called_once()


@pytest.mark.asyncio
async def test_alert_manager_with_mock_backend():
    """Test alert manager with mock backend."""
    backend = MockAlertBackend()
    manager = AlertManager(backend)

    result = await manager.send_change_alert(
        url="https://example.com",
        query="test query",
        summary="Test summary",
    )

    assert result is True


@pytest.mark.asyncio
async def test_alert_manager_with_email_backend():
    """Test alert manager with email backend."""
    # Create email backend with mocked SMTP
    backend = EmailAlertBackend(
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password",  # noqa: S106
        from_email="from@example.com",
        to_email="to@example.com",
    )
    mock_smtp = AsyncMock()
    mock_smtp.is_connected = True
    mock_smtp.send_message = AsyncMock(return_value=True)
    backend._client = mock_smtp

    manager = AlertManager(backend)

    result = await manager.send_change_alert(
        url="https://example.com",
        query="test query",
        summary="Test summary",
    )

    assert result is True
    mock_smtp.send_message.assert_called_once()
