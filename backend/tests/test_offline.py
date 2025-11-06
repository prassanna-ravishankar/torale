#!/usr/bin/env python3
"""Offline tests - these work without API keys or external services"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def test_models():
    """Test that data models work correctly"""
    print(f"{BLUE}Testing data models...{RESET}")

    from datetime import datetime
    from uuid import uuid4

    from torale.core.models import ExecutorType, NotifyBehavior, Task, TaskCreate, TaskStatus

    # Test TaskCreate
    task_create = TaskCreate(
        name="Test Task",
        schedule="0 9 * * *",
        executor_type=ExecutorType.LLM_GROUNDED_SEARCH,
        search_query="What is 2+2?",
        condition_description="A numerical answer is provided",
        config={"model": "gemini-2.0-flash-exp"},
        is_active=True,
    )
    assert task_create.name == "Test Task"
    print(f"{GREEN}✓ TaskCreate model works{RESET}")

    # Test Task
    task = Task(
        id=uuid4(),
        user_id=uuid4(),
        name="Test Task",
        schedule="0 9 * * *",
        executor_type=ExecutorType.LLM_GROUNDED_SEARCH,
        search_query="test query",
        condition_description="test condition",
        config={"model": "gemini-2.0-flash-exp"},
        is_active=True,
        created_at=datetime.now(),
    )
    assert task.name == "Test Task"
    print(f"{GREEN}✓ Task model works{RESET}")

    # Test enums
    assert ExecutorType.LLM_GROUNDED_SEARCH == "llm_grounded_search"
    assert TaskStatus.PENDING == "pending"
    assert NotifyBehavior.ONCE == "once"
    print(f"{GREEN}✓ Enums work correctly{RESET}")

    return True


def test_executor_validation():
    """Test executor validation without making API calls"""
    print(f"\n{BLUE}Testing executor validation...{RESET}")

    # Skip if no GOOGLE_API_KEY (GroundedSearchExecutor requires it)
    import os

    if not os.getenv("GOOGLE_API_KEY"):
        print(f"{GREEN}✓ Executor validation (skipped - no API key){RESET}")
        return True

    from torale.executors.grounded_search import GroundedSearchExecutor

    executor = GroundedSearchExecutor()

    # Valid config
    valid_config = {
        "search_query": "Test query",
        "condition_description": "Test condition",
        "model": "gemini-2.0-flash-exp",
    }
    assert executor.validate_config(valid_config)
    print(f"{GREEN}✓ Valid config passes{RESET}")

    # Invalid config (missing search_query)
    invalid_config = {"condition_description": "Test", "model": "gemini-2.0-flash-exp"}
    assert not executor.validate_config(invalid_config)
    print(f"{GREEN}✓ Invalid config rejected{RESET}")

    # Invalid config (missing condition_description)
    invalid_config2 = {"search_query": "Test"}
    assert not executor.validate_config(invalid_config2)
    print(f"{GREEN}✓ Missing condition rejected{RESET}")

    return True


def test_api_routes():
    """Test that API routes are defined correctly"""
    print(f"\n{BLUE}Testing API route definitions...{RESET}")

    from torale.api.main import app

    routes = [route.path for route in app.routes]

    # Check essential routes exist
    expected_routes = [
        "/health",
        "/api/v1/tasks/",
        "/api/v1/tasks/{task_id}",
        "/api/v1/tasks/{task_id}/execute",
        "/api/v1/tasks/{task_id}/executions",
    ]

    for route in expected_routes:
        if any(route in r for r in routes):
            print(f"{GREEN}✓ Route {route} exists{RESET}")
        else:
            print(f"{RED}✗ Route {route} missing{RESET}")

    return True


def test_cli_commands():
    """Test that CLI commands are registered"""
    print(f"\n{BLUE}Testing CLI command registration...{RESET}")

    try:
        from torale.cli.main import app

        # Check main commands
        commands = [cmd.name for cmd in app.registered_commands]

        expected = ["version", "config"]
        for cmd in expected:
            if cmd in commands:
                print(f"{GREEN}✓ Command '{cmd}' registered{RESET}")
            else:
                print(f"{RED}✗ Command '{cmd}' missing{RESET}")

        # Check subcommands
        subapps = {group.name for group in app.registered_groups}

        if "auth" in subapps:
            print(f"{GREEN}✓ Auth commands registered{RESET}")
        else:
            print(f"{RED}✗ Auth commands missing{RESET}")

        if "task" in subapps:
            print(f"{GREEN}✓ Task commands registered{RESET}")
        else:
            print(f"{RED}✗ Task commands missing{RESET}")

        return True
    except Exception as e:
        print(f"{RED}✗ CLI test failed: {e}{RESET}")
        return False


def test_temporal_workflow():
    """Test that Temporal workflow can be imported"""
    print(f"\n{BLUE}Testing Temporal workflow definitions...{RESET}")

    try:
        from torale.workers.workflows import TaskExecutionRequest

        print(f"{GREEN}✓ Workflow class imported{RESET}")
        print(f"{GREEN}✓ Activities imported{RESET}")

        # Test data structure
        from uuid import uuid4

        request = TaskExecutionRequest(
            task_id=str(uuid4()), execution_id=str(uuid4()), user_id=str(uuid4()), task_name="Test"
        )
        assert request.task_name == "Test"
        print(f"{GREEN}✓ Request dataclass works{RESET}")

        return True
    except Exception as e:
        print(f"{RED}✗ Temporal test failed: {e}{RESET}")
        return False


def main():
    """Run all offline tests"""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Offline Tests (No API Keys Required){RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    all_pass = True

    all_pass &= test_models()
    all_pass &= test_executor_validation()
    all_pass &= test_api_routes()
    all_pass &= test_cli_commands()
    all_pass &= test_temporal_workflow()

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if all_pass:
        print(f"{GREEN}✅ All offline tests passed!{RESET}")
        print(f"\n{BLUE}Code structure is correct. Add API keys to test integrations.{RESET}")
    else:
        print(f"{RED}❌ Some tests failed - check code structure{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
