"""Admin console API assembled from domain-specific routers.

Imports below preserve the module's historical callable/model surface for code
that invokes handlers directly, while route implementations live with their
own domain.
"""

from fastapi import APIRouter

from webwhen.api.routers.admin_routes.connectors import (
    ConnectorResetResponse,
    admin_reset_connectors,
)
from webwhen.api.routers.admin_routes.connectors import (
    router as connectors_router,
)
from webwhen.api.routers.admin_routes.observability import (
    get_platform_stats,
    list_all_queries,
    list_recent_errors,
    list_recent_executions,
    list_scheduler_jobs,
)
from webwhen.api.routers.admin_routes.observability import (
    router as observability_router,
)
from webwhen.api.routers.admin_routes.tasks import (
    AdminTaskStateUpdateRequest,
    admin_execute_task,
    admin_update_task_state,
    reset_task_history,
)
from webwhen.api.routers.admin_routes.tasks import (
    router as tasks_router,
)
from webwhen.api.routers.admin_routes.users import (
    BulkUpdateUserRolesRequest,
    UpdateUserRoleRequest,
    bulk_update_user_roles,
    deactivate_user,
    list_users,
    update_user_role,
)
from webwhen.api.routers.admin_routes.users import (
    router as users_router,
)
from webwhen.api.routers.admin_routes.waitlist import (
    UpdateWaitlistEntryRequest,
    delete_waitlist_entry,
    get_waitlist_stats,
    list_waitlist,
    update_waitlist_entry,
)
from webwhen.api.routers.admin_routes.waitlist import (
    router as waitlist_router,
)

router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)
router.include_router(observability_router)
router.include_router(users_router)
router.include_router(waitlist_router)
router.include_router(tasks_router)
router.include_router(connectors_router)

__all__ = [
    "AdminTaskStateUpdateRequest",
    "BulkUpdateUserRolesRequest",
    "ConnectorResetResponse",
    "UpdateUserRoleRequest",
    "UpdateWaitlistEntryRequest",
    "admin_execute_task",
    "admin_reset_connectors",
    "admin_update_task_state",
    "bulk_update_user_roles",
    "deactivate_user",
    "delete_waitlist_entry",
    "get_platform_stats",
    "get_waitlist_stats",
    "list_all_queries",
    "list_recent_errors",
    "list_recent_executions",
    "list_scheduler_jobs",
    "list_users",
    "list_waitlist",
    "reset_task_history",
    "router",
    "update_user_role",
    "update_waitlist_entry",
]
