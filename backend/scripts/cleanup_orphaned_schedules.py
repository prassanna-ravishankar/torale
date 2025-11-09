#!/usr/bin/env python3
"""
Cleanup script for orphaned Temporal schedules.

Finds and deletes Temporal schedules for tasks that no longer exist in the database.
This can happen if schedule deletion fails but the task gets deleted from the database.

Usage:
    # Dry run (default) - shows what would be deleted
    uv run python scripts/cleanup_orphaned_schedules.py

    # Actually delete orphaned schedules
    uv run python scripts/cleanup_orphaned_schedules.py --delete

    # Cleanup specific task
    uv run python scripts/cleanup_orphaned_schedules.py --task-id <uuid> --delete
"""

import argparse
import asyncio
import sys
from uuid import UUID

import asyncpg
from temporalio.client import Client

from torale.core.config import settings


async def get_temporal_client() -> Client:
    """Get a Temporal client with proper authentication."""
    if settings.temporal_api_key:
        return await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            tls=True,
            api_key=settings.temporal_api_key,
        )
    else:
        return await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )


async def get_db_connection():
    """Get a database connection."""
    return await asyncpg.connect(settings.database_url)


async def cleanup_orphaned_schedules(dry_run: bool = True, specific_task_id: str | None = None):
    """
    Find and optionally delete orphaned Temporal schedules.

    Args:
        dry_run: If True, only report what would be deleted
        specific_task_id: If provided, only check this specific task
    """
    client = await get_temporal_client()
    conn = await get_db_connection()

    try:
        # Get all schedules from Temporal
        schedules = []
        async for schedule in client.list_schedules():
            schedule_id = schedule.id
            # Only process our task schedules (format: schedule-{task_id})
            if schedule_id.startswith("schedule-"):
                schedules.append(schedule_id)

        print(f"Found {len(schedules)} task schedules in Temporal")

        # Filter to specific task if requested
        if specific_task_id:
            specific_schedule_id = f"schedule-{specific_task_id}"
            schedules = [s for s in schedules if s == specific_schedule_id]
            print(f"Filtering to specific task: {specific_task_id}")

        # Check which schedules are orphaned
        if not schedules:
            print("\nNo schedules found!")
            return

        # Extract task IDs from schedule IDs and build mapping
        task_ids_to_check = []
        schedule_map = {}
        for schedule_id in schedules:
            task_id_str = schedule_id.replace("schedule-", "")
            try:
                task_id = UUID(task_id_str)
                task_ids_to_check.append(task_id)
                schedule_map[str(task_id)] = schedule_id
            except ValueError:
                print(f"WARNING: Invalid UUID in schedule ID: {schedule_id}")
                continue

        if not task_ids_to_check:
            print("\nNo valid task schedules found to check.")
            return

        # Fetch all existing task IDs from the database in a single query
        existing_task_rows = await conn.fetch(
            "SELECT id FROM tasks WHERE id = ANY($1::uuid[])", task_ids_to_check
        )
        existing_task_ids = {str(row["id"]) for row in existing_task_rows}

        # Find orphaned schedules by comparing sets
        orphaned_task_ids = {str(tid) for tid in task_ids_to_check} - existing_task_ids
        orphaned = sorted([(schedule_map[task_id], task_id) for task_id in orphaned_task_ids])

        print(f"\nFound {len(orphaned)} orphaned schedules:")
        for schedule_id, task_id in orphaned:
            print(f"  - {schedule_id} (task {task_id} deleted)")

        # Delete orphaned schedules if not dry run
        if orphaned and not dry_run:
            print(f"\nDeleting {len(orphaned)} orphaned schedules...")
            deleted = 0
            failed = 0

            for schedule_id, _task_id in orphaned:
                try:
                    schedule_handle = client.get_schedule_handle(schedule_id)
                    await schedule_handle.delete()
                    print(f"  ✓ Deleted {schedule_id}")
                    deleted += 1
                except Exception as e:
                    print(f"  ✗ Failed to delete {schedule_id}: {e}")
                    failed += 1

            print(f"\nResults: {deleted} deleted, {failed} failed")
        elif orphaned:
            print("\n[DRY RUN] Run with --delete to actually remove these schedules")
        else:
            print("\nNo orphaned schedules found!")

    finally:
        await conn.close()
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="Cleanup orphaned Temporal schedules")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete orphaned schedules (default is dry run)",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Only check/delete schedule for specific task ID",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Temporal Schedule Cleanup")
    print("=" * 60)
    print(f"Mode: {'DELETE' if args.delete else 'DRY RUN'}")
    print(f"Temporal: {settings.temporal_host}")
    print(f"Namespace: {settings.temporal_namespace}")
    print("=" * 60)
    print()

    try:
        await cleanup_orphaned_schedules(dry_run=not args.delete, specific_task_id=args.task_id)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
