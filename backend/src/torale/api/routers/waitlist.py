"""Public waitlist endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from torale.api.users import get_async_session

router = APIRouter()


class JoinWaitlistRequest(BaseModel):
    """Request to join waitlist."""

    email: EmailStr


class JoinWaitlistResponse(BaseModel):
    """Response after joining waitlist."""

    message: str
    position: int | None


@router.post("/public/waitlist", response_model=JoinWaitlistResponse)
async def join_waitlist(
    request: JoinWaitlistRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Join the waitlist (public endpoint, no auth required).

    Users provide their email and are added to the waitlist queue.
    """
    try:
        # Insert into waitlist
        await session.execute(
            text("""
            INSERT INTO waitlist (email, created_at, status)
            VALUES (:email, :created_at, 'pending')
            RETURNING id
            """),
            {
                "email": request.email.lower(),
                "created_at": datetime.now(UTC),
            },
        )
        await session.commit()

        # Get position in queue
        position_result = await session.execute(
            text("""
            SELECT COUNT(*) + 1 as position
            FROM waitlist
            WHERE status = 'pending' AND created_at < (
                SELECT created_at FROM waitlist WHERE email = :email
            )
            """),
            {"email": request.email.lower()},
        )
        position = position_result.scalar()

        return JoinWaitlistResponse(
            message="You've been added to the waitlist! We'll notify you when a spot opens up.",
            position=position,
        )

    except Exception as e:
        if "unique constraint" in str(e).lower():
            # Email already on waitlist
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email is already on the waitlist.",
            ) from e
        raise
