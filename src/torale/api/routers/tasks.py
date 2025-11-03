import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from torale.api.auth import CurrentUser
from torale.core.database import Database, get_db
from torale.core.models import Task, TaskCreate, TaskExecution, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def parse_task_row(row) -> dict:
    """Parse a task row from the database, converting JSON strings to dicts"""
    task_dict = dict(row)
    # Parse config if it's a string
    if isinstance(task_dict.get("config"), str):
        task_dict["config"] = json.loads(task_dict["config"])
    return task_dict


def parse_execution_row(row) -> dict:
    """Parse an execution row from the database, converting JSON strings to dicts"""
    exec_dict = dict(row)
    # Parse result if it's a string
    if isinstance(exec_dict.get("result"), str):
        exec_dict["result"] = json.loads(exec_dict["result"])
    return exec_dict


@router.post("/", response_model=Task)
async def create_task(task: TaskCreate, user: CurrentUser, db: Database = Depends(get_db)):
    query = """
        INSERT INTO tasks (user_id, name, schedule, executor_type, config, is_active)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, user_id, name, schedule, executor_type, config, is_active, created_at, updated_at
    """

    row = await db.fetch_one(
        query,
        user.id,
        task.name,
        task.schedule,
        task.executor_type,
        json.dumps(task.config),
        task.is_active,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create task",
        )

    return Task(**parse_task_row(row))


@router.get("/", response_model=list[Task])
async def list_tasks(
    user: CurrentUser, is_active: bool | None = None, db: Database = Depends(get_db)
):
    if is_active is not None:
        query = """
            SELECT id, user_id, name, schedule, executor_type, config, is_active, created_at, updated_at
            FROM tasks
            WHERE user_id = $1 AND is_active = $2
            ORDER BY created_at DESC
        """
        rows = await db.fetch_all(query, user.id, is_active)
    else:
        query = """
            SELECT id, user_id, name, schedule, executor_type, config, is_active, created_at, updated_at
            FROM tasks
            WHERE user_id = $1
            ORDER BY created_at DESC
        """
        rows = await db.fetch_all(query, user.id)

    return [Task(**parse_task_row(row)) for row in rows]


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    query = """
        SELECT id, user_id, name, schedule, executor_type, config, is_active, created_at, updated_at
        FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    row = await db.fetch_one(query, task_id, user.id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return Task(**parse_task_row(row))


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID, task_update: TaskUpdate, user: CurrentUser, db: Database = Depends(get_db)
):
    # First verify the task belongs to the user
    existing_query = """
        SELECT id, user_id, name, schedule, executor_type, config, is_active, created_at, updated_at
        FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    existing = await db.fetch_one(existing_query, task_id, user.id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)

    if not update_data:
        return Task(**parse_task_row(existing))

    # Build dynamic UPDATE query
    set_clauses = []
    params = []
    param_num = 1

    for field, value in update_data.items():
        if field == "config":
            set_clauses.append(f"{field} = ${param_num}")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{field} = ${param_num}")
            params.append(value)
        param_num += 1

    params.append(task_id)
    params.append(user.id)

    query = f"""
        UPDATE tasks
        SET {", ".join(set_clauses)}
        WHERE id = ${param_num} AND user_id = ${param_num + 1}
        RETURNING id, user_id, name, schedule, executor_type, config, is_active, created_at, updated_at
    """

    row = await db.fetch_one(query, *params)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update task",
        )

    return Task(**parse_task_row(row))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    query = """
        DELETE FROM tasks
        WHERE id = $1 AND user_id = $2
        RETURNING id
    """

    row = await db.fetch_one(query, task_id, user.id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return None


@router.post("/{task_id}/execute", response_model=TaskExecution)
async def execute_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    # Verify task exists and belongs to user
    task_query = """
        SELECT id FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    task = await db.fetch_one(task_query, task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Create execution record
    execution_query = """
        INSERT INTO task_executions (task_id, status)
        VALUES ($1, $2)
        RETURNING id, task_id, status, started_at, completed_at, result, error_message, created_at
    """

    row = await db.fetch_one(execution_query, task_id, "pending")

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create execution",
        )

    # TODO: Trigger Temporal workflow for actual execution

    return TaskExecution(**parse_execution_row(row))


@router.get("/{task_id}/executions", response_model=list[TaskExecution])
async def get_task_executions(
    task_id: UUID, user: CurrentUser, limit: int = 100, db: Database = Depends(get_db)
):
    # Verify task belongs to user
    task_query = """
        SELECT id FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    task = await db.fetch_one(task_query, task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get executions
    executions_query = """
        SELECT id, task_id, status, started_at, completed_at, result, error_message, created_at
        FROM task_executions
        WHERE task_id = $1
        ORDER BY started_at DESC
        LIMIT $2
    """

    rows = await db.fetch_all(executions_query, task_id, limit)

    return [TaskExecution(**parse_execution_row(row)) for row in rows]
