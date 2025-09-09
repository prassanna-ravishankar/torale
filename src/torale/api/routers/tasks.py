from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from torale.api.auth import CurrentUser
from torale.core.database import get_supabase_client
from torale.core.models import Task, TaskCreate, TaskExecution, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=Task)
async def create_task(task: TaskCreate, user: CurrentUser):
    supabase = get_supabase_client()
    
    data = {
        **task.model_dump(),
        "user_id": user["id"],
    }
    
    response = supabase.table("tasks").insert(data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create task",
        )
    
    return Task(**response.data[0])


@router.get("/", response_model=list[Task])
async def list_tasks(user: CurrentUser, is_active: bool | None = None):
    supabase = get_supabase_client()
    
    query = supabase.table("tasks").select("*").eq("user_id", user["id"])
    
    if is_active is not None:
        query = query.eq("is_active", is_active)
    
    response = query.order("created_at", desc=True).execute()
    
    return [Task(**task) for task in response.data]


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID, user: CurrentUser):
    supabase = get_supabase_client()
    
    response = (
        supabase.table("tasks")
        .select("*")
        .eq("id", str(task_id))
        .eq("user_id", user["id"])
        .single()
        .execute()
    )
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    return Task(**response.data)


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: UUID, task_update: TaskUpdate, user: CurrentUser):
    supabase = get_supabase_client()
    
    # First verify the task belongs to the user
    existing = (
        supabase.table("tasks")
        .select("*")
        .eq("id", str(task_id))
        .eq("user_id", user["id"])
        .single()
        .execute()
    )
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    
    if not update_data:
        return Task(**existing.data)
    
    response = (
        supabase.table("tasks")
        .update(update_data)
        .eq("id", str(task_id))
        .execute()
    )
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update task",
        )
    
    return Task(**response.data[0])


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, user: CurrentUser):
    supabase = get_supabase_client()
    
    response = (
        supabase.table("tasks")
        .delete()
        .eq("id", str(task_id))
        .eq("user_id", user["id"])
        .execute()
    )
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    return None


@router.post("/{task_id}/execute", response_model=TaskExecution)
async def execute_task(task_id: UUID, user: CurrentUser):
    supabase = get_supabase_client()
    
    # Verify task exists and belongs to user
    task_response = (
        supabase.table("tasks")
        .select("*")
        .eq("id", str(task_id))
        .eq("user_id", user["id"])
        .single()
        .execute()
    )
    
    if not task_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Create execution record
    execution_data = {
        "task_id": str(task_id),
        "status": "pending",
    }
    
    response = supabase.table("task_executions").insert(execution_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create execution",
        )
    
    # TODO: Trigger Temporal workflow for actual execution
    
    return TaskExecution(**response.data[0])


@router.get("/{task_id}/executions", response_model=list[TaskExecution])
async def get_task_executions(task_id: UUID, user: CurrentUser, limit: int = 100):
    supabase = get_supabase_client()
    
    # Verify task belongs to user
    task_response = (
        supabase.table("tasks")
        .select("id")
        .eq("id", str(task_id))
        .eq("user_id", user["id"])
        .single()
        .execute()
    )
    
    if not task_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Get executions
    response = (
        supabase.table("task_executions")
        .select("*")
        .eq("task_id", str(task_id))
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    
    return [TaskExecution(**execution) for execution in response.data]