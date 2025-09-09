from datetime import datetime
from uuid import UUID

from temporalio import activity

from torale.core.database import get_supabase_client
from torale.core.models import TaskStatus
from torale.executors.llm_text import LLMTextExecutor


@activity.defn
async def execute_task(task_id: str, execution_id: str) -> dict:
    supabase = get_supabase_client()
    
    # Get task details
    task_response = (
        supabase.table("tasks")
        .select("*")
        .eq("id", task_id)
        .single()
        .execute()
    )
    
    if not task_response.data:
        raise ValueError(f"Task {task_id} not found")
    
    task = task_response.data
    
    # Update execution status to running
    supabase.table("task_executions").update({
        "status": TaskStatus.RUNNING.value,
    }).eq("id", execution_id).execute()
    
    # Execute based on executor type
    try:
        if task["executor_type"] == "llm_text":
            executor = LLMTextExecutor()
            result = await executor.execute(task["config"])
        else:
            raise ValueError(f"Unsupported executor type: {task['executor_type']}")
        
        # Update execution with success
        supabase.table("task_executions").update({
            "status": TaskStatus.SUCCESS.value,
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", execution_id).execute()
        
        return result
        
    except Exception as e:
        # Update execution with failure
        supabase.table("task_executions").update({
            "status": TaskStatus.FAILED.value,
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", execution_id).execute()
        
        raise


@activity.defn
async def send_notification(user_id: str, task_name: str, result: dict) -> None:
    # TODO: Implement notification sending via NotificationAPI
    print(f"Would send notification to user {user_id} for task '{task_name}'")
    print(f"Result: {result}")
    pass