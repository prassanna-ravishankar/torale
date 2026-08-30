"""Admin waitlist-management routes."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from webwhen.access import ClerkUser, require_admin
from webwhen.api.routers.admin_routes.common import serialize_waitlist_row
from webwhen.core.database import Database, get_db

router = APIRouter()


@router.get("/waitlist")
async def list_waitlist(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
    status_filter: str | None = None,
):
    """
    List all waitlist entries (admin only).

    Optionally filter by status: pending, invited, or converted.
    """
    query = "SELECT id, email, created_at, status, invited_at, notes FROM waitlist"
    params: list[Any] = []
    if status_filter:
        query += " WHERE status = $1"
        params.append(status_filter)
    query += " ORDER BY created_at ASC"
    rows = await db.fetch_all(query, *params)

    return [serialize_waitlist_row(row) for row in rows]


@router.get("/waitlist/stats")
async def get_waitlist_stats(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Get waitlist statistics (admin only).

    Returns counts by status and recent growth.
    """
    row = await db.fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'invited') as invited,
            COUNT(*) FILTER (WHERE status = 'converted') as converted,
            COUNT(*) as total
        FROM waitlist
        """
    )

    return {
        "pending": row["pending"] or 0,
        "invited": row["invited"] or 0,
        "converted": row["converted"] or 0,
        "total": row["total"] or 0,
    }


class UpdateWaitlistEntryRequest(BaseModel):
    """Request model for updating a waitlist entry."""

    status: Literal["pending", "invited", "converted"] | None = None
    notes: str | None = None


@router.patch("/waitlist/{entry_id}")
async def update_waitlist_entry(
    entry_id: UUID,
    data: UpdateWaitlistEntryRequest,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Update waitlist entry (admin only).

    Used to mark entries as invited or add notes.
    """
    updates = []
    params: list[Any] = [entry_id]  # $1 = entry_id
    param_idx = 1

    if data.status is not None:
        param_idx += 1
        updates.append(f"status = ${param_idx}")
        params.append(data.status)
        if data.status == "invited":
            param_idx += 1
            updates.append(f"invited_at = ${param_idx}")
            params.append(datetime.now(UTC))

    if data.notes is not None:
        param_idx += 1
        updates.append(f"notes = ${param_idx}")
        params.append(data.notes)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided",
        )

    row = await db.fetch_one(
        f"""
        UPDATE waitlist
        SET {", ".join(updates)}
        WHERE id = $1
        RETURNING id, email, created_at, status, invited_at, notes
        """,
        *params,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    return serialize_waitlist_row(row)


@router.delete("/waitlist/{entry_id}")
async def delete_waitlist_entry(
    entry_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Delete waitlist entry (admin only).

    Use when removing spam or invalid entries.
    """
    row = await db.fetch_one(
        "DELETE FROM waitlist WHERE id = $1 RETURNING id",
        entry_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    return {"status": "deleted"}
