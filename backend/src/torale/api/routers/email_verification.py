"""Email verification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from torale.api.auth import CurrentUserOrTestUser
from torale.core.database import Database, get_db
from torale.core.email_verification import EmailVerificationService
from torale.notifications.novu_service import novu_service

CurrentUser = CurrentUserOrTestUser
router = APIRouter(prefix="/email-verification", tags=["email-verification"])


class VerificationRequest(BaseModel):
    """Request to send verification email."""

    email: EmailStr


class VerificationConfirm(BaseModel):
    """Confirm email verification with code."""

    email: EmailStr
    code: str


@router.post("/send")
async def send_verification_email(
    request: VerificationRequest, user: CurrentUser, db: Database = Depends(get_db)
):
    """
    Send verification code to email address.

    Required before using custom email for notifications.
    """
    conn = await db.get_connection()

    try:
        # Check if already verified
        if await EmailVerificationService.is_email_verified(conn, str(user.id), request.email):
            return {"message": "Email already verified"}

        # Create verification
        success, code, error = await EmailVerificationService.create_verification(
            conn, str(user.id), request.email
        )

        if not success:
            raise HTTPException(status_code=429, detail=error)

        # Get user name for personalization (use email prefix as fallback)
        user_row = await conn.fetchrow("SELECT first_name FROM users WHERE id = $1", user.id)
        user_name = (
            user_row["first_name"]
            if user_row and user_row["first_name"]
            else user.email.split("@")[0]
        )

        # Send verification email via Novu (or log code if not configured)
        await novu_service.send_verification_email(
            email=request.email, code=code, user_name=user_name
        )

        return {
            "message": f"Verification code sent to {request.email}",
            "expires_in_minutes": EmailVerificationService.VERIFICATION_EXPIRY_MINUTES,
        }

    finally:
        await conn.close()


@router.post("/verify")
async def verify_email_code(
    request: VerificationConfirm, user: CurrentUser, db: Database = Depends(get_db)
):
    """Verify email with code."""
    conn = await db.get_connection()

    try:
        success, error = await EmailVerificationService.verify_code(
            conn, str(user.id), request.email, request.code
        )

        if not success:
            raise HTTPException(status_code=400, detail=error)

        return {"message": "Email verified successfully"}

    finally:
        await conn.close()


@router.get("/verified-emails")
async def list_verified_emails(user: CurrentUser, db: Database = Depends(get_db)):
    """List user's verified email addresses."""
    conn = await db.get_connection()

    try:
        # Get Clerk email (always trusted)
        user_row = await conn.fetchrow(
            "SELECT email, verified_notification_emails FROM users WHERE id = $1",
            user.id,
        )

        clerk_email = user_row["email"]
        verified_emails = user_row["verified_notification_emails"] or []

        # Always include Clerk email as verified
        all_verified = list(set([clerk_email] + verified_emails))

        return {"verified_emails": all_verified, "primary_email": clerk_email}

    finally:
        await conn.close()


@router.delete("/verified-emails/{email}")
async def remove_verified_email(email: str, user: CurrentUser, db: Database = Depends(get_db)):
    """Remove email from verified list (cannot remove Clerk email)."""
    conn = await db.get_connection()

    try:
        # Get Clerk email
        clerk_email = await conn.fetchval("SELECT email FROM users WHERE id = $1", user.id)

        if email == clerk_email:
            raise HTTPException(status_code=400, detail="Cannot remove primary Clerk email")

        # Remove from verified list
        await conn.execute(
            """
            UPDATE users
            SET verified_notification_emails = array_remove(verified_notification_emails, $1)
            WHERE id = $2
            """,
            email,
            user.id,
        )

        return {"message": "Email removed from verified list"}

    finally:
        await conn.close()
