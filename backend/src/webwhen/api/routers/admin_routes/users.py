"""Admin user and role-management routes."""

import asyncio
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from webwhen.access import ClerkUser, clerk_client, require_admin
from webwhen.core.config import settings
from webwhen.core.database import Database, get_db
from webwhen.tasks import TaskState
from webwhen.tasks.service import TaskService

router = APIRouter()
logger = logging.getLogger(__name__)


class UpdateUserRoleRequest(BaseModel):
    """Request model for updating a single user's role."""

    role: Literal["admin", "developer"] | None = Field(
        ...,
        description="User role: 'admin', 'developer', or null to remove role",
    )


class BulkUpdateUserRolesRequest(BaseModel):
    """Request model for bulk updating user roles."""

    user_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Array of user IDs to update (max 100)",
    )
    role: Literal["admin", "developer"] | None = Field(
        ...,
        description="User role: 'admin', 'developer', or null to remove role",
    )


@router.get("/users")
async def list_users(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    List all platform users with statistics and roles.

    Returns:
    - All user accounts with email and Clerk ID
    - User roles from Clerk publicMetadata
    - Signup date
    - Task count per user
    - Total execution count
    - Number of triggered conditions
    - Active/inactive status
    - Platform capacity info
    """
    rows = await db.fetch_all(
        """
        SELECT
            u.id,
            u.email,
            u.clerk_user_id,
            u.is_active,
            u.created_at,
            COUNT(DISTINCT t.id) as task_count,
            COUNT(te.id) as total_executions,
            SUM(CASE WHEN te.notification IS NOT NULL THEN 1 ELSE 0 END) as notifications_count
        FROM users u
        LEFT JOIN tasks t ON t.user_id = u.id
        LEFT JOIN task_executions te ON te.task_id = t.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """
    )

    # Batch-fetch roles from Clerk to avoid N+1 query problem
    role_map = {}
    clerk_warnings: list[str] = []
    if clerk_client:
        try:
            limit = 500
            offset = 0

            while True:
                clerk_users_response = await clerk_client.users.list_async(
                    limit=limit, offset=offset
                )

                if not clerk_users_response or not clerk_users_response.data:
                    break

                for user in clerk_users_response.data:
                    role_map[user.id] = (user.public_metadata or {}).get("role")

                if len(clerk_users_response.data) < limit:
                    break

                offset += limit

        except Exception as e:
            logger.error(f"Failed to batch-fetch users from Clerk: {e}")
            clerk_warnings.append(f"Clerk role fetch failed: {e}. Roles may be incomplete.")

    users = []
    for row in rows:
        user_data = {
            "id": str(row["id"]),
            "email": row["email"],
            "clerk_user_id": row["clerk_user_id"],
            "is_active": row["is_active"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "task_count": row["task_count"] or 0,
            "total_executions": row["total_executions"] or 0,
            "notifications_count": row["notifications_count"] or 0,
            "role": role_map.get(row["clerk_user_id"]),
        }
        users.append(user_data)

    active_users = sum(1 for u in users if u["is_active"])
    max_users = getattr(settings, "max_users", 100)

    response = {
        "users": users,
        "capacity": {
            "used": active_users,
            "total": max_users,
            "available": max_users - active_users,
        },
    }
    if clerk_warnings:
        response["warnings"] = clerk_warnings
    return response


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Manually deactivate a user account.

    This sets user.is_active = false and pauses all their active tasks via state machine.
    Frees up a seat in the capacity limit.

    Path Parameters:
    - user_id: UUID of the user to deactivate

    Returns:
    - Status confirmation with count of tasks paused
    """
    check_row = await db.fetch_one("SELECT id FROM users WHERE id = $1", user_id)
    if not check_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    active_tasks = await db.fetch_all(
        "SELECT id, state FROM tasks WHERE user_id = $1 AND state = 'active'",
        user_id,
    )

    task_service = TaskService(db=db)
    paused_count = 0
    failed_tasks = []

    for task_row in active_tasks:
        try:
            current_state = TaskState(task_row["state"])
            await task_service.pause(task_id=task_row["id"], current_state=current_state)
            paused_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": str(task_row["id"]), "error": str(e)})

    await db.execute(
        "UPDATE users SET is_active = false, updated_at = NOW() WHERE id = $1",
        user_id,
    )

    return {
        "status": "deactivated",
        "user_id": str(user_id),
        "tasks_paused": paused_count,
        "tasks_failed": failed_tasks if failed_tasks else None,
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Update a user's role in Clerk publicMetadata.

    Admins can assign roles: "admin", "developer", or null (remove role).

    Safeguards:
    - Admins cannot change their own role (prevents self-demotion)
    - Role must be one of: "admin", "developer", or null (validated by Pydantic)

    Path Parameters:
    - user_id: UUID of the user to update

    Request Body:
    - role: "admin", "developer", or null

    Returns:
    - Updated user information
    """
    role = request.role

    user_row = await db.fetch_one("SELECT clerk_user_id FROM users WHERE id = $1", user_id)
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    target_clerk_user_id = user_row["clerk_user_id"]

    if admin.clerk_user_id == target_clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )

    if target_clerk_user_id == "test_user_noauth":
        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
            "note": "Test user - role not persisted to Clerk",
        }

    if settings.webwhen_noauth:
        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
            "note": "NoAuth mode - role not persisted to Clerk",
        }

    if not clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not initialized",
        )

    try:
        await clerk_client.users.update_metadata_async(
            user_id=target_clerk_user_id,
            public_metadata={"role": role},
        )

        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        ) from e


@router.patch("/users/roles")
async def bulk_update_user_roles(
    request: BulkUpdateUserRolesRequest,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Bulk update roles for multiple users.

    Request body:
    {
        "user_ids": ["uuid1", "uuid2", ...],  # 1-100 UUIDs
        "role": "admin" | "developer" | null
    }

    Returns:
    {
        "updated": 5,
        "failed": 0,
        "errors": []
    }
    """
    user_ids = request.user_ids
    role = request.role

    if not clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not initialized",
        )

    updated_count = 0
    failed_count = 0
    errors = []

    rows = await db.fetch_all(
        "SELECT id, clerk_user_id FROM users WHERE id = ANY($1::uuid[])",
        user_ids,
    )
    user_map = {str(row["id"]): row["clerk_user_id"] for row in rows}

    clerk_users_map = {}
    if user_map:
        clerk_ids = list(user_map.values())
        clerk_ids_to_fetch = [cid for cid in clerk_ids if cid != "test_user_noauth"]

        if clerk_ids_to_fetch and not settings.webwhen_noauth:
            try:
                clerk_users_response = await clerk_client.users.list_async(
                    user_id=clerk_ids_to_fetch, limit=100
                )
                clerk_users_map = {user.id: user for user in clerk_users_response.data}
            except Exception as e:
                logger.error(f"Clerk batch fetch failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to fetch users from Clerk: {e}",
                ) from e

    update_tasks = []
    task_metadata = []

    for user_id in user_ids:
        try:
            if user_id not in user_map:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "User not found"})
                continue

            target_clerk_user_id = user_map[user_id]

            if admin.clerk_user_id == target_clerk_user_id:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "Cannot change own role"})
                continue

            if target_clerk_user_id == "test_user_noauth" or settings.webwhen_noauth:
                updated_count += 1
                continue

            clerk_user = clerk_users_map.get(target_clerk_user_id)
            if not clerk_user:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "User not found in Clerk"})
                continue

            update_coro = clerk_client.users.update_metadata_async(
                user_id=target_clerk_user_id,
                public_metadata={"role": role},
            )
            update_tasks.append(update_coro)
            task_metadata.append({"user_id": user_id})

        except Exception as e:
            failed_count += 1
            errors.append({"user_id": user_id, "error": str(e)})

    if update_tasks:
        results = await asyncio.gather(*update_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_count += 1
                errors.append({"user_id": task_metadata[i]["user_id"], "error": str(result)})
            else:
                updated_count += 1

    return {
        "updated": updated_count,
        "failed": failed_count,
        "errors": errors,
    }


# Waitlist endpoints
