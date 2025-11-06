#!/usr/bin/env python3
"""Quick smoke test - run this to verify basic functionality before full testing"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_environment():
    """Check if environment is set up correctly"""
    print(f"{BLUE}Checking environment...{RESET}")

    issues = []

    # Check for .env file
    if not Path(".env").exists():
        issues.append("No .env file found - run: cp .env.example .env")

    # Check for at least one API key
    has_llm = any(
        [os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY"), os.getenv("GOOGLE_API_KEY")]
    )

    if not has_llm:
        issues.append("No LLM API keys configured in .env")

    if issues:
        print(f"{RED}Environment issues found:{RESET}")
        for issue in issues:
            print(f"  {RED}✗ {issue}{RESET}")
        return False
    else:
        print(f"{GREEN}✓ Environment OK{RESET}")
        return True


async def test_imports():
    """Test that all modules can be imported"""
    print(f"\n{BLUE}Testing imports...{RESET}")

    try:
        from torale.api.main import app  # noqa: F401
        from torale.core import config, models  # noqa: F401
        from torale.executors.grounded_search import GroundedSearchExecutor  # noqa: F401

        print(f"{GREEN}✓ All imports successful{RESET}")
        return True
    except ImportError as e:
        print(f"{RED}✗ Import failed: {e}{RESET}")
        print(f"{YELLOW}  Run: uv sync{RESET}")
        import traceback

        traceback.print_exc()
        return False


async def test_config():
    """Test configuration loading"""
    print(f"\n{BLUE}Testing configuration...{RESET}")

    try:
        from torale.core.config import settings

        # Check database URL
        if settings.database_url:
            print(f"{GREEN}✓ Database URL configured{RESET}")
        else:
            print(f"{YELLOW}⚠ Database URL not configured{RESET}")

        # Show which LLMs are configured
        if settings.google_api_key:
            print(f"{GREEN}✓ Google API key configured (required){RESET}")
        else:
            print(f"{YELLOW}⚠ Google API key not configured (required for grounded search){RESET}")

        return True
    except Exception as e:
        print(f"{RED}✗ Config error: {e}{RESET}")
        import traceback

        traceback.print_exc()
        return False


async def test_executor_init():
    """Test that executor can be initialized"""
    print(f"\n{BLUE}Testing executor initialization...{RESET}")

    if not os.getenv("GOOGLE_API_KEY"):
        print(f"{YELLOW}⚠ Grounded search executor skipped (no GOOGLE_API_KEY){RESET}")
        print(f"{YELLOW}  Add GOOGLE_API_KEY to .env to test{RESET}")
        return True

    try:
        from torale.executors.grounded_search import GroundedSearchExecutor

        executor = GroundedSearchExecutor()
        print(f"{GREEN}✓ Grounded search executor initialized{RESET}")

        # Try a quick execution
        print(f"{BLUE}  Running quick test...{RESET}")
        result = await executor.execute(
            {
                "search_query": "What is 1+1?",
                "condition_description": "A numerical answer is provided",
                "model": "gemini-2.0-flash-exp",
            }
        )

        if result.get("success"):
            print(f"{GREEN}  ✓ Grounded search execution successful!{RESET}")
            print(f"{GREEN}    Condition met: {result.get('condition_met')}{RESET}")
        else:
            print(f"{YELLOW}  ⚠ Execution failed: {result.get('error')}{RESET}")

        return True
    except Exception as e:
        print(f"{RED}✗ Executor init failed: {e}{RESET}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all quick tests"""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Torale Quick Test Suite{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    all_pass = True

    # Check environment first
    if not check_environment():
        print(f"\n{RED}Fix environment issues first!{RESET}")
        return False

    # Run tests
    all_pass &= await test_imports()
    all_pass &= await test_config()
    all_pass &= await test_executor_init()

    # Summary
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if all_pass:
        print(f"{GREEN}✅ All quick tests passed!{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print("  1. Run full executor tests: python tests/test_executors.py")
        print("  2. Start local services: docker compose up -d")
        print("  3. Run API: uv run python run_api.py")
    else:
        print(f"{YELLOW}⚠ Some tests failed - see above for details{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
