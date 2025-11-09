"""Test OpenAI web search approach."""

from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✓ Loaded .env\n")

from approaches.openai_websearch import evaluate, retrieve  # noqa: E402

# Test retrieve with web search
print("Testing OpenAI Responses API with web search...")
try:
    result = retrieve("When is the next iPhone being released?")
    print("✓ Retrieve works!")
    print(f"  Answer: {result['answer'][:150]}...")
    print(f"  Sources: {len(result['sources'])}")
    for i, source in enumerate(result["sources"][:3]):
        print(f"    {i + 1}. {source['title'][:60]}...")
        print(f"       {source['url']}")
    print(f"  Usage: {result['usage']}\n")

    # Test evaluate
    print("Testing evaluate...")
    eval_result = evaluate(
        result["answer"], "A specific release date or month has been officially announced"
    )
    print("✓ Evaluate works!")
    print(f"  Condition met: {eval_result['condition_met']}")
    print(f"  Reasoning: {eval_result['reasoning'][:150]}...")
    print(f"  Usage: {eval_result['usage']}\n")

    print("🎉 OpenAI web search approach is fully functional!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
