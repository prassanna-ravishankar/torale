from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from torale.monitoring import EnrichedMonitoringResult
from torale.tasks.tasks import TaskExecutionRequest


@workflow.defn
class TaskExecutionWorkflow:
    """
    Smart workflow that orchestrates monitoring execution.

    Orchestration logic is now visible at the workflow level:
    1. Fetch task configuration
    2. Perform grounded search
    3. Execute monitoring pipeline (extraction + comparison)
    4. Decide notification (based on change detection)
    5. Send notification if needed
    6. Persist execution result

    This replaces the "god activity" pattern with focused activities.
    """

    @workflow.run
    async def run(self, request: TaskExecutionRequest) -> dict:
        # Main retry policy for core activities
        # ApplicationError is non-retryable (deleted tasks, inactive tasks)
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2,
            non_retryable_error_types=["ApplicationError"],
        )

        # Step 1: Fetch task configuration and context
        task_data = await workflow.execute_activity(
            "get_task_data",
            args=[request.task_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Step 2: Perform grounded search
        search_result = await workflow.execute_activity(
            "perform_grounded_search",
            args=[task_data],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        # Step 3: Execute monitoring pipeline (extraction + comparison)
        monitoring_result = await workflow.execute_activity(
            "execute_monitoring_pipeline",
            args=[task_data, search_result],
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=retry_policy,
        )

        # Step 4: Enrich result with metadata for notifications
        # Create typed enriched result
        # Note: monitoring_result is a dict from execute_monitoring_pipeline activity
        # which returns MonitoringResult.model_dump(). If MonitoringResult schema changes,
        # ensure the activity return value stays compatible with this unpacking.
        is_first_execution = task_data.get("previous_state") is None
        enriched_result_model = EnrichedMonitoringResult(
            **monitoring_result,
            task_id=request.task_id,
            execution_id=request.execution_id,
            search_query=task_data["task"]["search_query"],
            is_first_execution=is_first_execution,
        )
        enriched_result = enriched_result_model.model_dump()

        # Step 5: Decide notification (VISIBLE orchestration logic!)
        changed = enriched_result.get("metadata", {}).get("changed", False)
        should_notify = changed and not request.suppress_notifications

        # Step 6: Send notifications if needed (orchestrated via focused activities)
        # Notifications should not fail the workflow, so wrap in try-except
        # Configure minimal retry policy for notifications
        notification_retry_policy = RetryPolicy(
            maximum_attempts=2,  # Try once more for transient failures
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2,
            non_retryable_error_types=["ApplicationError"],  # Skip spam limits, missing config
        )

        if should_notify:
            try:
                # 6a: Fetch notification context (task, user, execution details)
                notification_context = await workflow.execute_activity(
                    "fetch_notification_context",
                    args=[request.task_id, request.execution_id, request.user_id],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,  # Use default retry for fetching context
                )

                # 6b: Send email notification if channel is enabled
                if "email" in notification_context.get("notification_channels", ["email"]):
                    await workflow.execute_activity(
                        "send_email_notification",
                        args=[
                            request.user_id,
                            request.task_name,
                            notification_context,
                            enriched_result,
                        ],
                        start_to_close_timeout=timedelta(minutes=1),
                        retry_policy=notification_retry_policy,
                    )

                # 6c: Send webhook notification if channel is enabled
                if "webhook" in notification_context.get("notification_channels", []):
                    await workflow.execute_activity(
                        "send_webhook_notification",
                        args=[notification_context, enriched_result],
                        start_to_close_timeout=timedelta(minutes=1),
                        retry_policy=notification_retry_policy,
                    )
            except Exception as e:
                # Log but don't fail workflow for notification failures
                workflow.logger.warning(f"Notification failed: {e}")

        # Step 7: Persist execution result
        await workflow.execute_activity(
            "persist_execution_result",
            args=[request.task_id, request.execution_id, enriched_result],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        # Step 8: Handle task completion if notify_behavior is "once" and condition changed
        if changed and task_data["task"]["notify_behavior"] == "once":
            await workflow.execute_activity(
                "complete_task",
                args=[request.task_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

        return enriched_result
