"""Shared serialization helpers for admin routes."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_json_field(value: Any) -> Any:
    """Parse a JSON database field while preserving malformed values."""
    if isinstance(value, str):
        try:
            return json.loads(value) if value else None
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON field: %r", value[:200])
            return value
    return value


def serialize_waitlist_row(row: Any) -> dict[str, Any]:
    """Convert a waitlist database row to the admin API representation."""
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "status": row["status"],
        "invited_at": row["invited_at"].isoformat() if row["invited_at"] else None,
        "notes": row["notes"],
    }
