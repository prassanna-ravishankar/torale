#!/usr/bin/env python3
"""Integration test for Gemini grounded search support"""

import asyncio
import os

import pytest
from dotenv import load_dotenv

load_dotenv()


async def test_gemini_integration():
    from torale.executors.grounded_search import GroundedSearchExecutor

    # Check if Google API key is configured
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Add your Google API key to .env file")
        pytest.skip("GOOGLE_API_KEY not configured")

    print(f"✅ Google API key found: {google_api_key[:20]}...")

    # Initialize executor
    executor = GroundedSearchExecutor()
    print("✅ Grounded search executor initialized")

    # Test configuration
    config = {
        "search_query": "What is 2+2?",
        "condition_description": "A numerical answer is provided",
        "model": "gemini-2.0-flash-exp",
    }

    if not executor.validate_config(config):
        print("❌ Configuration validation failed")
        return False

    print("✅ Configuration valid")

    # Execute test
    try:
        print("🧪 Testing Gemini grounded search...")
        result = await executor.execute(config)

        if result.get("success"):
            print(f"✅ Gemini answer: {result.get('answer', '')[:100]}...")
            print(f"✅ Condition met: {result.get('condition_met')}")
            print(f"✅ Sources found: {len(result.get('grounding_sources', []))}")
            return True
        else:
            print(f"❌ Execution failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exception during execution: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_gemini_executor():
    """Pytest version of the Gemini integration test"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        pytest.skip("GOOGLE_API_KEY not configured")

    from torale.executors.grounded_search import GroundedSearchExecutor

    executor = GroundedSearchExecutor()

    assert executor.client is not None, "Gemini client should be initialized"

    config = {
        "search_query": "What is the capital of France?",
        "condition_description": "A city name is provided",
        "model": "gemini-2.0-flash-exp",
    }

    result = await executor.execute(config)

    # Skip if quota exhausted or API unavailable (common in CI)
    if not result.get("success"):
        error = result.get("error", "")
        if "RESOURCE_EXHAUSTED" in str(error) or "429" in str(error):
            pytest.skip(f"Gemini API quota exhausted: {error}")
        elif "UNAVAILABLE" in str(error) or "503" in str(error):
            pytest.skip(f"Gemini API unavailable: {error}")

    assert result.get("success") is True, f"Execution failed: {result.get('error')}"
    assert result.get("answer"), "Response should have answer"
    assert result.get("condition_met") is not None, "Should have condition_met field"
    assert isinstance(result.get("grounding_sources"), list), "Should have grounding sources list"


if __name__ == "__main__":
    success = asyncio.run(test_gemini_integration())
    if success:
        print("\n🎉 Gemini grounded search working correctly!")
    else:
        print("\n💥 Gemini grounded search needs debugging")
