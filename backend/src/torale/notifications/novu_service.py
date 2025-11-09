"""Novu Cloud notification service."""

import logging

from torale.core.config import settings

logger = logging.getLogger(__name__)


class NovuService:
    """Novu Cloud notification service."""

    def __init__(self):
        if not settings.novu_secret_key:
            # Don't fail - just log warning and disable notifications
            logger.warning("Novu secret key not configured - notifications disabled")
            self._enabled = False
            self._client = None
        else:
            self._enabled = True
            # Import here to avoid errors if novu not installed
            try:
                from novu_py import Novu

                self._client = Novu(
                    secret_key=settings.novu_secret_key, server_url=settings.novu_api_url
                )
                logger.info("Novu service initialized successfully")
            except ImportError:
                logger.error("novu-py package not installed. Run: uv add novu-py")
                self._enabled = False
                self._client = None

    async def send_condition_met_notification(
        self,
        subscriber_id: str,  # user email
        task_name: str,
        search_query: str,
        answer: str,
        change_summary: str | None,
        grounding_sources: list[dict],
        task_id: str,
        execution_id: str,
    ) -> dict:
        """
        Send notification when monitoring condition is met.

        Returns: {"success": bool, "transaction_id": str, "error": str}
        """
        if not self._enabled or not self._client:
            return {
                "success": False,
                "error": "Novu not configured",
                "skipped": True,
            }

        try:
            import novu_py

            # Trigger Novu workflow
            response = await self._client.trigger_async(
                trigger_event_request_dto=novu_py.TriggerEventRequestDto(
                    workflow_id=settings.novu_workflow_id,
                    to={
                        "subscriber_id": subscriber_id,
                        "email": subscriber_id,  # Explicitly provide email address
                    },
                    payload={
                        "task_name": task_name,
                        "search_query": search_query,
                        "answer": answer,
                        "change_summary": change_summary or "Condition met",
                        "grounding_sources": grounding_sources[:5],  # Limit to 5 sources
                        "task_id": task_id,
                        "execution_id": execution_id,
                    },
                )
            )

            # Extract transaction ID from response
            transaction_id = None
            if hasattr(response, "result") and hasattr(response.result, "transaction_id"):
                transaction_id = response.result.transaction_id

            logger.info(f"Notification sent to {subscriber_id}: {transaction_id}")

            return {
                "success": True,
                "transaction_id": transaction_id,
            }

        except Exception as e:
            # Don't raise - log error and return failure
            logger.error(f"Novu API error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def send_verification_email(self, email: str, code: str, user_name: str) -> dict:
        """
        Send email verification code.

        Returns: {"success": bool, "transaction_id": str, "error": str}
        """
        if not self._enabled or not self._client:
            # For development - just log the code
            logger.warning(f"Novu not configured - verification code for {email}: {code}")
            return {
                "success": False,
                "error": "Novu not configured",
                "skipped": True,
            }

        try:
            import novu_py

            # Trigger verification workflow
            response = await self._client.trigger_async(
                trigger_event_request_dto=novu_py.TriggerEventRequestDto(
                    workflow_id=settings.novu_verification_workflow_id,
                    to={
                        "subscriber_id": email,
                        "email": email,  # Explicitly provide email address
                    },
                    payload={
                        "code": code,
                        "user_name": user_name,
                        "expires_in_minutes": 15,
                    },
                )
            )

            # Extract transaction ID from response
            transaction_id = None
            if hasattr(response, "result") and hasattr(response.result, "transaction_id"):
                transaction_id = response.result.transaction_id

            logger.info(f"Verification email sent to {email}: {transaction_id}")

            return {
                "success": True,
                "transaction_id": transaction_id,
            }

        except Exception as e:
            logger.error(f"Novu verification email error: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
novu_service = NovuService()
