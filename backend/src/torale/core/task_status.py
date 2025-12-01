"""Task status logic - derive task activity state from current data."""

from enum import Enum
from typing import TypedDict


class TaskActivityState(Enum):
    """What the task is currently DOING."""

    ACTIVE = "active"  # Monitoring on schedule
    COMPLETED = "completed"  # Auto-stopped after notify_behavior="once" success
    PAUSED = "paused"  # User manually stopped


class TaskStatusInfo(TypedDict):
    """Task status information with display metadata."""

    activity_state: TaskActivityState
    icon: str
    label: str
    color: str
    description: str


def get_task_status(is_active: bool, last_execution_condition_met: bool | None) -> TaskStatusInfo:
    """
    Derive task status from is_active and latest execution result.

    This is the single source of truth for task status across the application.
    All status display logic should use this function.

    Logic:
    - Active (is_active=true): Task is monitoring on schedule
    - Completed (is_active=false + last_execution.condition_met=true):
        Auto-stopped after notify_behavior="once" success
    - Paused (is_active=false + last_execution.condition_met=false/null):
        User manually stopped

    Args:
        is_active: Whether task is currently active (monitoring)
        last_execution_condition_met: Whether the latest execution met its condition
            (None if task never executed)

    Returns:
        TaskStatusInfo with activity state and display metadata
    """
    if is_active:
        return {
            "activity_state": TaskActivityState.ACTIVE,
            "icon": "🟢",
            "label": "Monitoring",
            "color": "green",
            "description": "Actively checking on schedule",
        }

    # Inactive - determine why
    if last_execution_condition_met:
        return {
            "activity_state": TaskActivityState.COMPLETED,
            "icon": "✅",
            "label": "Completed",
            "color": "blue",
            "description": "Notified once and auto-stopped",
        }

    return {
        "activity_state": TaskActivityState.PAUSED,
        "icon": "⏸️",
        "label": "Paused",
        "color": "yellow",
        "description": "Manually paused by user",
    }
