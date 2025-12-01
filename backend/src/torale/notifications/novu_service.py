"""Novu Cloud notification service."""

import logging

from cron_descriptor import Options, get_description

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

            # Convert markdown answer to HTML for email rendering
            try:
                import markdown

                answer_html = markdown.markdown(
                    answer, extensions=["nl2br", "fenced_code", "tables"]
                )
            except ImportError:
                logger.warning("markdown library not installed - using plain text")
                answer_html = answer.replace("\n", "<br>")

            # Transform grounding sources: url → uri for Novu template compatibility
            formatted_sources = [
                {"uri": s.get("url", ""), "title": s.get("title", "Unknown")}
                for s in grounding_sources[:5]  # Limit to 5 sources
            ]

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
                        "answer": answer_html,  # Send HTML-formatted answer
                        "change_summary": change_summary or "Condition met",
                        "grounding_sources": formatted_sources,
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

    async def send_welcome_email(
        self,
        subscriber_id: str,
        task_name: str,
        search_query: str,
        condition_description: str,
        notify_behavior: str,
        schedule: str,
        first_execution_result: dict | None,
        task_id: str,
    ) -> dict:
        """
        Send welcome email after task creation with first execution results.

        This email is ONLY sent after the first execution completes, so it always
        includes execution results.

        Email explains:
        - What's being monitored
        - When next check runs
        - How user will be notified
        - First execution results with sources
        - notify_behavior explanation
        - Next steps (conditional based on condition_met and notify_behavior)

        Returns: {"success": bool, "transaction_id": str, "error": str}
        """
        if not self._enabled or not self._client:
            logger.warning(f"Novu not configured - welcome email for {subscriber_id}")
            return {"success": False, "error": "Novu not configured", "skipped": True}

        try:
            import novu_py

            # Convert markdown to HTML if first execution completed
            answer_html = None
            if first_execution_result:
                answer = first_execution_result.get("answer", "")
                try:
                    import markdown

                    answer_html = markdown.markdown(answer, extensions=["nl2br"])
                except ImportError:
                    logger.warning("markdown library not installed - using plain text")
                    answer_html = answer.replace("\n", "<br>")

            # Format grounding sources
            formatted_sources = []
            if first_execution_result and first_execution_result.get("grounding_sources"):
                formatted_sources = [
                    {"uri": s.get("url", ""), "title": s.get("title", "Unknown")}
                    for s in first_execution_result["grounding_sources"][:5]
                ]

            # Human-readable schedule using cron-descriptor
            # Use verbose mode to include frequency (e.g., "Every day at 09:00 AM")
            options = Options()
            options.use_24hour_time_format = False
            options.verbose = True
            schedule_description = get_description(schedule, options)

            # Trigger welcome workflow
            response = await self._client.trigger_async(
                trigger_event_request_dto=novu_py.TriggerEventRequestDto(
                    workflow_id=settings.novu_welcome_workflow_id,
                    to={
                        "subscriber_id": subscriber_id,
                        "email": subscriber_id,
                    },
                    payload={
                        "task_name": task_name,
                        "search_query": search_query,
                        "condition_description": condition_description,
                        "notify_behavior": notify_behavior,
                        "schedule_description": schedule_description,
                        "answer": answer_html,
                        "condition_met": (
                            first_execution_result.get("condition_met")
                            if first_execution_result
                            else False
                        ),
                        "grounding_sources": formatted_sources,
                        "task_id": task_id,
                    },
                )
            )

            transaction_id = None
            if hasattr(response, "result") and hasattr(response.result, "transaction_id"):
                transaction_id = response.result.transaction_id

            logger.info(f"Welcome email sent to {subscriber_id}: {transaction_id}")
            return {"success": True, "transaction_id": transaction_id}

        except Exception as e:
            logger.error(f"Welcome email error: {str(e)}")
            return {"success": False, "error": str(e)}


# Singleton instance
novu_service = NovuService()
