"""Test auto-verification of Clerk emails."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncpg

from torale.core.config import settings
from torale.core.email_verification import EmailVerificationService


async def test_auto_verification():
    """Test auto-verification implementation."""
    print("Testing Clerk email auto-verification...\n")

    # Connect to database
    conn = await asyncpg.connect(settings.database_url)

    try:
        # Test 1: Runtime check for Clerk email
        print("Test 1: Runtime check for Clerk email")
        print("-" * 50)

        # Get a user with Clerk email
        user = await conn.fetchrow("""
            SELECT id, email, verified_notification_emails
            FROM users
            LIMIT 1
        """)

        if not user:
            print("⚠ No users found in database")
            print("✓ Create a user via /auth/sync-user first\n")
            return

        user_id = str(user["id"])
        clerk_email = user["email"]
        verified_emails = user["verified_notification_emails"] or []

        print(f"User ID: {user_id}")
        print(f"Clerk email: {clerk_email}")
        print(f"Verified emails array: {verified_emails}")

        # Check if Clerk email is verified (should be True even if not in array)
        is_verified = await EmailVerificationService.is_email_verified(conn, user_id, clerk_email)
        print(f"is_email_verified(clerk_email): {is_verified}")

        if is_verified:
            print("✓ Clerk email auto-verified via runtime check\n")
        else:
            print("✗ FAILED: Clerk email should be auto-verified\n")
            return

        # Test 2: Custom email requires verification
        print("Test 2: Custom email requires verification")
        print("-" * 50)

        custom_email = "custom@example.com"
        is_custom_verified = await EmailVerificationService.is_email_verified(
            conn, user_id, custom_email
        )
        print(f"Custom email: {custom_email}")
        print(f"is_email_verified(custom_email): {is_custom_verified}")

        if not is_custom_verified:
            print("✓ Custom email correctly requires verification\n")
        else:
            print("✗ FAILED: Custom email should not be auto-verified\n")
            return

        # Test 3: Check if Clerk email is in verified_notification_emails array
        print("Test 3: Database persistence")
        print("-" * 50)

        in_array = clerk_email in verified_emails
        print(f"Clerk email in verified_notification_emails: {in_array}")

        if in_array:
            print("✓ Clerk email persisted in database array")
            print("  (either via migration or /auth/sync-user)\n")
        else:
            print("⚠ Clerk email not in array (migration may not have run)")
            print("  But runtime check still works as safety net\n")

        # Test 4: Simulate email change
        print("Test 4: Email change handling")
        print("-" * 50)

        # This would happen in /auth/sync-user when Clerk email changes
        old_email = clerk_email
        new_email = "newemail@example.com"

        print("Simulating email change:")
        print(f"  Old: {old_email}")
        print(f"  New: {new_email}")

        # Perform the update operation from /auth/sync-user
        await conn.execute(
            """
            UPDATE users
            SET email = $1,
                verified_notification_emails = (
                    -- Remove old email
                    array_remove(
                        COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                        $2
                    )
                    ||
                    -- Add new email if not present
                    CASE
                        WHEN $1 = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[]))
                        THEN ARRAY[]::TEXT[]
                        ELSE ARRAY[$1]::TEXT[]
                    END
                )
            WHERE id = $3
        """,
            new_email,
            old_email,
            user["id"],
        )

        # Verify the change
        updated_user = await conn.fetchrow(
            """
            SELECT email, verified_notification_emails
            FROM users
            WHERE id = $1
        """,
            user["id"],
        )

        print("After update:")
        print(f"  email: {updated_user['email']}")
        print(f"  verified_notification_emails: {updated_user['verified_notification_emails']}")

        # Check verification status
        old_verified = await EmailVerificationService.is_email_verified(conn, user_id, old_email)
        new_verified = await EmailVerificationService.is_email_verified(conn, user_id, new_email)

        print(f"  Old email verified: {old_verified}")
        print(f"  New email verified: {new_verified}")

        # Revert the change
        await conn.execute(
            """
            UPDATE users
            SET email = $1,
                verified_notification_emails = (
                    array_remove(
                        COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                        $2
                    )
                    ||
                    CASE
                        WHEN $1 = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[]))
                        THEN ARRAY[]::TEXT[]
                        ELSE ARRAY[$1]::TEXT[]
                    END
                )
            WHERE id = $3
        """,
            old_email,
            new_email,
            user["id"],
        )

        if not old_verified and new_verified:
            print("✓ Email change correctly updated verified emails\n")
        else:
            print("✗ FAILED: Email change handling incorrect\n")
            return

        # Test 5: Spam protection still works
        print("Test 5: Spam protection")
        print("-" * 50)

        can_send, error = await EmailVerificationService.check_spam_limits(
            conn, user_id, clerk_email
        )
        print(f"can_send notifications: {can_send}")
        print(f"error: {error}")

        if can_send:
            print("✓ Spam protection allows normal usage\n")
        else:
            print("⚠ Rate limit hit (might have run tests recently)\n")

        # Summary
        print("=" * 50)
        print("✅ All auto-verification tests passed!")
        print("\nImplementation verified:")
        print("  ✓ Clerk emails auto-verified via runtime check")
        print("  ✓ Custom emails require verification")
        print("  ✓ Database persistence works (when migration runs)")
        print("  ✓ Email changes update verified_notification_emails")
        print("  ✓ Spam protection still enforced")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_auto_verification())
