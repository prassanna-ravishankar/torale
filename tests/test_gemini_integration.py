#!/usr/bin/env python3
"""Integration test for Gemini API support"""

import asyncio
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

async def test_gemini_integration():
    from torale.executors.llm_text import LLMTextExecutor
    
    # Check if Google API key is configured
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Add your Google API key to .env file")
        return False
    
    print(f"✅ Google API key found: {google_api_key[:20]}...")
    
    # Initialize executor
    executor = LLMTextExecutor()
    
    if not executor.google_client:
        print("❌ Google client not initialized")
        return False
    
    print("✅ Google client initialized")
    
    # Test configuration
    config = {
        "prompt": "Say hello in exactly 3 words",
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 10,
        "temperature": 0.7
    }
    
    if not executor.validate_config(config):
        print("❌ Configuration validation failed")
        return False
    
    print("✅ Configuration valid")
    
    # Execute test
    try:
        print("🧪 Testing Gemini execution...")
        result = await executor.execute(config)
        
        if result.get("success"):
            print(f"✅ Gemini response: {result['content']}")
            return True
        else:
            print(f"❌ Execution failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during execution: {e}")
        return False

@pytest.mark.asyncio
async def test_gemini_executor():
    """Pytest version of the Gemini integration test"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        pytest.skip("GOOGLE_API_KEY not configured")
    
    from torale.executors.llm_text import LLMTextExecutor
    executor = LLMTextExecutor()
    
    assert executor.google_client is not None, "Google client should be initialized"
    
    config = {
        "prompt": "Say hello in exactly 3 words",
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 10,
        "temperature": 0.7
    }
    
    result = await executor.execute(config)
    assert result.get("success") is True, f"Execution failed: {result.get('error')}"
    assert result.get("content"), "Response should have content"

if __name__ == "__main__":
    success = asyncio.run(test_gemini_integration())
    if success:
        print("\n🎉 Gemini integration working correctly!")
    else:
        print("\n💥 Gemini integration needs debugging")