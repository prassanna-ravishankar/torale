#!/usr/bin/env python3
"""Simple integration tests for grounded search executor - run before full deployment"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


async def test_grounded_search():
    """Test grounded search executor with Gemini"""
    print(f"\n{BLUE}Testing Grounded Search Executor...{RESET}")

    if not os.getenv("GOOGLE_API_KEY"):
        print(f"{YELLOW}⚠ Gemini skipped (no API key){RESET}")
        return None

    try:
        from torale.executors.grounded_search import GroundedSearchExecutor

        executor = GroundedSearchExecutor()

        config = {
            "search_query": "What is 2+2?",
            "condition_description": "A numerical answer is provided",
            "model": "gemini-2.0-flash-exp",
        }

        result = await executor.execute(config)

        if result.get("success"):
            answer = result.get("answer", "")
            condition_met = result.get("condition_met", False)
            sources = result.get("grounding_sources", [])

            print(f"{GREEN}✓ Grounded search working!{RESET}")
            print(f"  Answer: {answer[:100]}...")
            print(f"  Condition met: {condition_met}")
            print(f"  Sources found: {len(sources)}")
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"{RED}✗ Grounded search failed: {error}{RESET}")
            return False

    except Exception as e:
        print(f"{RED}✗ Grounded search error: {str(e)}{RESET}")
        import traceback

        traceback.print_exc()
        return False


async def test_all_executors():
    """Test grounded search executor"""
    print(f"{BLUE}={'=' * 60}{RESET}")
    print(f"{BLUE}Grounded Search Executor Tests{RESET}")
    print(f"{BLUE}={'=' * 60}{RESET}")

    result = await test_grounded_search()

    # Summary
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Test Summary:{RESET}")
    print(f"{BLUE}={'=' * 60}{RESET}")

    if result is True:
        print(f"  {GREEN}✓ Grounded Search{RESET}")
        print(f"\n{GREEN}🎉 Grounded search executor working!{RESET}")
        return True
    elif result is False:
        print(f"  {RED}✗ Grounded Search{RESET}")
        print(f"\n{RED}❌ Grounded search executor failed{RESET}")
        return False
    else:
        print(f"  {YELLOW}⊘ Grounded Search (not configured){RESET}")
        print(f"\n{YELLOW}Configure GOOGLE_API_KEY in .env to test{RESET}")
        return False


async def test_error_handling():
    """Test that executor handles errors gracefully"""
    print(f"\n{BLUE}Testing error handling...{RESET}")

    if not os.getenv("GOOGLE_API_KEY"):
        print(f"{YELLOW}⚠ Error handling test skipped (no API key){RESET}")
        return

    from torale.executors.grounded_search import GroundedSearchExecutor

    executor = GroundedSearchExecutor()

    # Test with missing required fields
    try:
        result = await executor.execute(
            {
                "model": "gemini-2.0-flash-exp"
                # Missing search_query and condition_description
            }
        )
        assert result["success"] is False, "Should fail with missing fields"
        print(f"{GREEN}✓ Config validation works{RESET}")
    except ValueError:
        print(f"{GREEN}✓ Config validation works (raises error){RESET}")


if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(test_all_executors())

    # Test error handling regardless of API keys
    asyncio.run(test_error_handling())

    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if success:
        print(f"{GREEN}Ready for full deployment!{RESET}")
    else:
        print(f"{YELLOW}Configure API keys in .env for full testing{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
