#!/usr/bin/env python3
"""Simple integration tests for LLM executors - run before full deployment"""

import asyncio
import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


async def test_executor(name: str, model: str, test_prompt: str = "Reply with exactly: Hello World") -> bool:
    """Test a single executor with the given model"""
    from torale.executors.llm_text import LLMTextExecutor
    
    print(f"\n{BLUE}Testing {name} ({model})...{RESET}")
    
    try:
        executor = LLMTextExecutor()
        
        config = {
            "prompt": test_prompt,
            "model": model,
            "max_tokens": 20,
            "temperature": 0.1  # Low temperature for consistent results
        }
        
        result = await executor.execute(config)
        
        if result.get("success"):
            content = result.get("content", "").strip()
            print(f"{GREEN}✓ {name} working!{RESET}")
            print(f"  Response: {content[:50]}...")
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"{RED}✗ {name} failed: {error}{RESET}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ {name} error: {str(e)}{RESET}")
        return False


async def test_all_executors():
    """Test all configured executors"""
    print(f"{BLUE}={'='*60}{RESET}")
    print(f"{BLUE}LLM Executor Integration Tests{RESET}")
    print(f"{BLUE}={'='*60}{RESET}")
    
    results = {}
    
    # Test OpenAI
    if os.getenv("OPENAI_API_KEY"):
        results["OpenAI"] = await test_executor("OpenAI", "gpt-3.5-turbo")
    else:
        print(f"{YELLOW}⚠ OpenAI skipped (no API key){RESET}")
        results["OpenAI"] = None
    
    # Test Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        results["Anthropic"] = await test_executor("Anthropic", "claude-3-haiku-20240307")
    else:
        print(f"{YELLOW}⚠ Anthropic skipped (no API key){RESET}")
        results["Anthropic"] = None
    
    # Test Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        results["Gemini"] = await test_executor("Gemini", "gemini-2.0-flash-exp")
    else:
        print(f"{YELLOW}⚠ Gemini skipped (no API key){RESET}")
        results["Gemini"] = None
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary:{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    total = len([r for r in results.values() if r is not None])
    passed = len([r for r in results.values() if r is True])
    
    for provider, result in results.items():
        if result is True:
            print(f"  {GREEN}✓ {provider}{RESET}")
        elif result is False:
            print(f"  {RED}✗ {provider}{RESET}")
        else:
            print(f"  {YELLOW}⊘ {provider} (not configured){RESET}")
    
    if total > 0:
        print(f"\n{BLUE}Results: {passed}/{total} providers working{RESET}")
        if passed == total:
            print(f"{GREEN}🎉 All configured providers working!{RESET}")
        elif passed > 0:
            print(f"{YELLOW}⚠ Some providers need attention{RESET}")
        else:
            print(f"{RED}❌ No providers working - check API keys{RESET}")
    else:
        print(f"\n{YELLOW}No providers configured - add API keys to .env{RESET}")
    
    return passed == total if total > 0 else False


async def test_error_handling():
    """Test that executor handles errors gracefully"""
    from torale.executors.llm_text import LLMTextExecutor
    
    print(f"\n{BLUE}Testing error handling...{RESET}")
    
    executor = LLMTextExecutor()
    
    # Test with invalid model
    result = await executor.execute({
        "prompt": "Test",
        "model": "invalid-model-xyz",
        "max_tokens": 10
    })
    
    assert result["success"] is False, "Should fail with invalid model"
    assert "error" in result, "Should include error message"
    print(f"{GREEN}✓ Error handling works correctly{RESET}")
    
    # Test with missing config
    try:
        result = await executor.execute({"prompt": "Test"})  # Missing model
        assert result["success"] is False, "Should fail with missing model"
        print(f"{GREEN}✓ Config validation works{RESET}")
    except ValueError:
        print(f"{GREEN}✓ Config validation works (raises error){RESET}")


if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(test_all_executors())
    
    # Test error handling regardless of API keys
    asyncio.run(test_error_handling())
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if success:
        print(f"{GREEN}Ready for full deployment!{RESET}")
    else:
        print(f"{YELLOW}Configure API keys in .env for full testing{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")