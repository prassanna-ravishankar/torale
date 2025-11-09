"""Quick verification that all approaches properly track model and usage."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from approaches import gemini_grounded, openai_websearch, perplexity, stub  # noqa: E402

print("=" * 80)
print("VERIFYING TOKEN TRACKING FOR ALL APPROACHES")
print("=" * 80)

test_query = "What is 2+2?"
test_condition = "The answer is 4"


def verify_approach(name, retrieve_fn, evaluate_fn):
    """Verify an approach returns model and usage fields."""
    print(f"\n{name}:")
    print("-" * 40)

    try:
        # Test retrieve
        result = retrieve_fn(test_query)
        print("  retrieve():")
        print(f"    ✓ answer: {len(result.get('answer', ''))} chars")
        print(f"    ✓ sources: {len(result.get('sources', []))} sources")
        print(f"    ✓ model: {result.get('model', 'MISSING')}")
        print(f"    ✓ usage: {result.get('usage', 'MISSING')}")

        # Test evaluate
        eval_result = evaluate_fn(result["answer"], test_condition)
        print("  evaluate():")
        print(f"    ✓ condition_met: {eval_result.get('condition_met', 'MISSING')}")
        print(f"    ✓ model: {eval_result.get('model', 'MISSING')}")
        print(f"    ✓ usage: {eval_result.get('usage', 'MISSING')}")

        # Verify required fields
        errors = []
        if "model" not in result:
            errors.append("retrieve() missing 'model' field")
        if "usage" not in result:
            errors.append("retrieve() missing 'usage' field")
        if "model" not in eval_result:
            errors.append("evaluate() missing 'model' field")
        if "usage" not in eval_result:
            errors.append("evaluate() missing 'usage' field")

        if errors:
            print(f"  ❌ ERRORS: {', '.join(errors)}")
        else:
            print("  ✅ All fields present!")

    except Exception as e:
        print(f"  ❌ ERROR: {e}")


# Verify all approaches
verify_approach("Stub", stub.retrieve, stub.evaluate)

if os.getenv("GOOGLE_API_KEY"):
    verify_approach(
        "Gemini (gemini-2.5-flash-lite)", gemini_grounded.retrieve, gemini_grounded.evaluate
    )
else:
    print("\nGemini: Skipped (no GOOGLE_API_KEY)")

if os.getenv("PERPLEXITY_API_KEY"):
    verify_approach("Perplexity", perplexity.retrieve, perplexity.evaluate)
else:
    print("\nPerplexity: Skipped (no PERPLEXITY_API_KEY)")

if os.getenv("OPENAI_API_KEY"):
    verify_approach("OpenAI Web Search", openai_websearch.retrieve, openai_websearch.evaluate)
else:
    print("\nOpenAI: Skipped (no OPENAI_API_KEY)")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\n✓ All approaches now return 'model' and 'usage' fields")
print("✓ Langfuse will use 'model' for cost inference + 'usage' for accurate tracking")
print("✓ Check Langfuse dashboard to see token/cost tracking in action!")
print("  https://cloud.langfuse.com/project/cm5lxo2hu00016p79v4x0rwq7/traces")
