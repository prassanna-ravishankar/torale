import logging

from apscheduler.triggers.cron import CronTrigger

from torale.core.database import db
from torale.scheduler.scheduler import get_scheduler

logger = logging.getLogger(__name__)

_JOB_FUNC_REF = "torale.scheduler.job:execute_task_job"


async def sync_jobs_from_database() -> None:
    """Ensure APScheduler jobs match active/paused tasks in the database.

    Runs on every startup as a consistency check. Creates missing jobs,
    removes orphaned jobs.
    """
    scheduler = get_scheduler()

    rows = await db.fetch_all(
        """SELECT id, user_id, name, schedule, state
           FROM tasks
           WHERE state IN ('active', 'paused')"""
    )

    expected_job_ids = set()

    for row in rows:
        task_id = str(row["id"])
        job_id = f"task-{task_id}"
        expected_job_ids.add(job_id)

        existing_job = scheduler.get_job(job_id)

        if existing_job is None:
            scheduler.add_job(
                _JOB_FUNC_REF,
                trigger=CronTrigger.from_crontab(row["schedule"]),
                id=job_id,
                args=[task_id, str(row["user_id"]), row["name"]],
                replace_existing=True,
            )
            if row["state"] == "paused":
                scheduler.pause_job(job_id)
            logger.info(f"Synced job {job_id} (state={row['state']})")
        else:
            if row["state"] == "paused" and existing_job.next_run_time is not None:
                scheduler.pause_job(job_id)
            elif row["state"] == "active" and existing_job.next_run_time is None:
                scheduler.resume_job(job_id)

    for job in scheduler.get_jobs():
        if job.id.startswith("task-") and job.id not in expected_job_ids:
            scheduler.remove_job(job.id)
            logger.info(f"Removed orphaned job {job.id}")
