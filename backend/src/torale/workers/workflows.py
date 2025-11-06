from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


@dataclass
class TaskExecutionRequest:
    task_id: str
    execution_id: str
    user_id: str
    task_name: str


@workflow.defn
class TaskExecutionWorkflow:
    @workflow.run
    async def run(self, request: TaskExecutionRequest) -> dict:
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2,
        )

        # Execute the task (using string name to avoid importing activities)
        result = await workflow.execute_activity(
            "execute_task",
            args=[request.task_id, request.execution_id],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        # Send notification
        await workflow.execute_activity(
            "send_notification",
            args=[request.user_id, request.task_name, result],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        return result
