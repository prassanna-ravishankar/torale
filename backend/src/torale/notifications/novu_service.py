"""Novu Cloud notification service."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from torale.core.config import settings

logger = logging.getLogger(__name__)


def _parse_iso(value: str | None) -> datetime | None:
    """Parse ISO 8601 string to datetime, handling Z suffix."""
    if not value or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _format_next_run(next_run: str | None) -> str | None:
    """Format ISO 8601 next_run as human-readable string for Novu templates."""
    dt = _parse_iso(next_run)
    if dt is None:
        return None
    return dt.strftime("%B %d, %Y at %I:%M %p")


def _format_confidence(confidence: float | None) -> str | None:
    """Format confidence as percentage string for Novu templates."""
    if confidence is None:
        return None
    return f"{round(confidence * 100)}%"


def _md_to_html(text: str, extensions: list[str] | None = None) -> str:
    """Convert markdown to HTML, falling back to simple newline replacement."""
    try:
        import markdown

        return markdown.markdown(text, extensions=extensions or ["nl2br"])
    except ImportError:
        logger.warning("markdown library not installed - using plain text")
        return text.replace("\n", "<br>")


def _format_sources(sources: list[dict], limit: int = 5) -> list[dict]:
    """Transform grounding sources: url → uri for Novu template compatibility."""
    return [{"uri": s.get("url", ""), "title": s.get("title", "Unknown")} for s in sources[:limit]]


@dataclass
class NotificationPayload:
    """Shared context for task notification emails."""

    subscriber_id: str
    task_name: str
    search_query: str
    answer: str
    grounding_sources: list[dict]
    task_id: str
    next_run: str | None = None


class NovuService:
    """Novu Cloud notification service."""

    def __init__(self):
        if not settings.novu_secret_key:
            logger.warning("Novu secret key not configured - notifications disabled")
            self._enabled = False
            self._client = None
        else:
            self._enabled = True
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

    async def _trigger(self, workflow_id: str, subscriber_id: str, payload: dict) -> dict:
        """Trigger a Novu workflow and return result dict."""
        if not self._enabled or not self._client:
            return {"success": False, "error": "Novu not configured", "skipped": True}

        try:
            import novu_py

            response = await self._client.trigger_async(
                trigger_event_request_dto=novu_py.TriggerEventRequestDto(
                    workflow_id=workflow_id,
                    to={"subscriber_id": subscriber_id, "email": subscriber_id},
                    payload=payload,
                )
            )

            transaction_id = None
            if hasattr(response, "result") and hasattr(response.result, "transaction_id"):
                transaction_id = response.result.transaction_id

            logger.info(f"Novu workflow '{workflow_id}' sent to {subscriber_id}: {transaction_id}")
            return {"success": True, "transaction_id": transaction_id}

        except Exception as e:
            logger.error(f"Novu workflow '{workflow_id}' error: {e}")
            return {"success": False, "error": str(e)}

    async def send_condition_met_notification(
        self,
        payload: NotificationPayload,
        execution_id: str,
        confidence: float | None = None,
    ) -> dict:
        """Send notification when monitoring condition is met."""
        return await self._trigger(
            workflow_id=settings.novu_workflow_id,
            subscriber_id=payload.subscriber_id,
            payload={
                "task_name": payload.task_name,
                "search_query": payload.search_query,
                "answer": _md_to_html(
                    payload.answer, extensions=["nl2br", "fenced_code", "tables"]
                ),
                "grounding_sources": _format_sources(payload.grounding_sources),
                "task_id": payload.task_id,
                "execution_id": execution_id,
                "next_run": _format_next_run(payload.next_run),
                "confidence": _format_confidence(confidence),
            },
        )

    async def send_verification_email(self, email: str, code: str, user_name: str) -> dict:
        """Send email verification code."""
        if not self._enabled or not self._client:
            logger.warning(f"Novu not configured - verification code for {email}: {code}")
        return await self._trigger(
            workflow_id=settings.novu_verification_workflow_id,
            subscriber_id=email,
            payload={
                "code": code,
                "user_name": user_name,
                "expires_in_minutes": 15,
            },
        )

    async def send_welcome_email(
        self,
        payload: NotificationPayload,
        first_execution_result: dict | None,
    ) -> dict:
        """Send welcome email after task creation with first execution results."""
        answer_html = None
        if first_execution_result:
            answer_html = _md_to_html(first_execution_result.get("answer", ""))

        formatted_sources = []
        if first_execution_result and first_execution_result.get("grounding_sources"):
            formatted_sources = _format_sources(first_execution_result["grounding_sources"])

        return await self._trigger(
            workflow_id=settings.novu_welcome_workflow_id,
            subscriber_id=payload.subscriber_id,
            payload={
                "task_name": payload.task_name,
                "search_query": payload.search_query,
                "answer": answer_html,
                "condition_met": (
                    first_execution_result.get("condition_met") if first_execution_result else False
                ),
                "grounding_sources": formatted_sources,
                "task_id": payload.task_id,
                "next_run": _format_next_run(payload.next_run),
            },
        )


# Singleton instance
novu_service = NovuService()
