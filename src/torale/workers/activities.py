import json
from datetime import datetime
from uuid import UUID

import asyncpg
from temporalio import activity

from torale.core.config import settings
from torale.core.models import TaskStatus
from torale.executors.llm_text import LLMTextExecutor


async def get_db_connection():
    """Get a database connection for workers"""
    return await asyncpg.connect(settings.database_url)


@activity.defn
async def execute_task(task_id: str, execution_id: str) -> dict:
    conn = await get_db_connection()

    try:
        # Get task details
        task = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1", UUID(task_id)
        )

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Update execution status to running
        await conn.execute(
            """
            UPDATE task_executions
            SET status = $1
            WHERE id = $2
            """,
            TaskStatus.RUNNING.value,
            UUID(execution_id),
        )

        # Execute based on executor type
        executor_result = None
        try:
            if task["executor_type"] == "llm_text":
                executor = LLMTextExecutor()
                executor_result = await executor.execute(task["config"])
            else:
                raise ValueError(f"Unsupported executor type: {task['executor_type']}")

            # Update execution with success
            await conn.execute(
                """
                UPDATE task_executions
                SET status = $1, result = $2, completed_at = $3
                WHERE id = $4
                """,
                TaskStatus.SUCCESS.value,
                json.dumps(executor_result),
                datetime.utcnow(),
                UUID(execution_id),
            )

            return executor_result

        except Exception as e:
            # Update execution with failure
            await conn.execute(
                """
                UPDATE task_executions
                SET status = $1, error_message = $2, completed_at = $3
                WHERE id = $4
                """,
                TaskStatus.FAILED.value,
                str(e),
                datetime.utcnow(),
                UUID(execution_id),
            )

            raise

    finally:
        await conn.close()


@activity.defn
async def send_notification(user_id: str, task_name: str, result: dict) -> None:
    # TODO: Implement notification sending via NotificationAPI
    print(f"Would send notification to user {user_id} for task '{task_name}'")
    print(f"Result: {result}")
    pass
