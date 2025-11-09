"""Quick accuracy comparison across all approaches."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from approaches import gemini_grounded, openai_websearch, perplexity, stub  # noqa: E402
from harness import run_batch  # noqa: E402
from test_cases import ONCE_EXPERIMENTS  # noqa: E402

print("=" * 80)
print("ACCURACY COMPARISON - Running 10 test cases per approach")
print("=" * 80)

approaches = []

# Always include stub
approaches.append(("stub", stub.retrieve, stub.evaluate))

# Add real approaches if API keys available
if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
    approaches.append(("gemini_grounded", gemini_grounded.retrieve, gemini_grounded.evaluate))

if os.getenv("PERPLEXITY_API_KEY"):
    approaches.append(("perplexity", perplexity.retrieve, perplexity.evaluate))

if os.getenv("OPENAI_API_KEY"):
    approaches.append(("openai_websearch", openai_websearch.retrieve, openai_websearch.evaluate))

# Run comparison
results = []
for name, retrieve_fn, evaluate_fn in approaches:
    print(f"\n{'=' * 80}")
    print(f"Testing: {name}")
    print(f"{'=' * 80}")

    experiment_results = run_batch(
        experiments=ONCE_EXPERIMENTS[:10],  # Use first 10 test cases
        approach_name=name,
        retrieve_fn=retrieve_fn,
        evaluate_fn=evaluate_fn,
    )

    # Calculate summary stats from list of ExperimentResults
    accuracy = sum(r.accuracy for r in experiment_results) / len(experiment_results)
    avg_tokens = sum(r.total_tokens for r in experiment_results) / len(experiment_results)
    avg_latency = sum(r.latency_seconds for r in experiment_results) / len(experiment_results)

    results.append(
        {
            "approach": name,
            "accuracy": accuracy,
            "avg_tokens": avg_tokens,
            "avg_latency": avg_latency,
        }
    )

    print(f"\n✓ {name} complete:")
    print(f"  Accuracy: {accuracy:.1%}")
    print(f"  Avg tokens: {avg_tokens:.0f}")
    print(f"  Avg latency: {avg_latency:.2f}s")

# Print final comparison
print("\n" + "=" * 80)
print("FINAL COMPARISON")
print("=" * 80)
print(f"\n{'Approach':<20} {'Accuracy':<12} {'Avg Tokens':<12} {'Avg Latency':<12}")
print("-" * 80)

for r in sorted(results, key=lambda x: x["accuracy"], reverse=True):
    print(
        f"{r['approach']:<20} {r['accuracy']:>10.1%}  {r['avg_tokens']:>10.0f}  {r['avg_latency']:>10.2f}s"
    )

best = max(results, key=lambda x: x["accuracy"])
print("\n" + "=" * 80)
print(f"🏆 WINNER: {best['approach']} with {best['accuracy']:.1%} accuracy")
print("=" * 80)
