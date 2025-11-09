"""Quick test of harness with OpenAI web search approach."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env\n")

from approaches import openai_websearch
from harness import run_experiment
from test_cases import ONCE_EXPERIMENTS

# Test with first experiment
experiment = ONCE_EXPERIMENTS[0]
print(f"Testing: {experiment.search_query}\n")

result = run_experiment(
    experiment=experiment,
    approach_name="openai_websearch",
    retrieve_fn=openai_websearch.retrieve,
    evaluate_fn=openai_websearch.evaluate,
)

print(f"✓ Experiment complete!")
print(f"  Approach: {result.approach_name}")
print(f"  Accuracy: {result.accuracy}")
print(f"  Total tokens: {result.total_tokens}")
print(f"  Latency: {result.latency_seconds:.2f}s")
print(f"  Condition met: {result.condition_met}")
print(f"  Expected: {experiment.expected_outcome}")
print(f"\n✓ Check Langfuse for token tracking details!")
print(
    f"  https://cloud.langfuse.com/project/cm5lxo2hu00016p79v4x0rwq7/traces"
)
