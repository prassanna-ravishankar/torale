import json
import logging
from datetime import datetime
from uuid import UUID

import asyncpg
from temporalio import activity

from torale.core.config import settings
from torale.core.models import NotifyBehavior, TaskStatus
from torale.executors import GroundedSearchExecutor

logger = logging.getLogger(__name__)


async def get_db_connection():
    """Get a database connection for workers"""
    return await asyncpg.connect(settings.database_url)


@activity.defn
async def execute_task(task_id: str, execution_id: str) -> dict:
    conn = await get_db_connection()

    try:
        # Get task details
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", UUID(task_id))

        if not task:
            # Task was deleted but schedule still exists (orphaned schedule)
            # Log warning and return gracefully to avoid retries
            logger.warning(
                f"Task {task_id} not found in database (likely deleted). "
                f"Skipping execution. Schedule should be cleaned up."
            )
            return {
                "status": "skipped",
                "reason": "task_deleted",
                "message": f"Task {task_id} was deleted but schedule still exists",
            }

        # Parse config if it's a JSON string
        config = task["config"]
        if isinstance(config, str):
            config = json.loads(config)

        # Parse last_known_state if it's a JSON string
        last_known_state = task.get("last_known_state")
        if isinstance(last_known_state, str):
            last_known_state = json.loads(last_known_state) if last_known_state else None

        # Create execution record if not provided (scheduled execution)
        if not execution_id:
            row = await conn.fetchrow(
                """
                INSERT INTO task_executions (task_id, status)
                VALUES ($1, $2)
                RETURNING id
                """,
                UUID(task_id),
                TaskStatus.PENDING.value,
            )
            execution_id = str(row["id"])

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
            if task["executor_type"] == "llm_grounded_search":
                # Prepare config for grounded search executor
                executor_config = {
                    **config,
                    "search_query": task["search_query"],
                    "condition_description": task["condition_description"],
                    "last_known_state": last_known_state,
                }

                executor = GroundedSearchExecutor()
                executor_result = await executor.execute(executor_config)

                # Extract grounded search fields
                condition_met = executor_result.get("condition_met", False)
                change_summary = executor_result.get("change_summary")
                grounding_sources = executor_result.get("grounding_sources", [])
                current_state = executor_result.get("current_state", {})

                # Update execution with grounded search fields
                await conn.execute(
                    """
                    UPDATE task_executions
                    SET status = $1, result = $2, completed_at = $3,
                        condition_met = $4, change_summary = $5, grounding_sources = $6
                    WHERE id = $7
                    """,
                    TaskStatus.SUCCESS.value,
                    json.dumps(executor_result),
                    datetime.utcnow(),
                    condition_met,
                    change_summary,
                    json.dumps(grounding_sources),
                    UUID(execution_id),
                )

                # Update task state tracking
                await conn.execute(
                    """
                    UPDATE tasks
                    SET last_known_state = $1, condition_met = $2, updated_at = $3
                    WHERE id = $4
                    """,
                    json.dumps(current_state),
                    condition_met,
                    datetime.utcnow(),
                    UUID(task_id),
                )

                # Handle notify behavior if condition is met
                if condition_met:
                    notify_behavior = task.get("notify_behavior", "once")

                    # Update last_notified_at
                    await conn.execute(
                        """
                        UPDATE tasks
                        SET last_notified_at = $1
                        WHERE id = $2
                        """,
                        datetime.utcnow(),
                        UUID(task_id),
                    )

                    # Auto-disable task if notify_behavior is "once"
                    if notify_behavior == NotifyBehavior.ONCE.value:
                        await conn.execute(
                            """
                            UPDATE tasks
                            SET is_active = false
                            WHERE id = $1
                            """,
                            UUID(task_id),
                        )

            else:
                raise ValueError(f"Unsupported executor type: {task['executor_type']}")

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
