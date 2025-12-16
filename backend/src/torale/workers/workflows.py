from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from torale.core.models import TaskExecutionRequest


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
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2,
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
        # Create new enriched result instead of mutating
        is_first_execution = task_data.get("previous_state") is None
        enriched_result = {
            **monitoring_result,
            "task_id": request.task_id,
            "execution_id": request.execution_id,
            "search_query": task_data["task"]["search_query"],
            "is_first_execution": is_first_execution,
        }

        # Step 5: Decide notification (VISIBLE orchestration logic!)
        changed = enriched_result.get("metadata", {}).get("changed", False)
        should_notify = changed and not request.suppress_notifications

        # Step 6: Send notification if needed
        if should_notify:
            await workflow.execute_activity(
                "send_notification",
                args=[request.user_id, request.task_name, enriched_result],
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )

        # Step 7: Persist execution result
        await workflow.execute_activity(
            "persist_execution_result",
            args=[request.task_id, request.execution_id, enriched_result],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        return enriched_result
