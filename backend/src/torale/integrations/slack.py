"""Slack OAuth integration service."""

import logging

from cryptography.fernet import Fernet
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from torale.core.config import settings
from torale.core.database import Database

logger = logging.getLogger(__name__)


class SlackOAuthService:
    """Handle Slack OAuth flow and message posting."""

    OAUTH_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
    OAUTH_SCOPES = "chat:write,channels:read"

    def __init__(self, db: Database):
        self.db = db
        if not settings.oauth_encryption_key:
            raise ValueError(
                "OAUTH_ENCRYPTION_KEY environment variable is required for Slack integration. "
                "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        self.cipher = Fernet(settings.oauth_encryption_key.encode())

    def get_authorize_url(self, state: str) -> str:
        """Generate Slack OAuth authorization URL."""
        return (
            f"{self.OAUTH_AUTHORIZE_URL}?"
            f"client_id={settings.slack_client_id}&"
            f"scope={self.OAUTH_SCOPES}&"
            f"redirect_uri={settings.slack_redirect_uri}&"
            f"state={state}"
        )

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange OAuth code for access token. Raises SlackApiError on failure."""
        client = AsyncWebClient()
        response = await client.oauth_v2_access(
            client_id=settings.slack_client_id,
            client_secret=settings.slack_client_secret,
            code=code,
        )

        return {
            "access_token": response["access_token"],
            "workspace_id": response["team"]["id"],
            "workspace_name": response["team"]["name"],
            "bot_user_id": response.get("bot_user_id"),
        }

    async def list_channels(self, access_token: str) -> list[dict]:
        """Fetch user's Slack channels. Raises SlackApiError on failure."""
        client = AsyncWebClient(token=self._decrypt_token(access_token))
        response = await client.conversations_list(
            types="public_channel,private_channel", limit=1000
        )

        return [
            {"id": ch["id"], "name": f"#{ch['name']}"}
            for ch in response["channels"]
            if not ch["is_archived"]
        ]

    async def post_message(
        self, token: str, channel_id: str, blocks: list[dict], fallback_text: str
    ) -> bool:
        """Post message to Slack channel. Returns False on failure (non-raising)."""
        client = AsyncWebClient(token=self._decrypt_token(token))

        try:
            response = await client.chat_postMessage(
                channel=channel_id, blocks=blocks, text=fallback_text
            )
            return response["ok"]
        except SlackApiError as e:
            logger.error(f"Failed to post to Slack: {e}")
            return False

    def encrypt_token(self, token: str) -> str:
        """Encrypt token for storage."""
        return self.cipher.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted: str) -> str:
        """Decrypt stored token."""
        return self.cipher.decrypt(encrypted.encode()).decode()
