import logging
from datetime import UTC, datetime, timedelta

from apscheduler.triggers.date import DateTrigger

from torale.core.database import db
from torale.scheduler import JOB_FUNC_REF
from torale.scheduler.scheduler import get_scheduler

logger = logging.getLogger(__name__)


async def reap_stale_executions() -> None:
    """Mark executions stuck in 'running' state for >30 minutes as failed."""
    result = await db.fetch_all(
        """UPDATE task_executions
           SET status = 'failed',
               error_message = 'Reaped: execution stuck in running state',
               completed_at = $1
           WHERE status = 'running'
             AND started_at < $1 - INTERVAL '30 minutes'
           RETURNING id""",
        datetime.now(UTC),
    )
    if result:
        logger.warning(f"Reaped {len(result)} stale executions stuck in running state")


async def sync_jobs_from_database() -> None:
    """Ensure APScheduler jobs match active/paused tasks in the database.

    Runs on every startup as a consistency check. Creates missing jobs,
    removes orphaned jobs.
    """
    scheduler = get_scheduler()

    rows = await db.fetch_all(
        """SELECT id, user_id, name, next_run, state
           FROM tasks
           WHERE state IN ('active', 'paused')"""
    )

    expected_job_ids = set()
    failed_count = 0

    now = datetime.now(UTC)

    for row in rows:
        try:
            task_id = str(row["id"])
            job_id = f"task-{task_id}"
            expected_job_ids.add(job_id)

            existing_job = scheduler.get_job(job_id)

            # Use next_run from DB; fallback to now + 24h if null
            next_run = row["next_run"]
            if next_run is None or next_run <= now:
                next_run = now + timedelta(hours=24)

            if existing_job is None:
                scheduler.add_job(
                    JOB_FUNC_REF,
                    trigger=DateTrigger(run_date=next_run),
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
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to sync job for task {row['id']}: {e}", exc_info=True)
            continue

    for job in scheduler.get_jobs():
        if job.id.startswith("task-") and job.id not in expected_job_ids:
            scheduler.remove_job(job.id)
            logger.info(f"Removed orphaned job {job.id}")

    if failed_count:
        logger.warning(f"Job sync completed with {failed_count} failures out of {len(rows)} tasks")
    else:
        logger.info(f"Job sync completed: {len(rows)} tasks synced, 0 failures")
