from .scheduler import get_scheduler

# APScheduler resolves this string reference at runtime, avoiding circular imports.
# This is how APScheduler serializes jobs to the database.
JOB_FUNC_REF = "torale.scheduler.job:execute_task_job"

__all__ = ["get_scheduler", "JOB_FUNC_REF"]
