"""Public waitlist endpoint."""

from datetime import UTC, datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from torale.api.rate_limiter import limiter
from torale.core.database import Database, get_db

router = APIRouter()


class JoinWaitlistRequest(BaseModel):
    """Request to join waitlist."""

    email: EmailStr


class JoinWaitlistResponse(BaseModel):
    """Response after joining waitlist."""

    message: str
    position: int | None


@router.post("/public/waitlist", response_model=JoinWaitlistResponse)
@limiter.limit("5/minute")
async def join_waitlist(
    request_data: JoinWaitlistRequest,
    request: Request,
    db: Database = Depends(get_db),
):
    """
    Join the waitlist (public endpoint, no auth required).

    Users provide their email and are added to the waitlist queue.
    """
    try:
        await db.execute(
            """
            INSERT INTO waitlist (email, created_at, status)
            VALUES ($1, $2, 'pending')
            """,
            request_data.email.lower(),
            datetime.now(UTC),
        )

        position = await db.fetch_val(
            """
            SELECT COUNT(*) + 1
            FROM waitlist
            WHERE status = 'pending' AND created_at < (
                SELECT created_at FROM waitlist WHERE email = $1
            )
            """,
            request_data.email.lower(),
        )

        return JoinWaitlistResponse(
            message="You've been added to the waitlist! We'll notify you when a spot opens up.",
            position=position,
        )

    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already on the waitlist.",
        ) from e
