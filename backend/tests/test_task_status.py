#!/usr/bin/env python3
"""Tests for task status logic module"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def test_task_status_active():
    """Test status calculation for active tasks"""
    print(f"{BLUE}Testing active task status...{RESET}")

    from torale.core.task_status import TaskActivityState, get_task_status

    # Active task (is_active=True)
    status = get_task_status(is_active=True, last_execution_condition_met=None)
    assert status["activity_state"] == TaskActivityState.ACTIVE
    assert status["icon"] == "🟢"
    assert status["label"] == "Monitoring"
    assert status["color"] == "green"
    print(f"{GREEN}✓ Active task (never executed) status correct{RESET}")

    # Active task with previous execution (condition not met)
    status = get_task_status(is_active=True, last_execution_condition_met=False)
    assert status["activity_state"] == TaskActivityState.ACTIVE
    assert status["icon"] == "🟢"
    print(f"{GREEN}✓ Active task (condition not met) status correct{RESET}")

    # Active task with previous execution (condition met)
    status = get_task_status(is_active=True, last_execution_condition_met=True)
    assert status["activity_state"] == TaskActivityState.ACTIVE
    assert status["icon"] == "🟢"
    print(f"{GREEN}✓ Active task (condition met but still running) status correct{RESET}")

    return True


def test_task_status_completed():
    """Test status calculation for completed tasks (auto-stopped)"""
    print(f"\n{BLUE}Testing completed task status...{RESET}")

    from torale.core.task_status import TaskActivityState, get_task_status

    # Inactive task with condition met (auto-stopped after notify_behavior="once")
    status = get_task_status(is_active=False, last_execution_condition_met=True)
    assert status["activity_state"] == TaskActivityState.COMPLETED
    assert status["icon"] == "✅"
    assert status["label"] == "Completed"
    assert status["color"] == "blue"
    assert "auto-stopped" in status["description"].lower()
    print(f"{GREEN}✓ Completed task (auto-stopped) status correct{RESET}")

    return True


def test_task_status_paused():
    """Test status calculation for paused tasks (manually stopped)"""
    print(f"\n{BLUE}Testing paused task status...{RESET}")

    from torale.core.task_status import TaskActivityState, get_task_status

    # Inactive task with condition not met (manually paused)
    status = get_task_status(is_active=False, last_execution_condition_met=False)
    assert status["activity_state"] == TaskActivityState.PAUSED
    assert status["icon"] == "⏸️"
    assert status["label"] == "Paused"
    assert status["color"] == "yellow"
    print(f"{GREEN}✓ Paused task (condition not met) status correct{RESET}")

    # Inactive task never executed (manually paused before first execution)
    status = get_task_status(is_active=False, last_execution_condition_met=None)
    assert status["activity_state"] == TaskActivityState.PAUSED
    assert status["icon"] == "⏸️"
    assert status["label"] == "Paused"
    print(f"{GREEN}✓ Paused task (never executed) status correct{RESET}")

    return True


def test_task_activity_state_enum():
    """Test TaskActivityState enum values"""
    print(f"\n{BLUE}Testing TaskActivityState enum...{RESET}")

    from torale.core.task_status import TaskActivityState

    assert TaskActivityState.ACTIVE.value == "active"
    assert TaskActivityState.COMPLETED.value == "completed"
    assert TaskActivityState.PAUSED.value == "paused"
    print(f"{GREEN}✓ TaskActivityState enum values correct{RESET}")

    # Test all states are unique
    states = [TaskActivityState.ACTIVE, TaskActivityState.COMPLETED, TaskActivityState.PAUSED]
    assert len(set(states)) == 3
    print(f"{GREEN}✓ All activity states are unique{RESET}")

    return True


def test_status_info_structure():
    """Test that status info returns all required fields"""
    print(f"\n{BLUE}Testing status info structure...{RESET}")

    from torale.core.task_status import get_task_status

    status = get_task_status(is_active=True, last_execution_condition_met=None)

    # Check all required fields exist
    required_fields = ["activity_state", "icon", "label", "color", "description"]
    for field in required_fields:
        assert field in status, f"Missing field: {field}"
        assert status[field] is not None, f"Field {field} is None"
    print(f"{GREEN}✓ All required fields present{RESET}")

    # Check field types
    assert isinstance(status["icon"], str)
    assert isinstance(status["label"], str)
    assert isinstance(status["color"], str)
    assert isinstance(status["description"], str)
    print(f"{GREEN}✓ All field types correct{RESET}")

    return True


def main():
    """Run all task_status tests"""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Task Status Module Tests{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    all_pass = True

    all_pass &= test_task_activity_state_enum()
    all_pass &= test_task_status_active()
    all_pass &= test_task_status_completed()
    all_pass &= test_task_status_paused()
    all_pass &= test_status_info_structure()

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if all_pass:
        print(f"{GREEN}✅ All task_status tests passed!{RESET}")
    else:
        print(f"{RED}❌ Some tests failed{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
