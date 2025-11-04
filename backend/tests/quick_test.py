#!/usr/bin/env python3
"""Quick smoke test - run this to verify basic functionality before full testing"""

import asyncio
import sys
import os
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
    has_llm = any([
        os.getenv("OPENAI_API_KEY"),
        os.getenv("ANTHROPIC_API_KEY"), 
        os.getenv("GOOGLE_API_KEY")
    ])
    
    if not has_llm:
        issues.append("No LLM API keys configured in .env")
    
    # Check Python version
    if sys.version_info < (3, 11):
        issues.append(f"Python 3.11+ required (you have {sys.version})")
    
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
        from torale.core import config
        from torale.core import models
        from torale.executors.llm_text import LLMTextExecutor
        from torale.api.main import app
        print(f"{GREEN}✓ All imports successful{RESET}")
        return True
    except ImportError as e:
        print(f"{RED}✗ Import failed: {e}{RESET}")
        print(f"{YELLOW}  Run: uv sync{RESET}")
        return False


async def test_config():
    """Test configuration loading"""
    print(f"\n{BLUE}Testing configuration...{RESET}")
    
    try:
        from torale.core.config import settings
        
        # Check critical settings
        if not settings.supabase_url.startswith("http"):
            print(f"{YELLOW}⚠ Supabase URL not configured{RESET}")
        else:
            print(f"{GREEN}✓ Supabase URL configured{RESET}")
        
        # Show which LLMs are configured
        llms = []
        if settings.openai_api_key:
            llms.append("OpenAI")
        if settings.anthropic_api_key:
            llms.append("Anthropic")
        if settings.google_api_key:
            llms.append("Gemini")
        
        if llms:
            print(f"{GREEN}✓ LLMs configured: {', '.join(llms)}{RESET}")
        else:
            print(f"{YELLOW}⚠ No LLMs configured{RESET}")
        
        return True
    except Exception as e:
        print(f"{RED}✗ Config error: {e}{RESET}")
        return False


async def test_executor_init():
    """Test that executor can be initialized"""
    print(f"\n{BLUE}Testing executor initialization...{RESET}")
    
    try:
        from torale.executors.llm_text import LLMTextExecutor
        
        executor = LLMTextExecutor()
        
        # Check which clients were initialized
        clients = []
        if executor.openai_client:
            clients.append("OpenAI")
        if executor.anthropic_client:
            clients.append("Anthropic")
        if executor.google_client:
            clients.append("Gemini")
        
        if clients:
            print(f"{GREEN}✓ Clients initialized: {', '.join(clients)}{RESET}")
            
            # Try a quick execution with first available client
            test_model = None
            if executor.openai_client:
                test_model = "gpt-3.5-turbo"
            elif executor.google_client:
                test_model = "gemini-2.0-flash-exp"
            elif executor.anthropic_client:
                test_model = "claude-3-haiku-20240307"
            
            if test_model:
                print(f"{BLUE}  Running quick test with {test_model}...{RESET}")
                result = await executor.execute({
                    "prompt": "Say 'test'",
                    "model": test_model,
                    "max_tokens": 5
                })
                
                if result.get("success"):
                    print(f"{GREEN}  ✓ Execution successful!{RESET}")
                else:
                    print(f"{YELLOW}  ⚠ Execution failed: {result.get('error')}{RESET}")
        else:
            print(f"{YELLOW}⚠ No LLM clients initialized (check API keys){RESET}")
        
        return True
    except Exception as e:
        print(f"{RED}✗ Executor init failed: {e}{RESET}")
        return False


async def main():
    """Run all quick tests"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Torale Quick Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
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
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_pass:
        print(f"{GREEN}✅ All quick tests passed!{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print(f"  1. Run full executor tests: python tests/test_executors.py")
        print(f"  2. Start local services: docker compose up -d")
        print(f"  3. Run API: uv run python run_api.py")
    else:
        print(f"{YELLOW}⚠ Some tests failed - see above for details{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)