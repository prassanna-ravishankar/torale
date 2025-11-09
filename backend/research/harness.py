"""
Research harness for comparing grounded search approaches.

Usage:
    python harness.py

To install research dependencies:
    cd backend && uv sync --extra research
"""

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langfuse import Langfuse
from pydantic import BaseModel

# Load environment variables from project root .env
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Experiment(BaseModel):
    """A single test case for grounded search evaluation."""

    search_query: str
    condition_description: str
    expected_outcome: bool | None  # None = dynamic ground truth (e.g., weather)
    notify_behavior: Literal["once", "always", "track_state"] = "once"
    category: str  # e.g., "product_release", "availability", "boolean_fact", "weather"


class ExperimentResult(BaseModel):
    """Results from running a single experiment."""

    experiment: dict
    approach_name: str
    answer: str
    sources: list
    condition_met: bool
    reasoning: str
    total_tokens: int
    latency_seconds: float
    accuracy: bool  # condition_met == expected_outcome
    timestamp: str


# Initialize Langfuse client
# Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in environment
langfuse = Langfuse()


def run_experiment(
    experiment: Experiment,
    retrieve_fn: Callable[[str], dict],
    evaluate_fn: Callable[[str, str], dict],
    approach_name: str = "unnamed",
) -> ExperimentResult:
    """
    Run a single experiment with the given retrieve and evaluate functions.

    Args:
        experiment: The test case to run
        retrieve_fn: Function that takes a query and returns {"answer": str, "sources": list, "tokens": int}
        evaluate_fn: Function that takes (answer, condition) and returns {"condition_met": bool, "reasoning": str, "tokens": int}
        approach_name: Name of the approach (for logging)

    Returns:
        ExperimentResult with all metrics
    """
    start_time = time.time()

    # Start root span (trace) using context manager
    with langfuse.start_as_current_span(
        name=f"{approach_name}: {experiment.search_query[:50]}",
        metadata={
            "approach": approach_name,
            "category": experiment.category,
            "notify_behavior": experiment.notify_behavior,
        },
    ) as root_span:
        # Set trace-level attributes
        root_span.update_trace(tags=[approach_name, experiment.category])

        # Step 1: Retrieve (use generation span for LLM calls with proper token tracking)
        with langfuse.start_as_current_generation(
            name="retrieve",
            input={"query": experiment.search_query},
            model=None,  # Will update after getting result
        ) as retrieve_span:
            retrieve_result = retrieve_fn(experiment.search_query)

            # Update with model and usage_details (Langfuse uses model for cost inference)
            update_kwargs = {"output": retrieve_result}

            if "model" in retrieve_result:
                update_kwargs["model"] = retrieve_result["model"]

            if "usage" in retrieve_result:
                update_kwargs["usage_details"] = retrieve_result["usage"]
            elif "tokens" in retrieve_result:
                # Fallback for old format
                update_kwargs["metadata"] = {"tokens": retrieve_result["tokens"]}

            retrieve_span.update(**update_kwargs)

        # Step 2: Evaluate (use generation span for LLM calls)
        with langfuse.start_as_current_generation(
            name="evaluate",
            input={
                "answer": retrieve_result["answer"],
                "condition": experiment.condition_description,
            },
            model=None,  # Will update after getting result
        ) as evaluate_span:
            evaluate_result = evaluate_fn(
                retrieve_result["answer"], experiment.condition_description
            )

            # Update with model and usage_details
            update_kwargs = {"output": evaluate_result}

            if "model" in evaluate_result:
                update_kwargs["model"] = evaluate_result["model"]

            if "usage" in evaluate_result:
                update_kwargs["usage_details"] = evaluate_result["usage"]
            elif "tokens" in evaluate_result:
                # Fallback for old format
                update_kwargs["metadata"] = {"tokens": evaluate_result["tokens"]}

            evaluate_span.update(**update_kwargs)

        latency = time.time() - start_time

        # Calculate total tokens from usage dicts or fallback to old format
        retrieve_total = retrieve_result.get("usage", {}).get("total")
        retrieve_tokens = (
            retrieve_total if retrieve_total is not None else retrieve_result.get("tokens", 0)
        )
        evaluate_total = evaluate_result.get("usage", {}).get("total")
        evaluate_tokens = (
            evaluate_total if evaluate_total is not None else evaluate_result.get("tokens", 0)
        )
        total_tokens = retrieve_tokens + evaluate_tokens

        # Handle dynamic ground truth for real-time checks (like weather)
        expected = experiment.expected_outcome
        if expected is None:
            from dynamic_gt import get_dynamic_ground_truth

            expected = get_dynamic_ground_truth(experiment)
            # Show resolved GT in output for transparency
            print(f"  Dynamic GT resolved: {expected}")

        accuracy = evaluate_result["condition_met"] == expected

        # Update root span with final metrics
        root_span.update(
            output={
                "condition_met": evaluate_result["condition_met"],
                "accuracy": accuracy,
            },
            metadata={
                "total_tokens": total_tokens,
                "latency_seconds": latency,
                "expected": experiment.expected_outcome,
                "actual": evaluate_result["condition_met"],
            },
        )

    result = ExperimentResult(
        experiment=experiment.model_dump(),
        approach_name=approach_name,
        answer=retrieve_result["answer"],
        sources=retrieve_result.get("sources", []),
        condition_met=evaluate_result["condition_met"],
        reasoning=evaluate_result.get("reasoning", ""),
        total_tokens=total_tokens,
        latency_seconds=latency,
        accuracy=accuracy,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    return result


def run_batch(
    experiments: list[Experiment],
    retrieve_fn: Callable[[str], dict],
    evaluate_fn: Callable[[str, str], dict],
    approach_name: str = "unnamed",
) -> list[ExperimentResult]:
    """
    Run a batch of experiments and print summary statistics.

    Args:
        experiments: List of experiments to run
        retrieve_fn: Retrieval function
        evaluate_fn: Evaluation function
        approach_name: Name of the approach

    Returns:
        List of ExperimentResults
    """
    print(f"\n{'=' * 80}")
    print(f"Running {len(experiments)} experiments with approach: {approach_name}")
    print(f"{'=' * 80}\n")

    results = []
    for i, experiment in enumerate(experiments, 1):
        print(f"[{i}/{len(experiments)}] {experiment.search_query[:60]}...")
        result = run_experiment(experiment, retrieve_fn, evaluate_fn, approach_name)
        results.append(result)

        # Print result
        status = "✓" if result.accuracy else "✗"
        print(
            f"  {status} Expected: {experiment.expected_outcome}, "
            f"Got: {result.condition_met}, "
            f"Tokens: {result.total_tokens}, "
            f"Time: {result.latency_seconds:.2f}s\n"
        )

    # Calculate summary statistics
    accuracy = sum(r.accuracy for r in results) / len(results) * 100
    avg_tokens = sum(r.total_tokens for r in results) / len(results)
    avg_latency = sum(r.latency_seconds for r in results) / len(results)
    total_tokens = sum(r.total_tokens for r in results)

    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {approach_name}")
    print(f"{'=' * 80}")
    print(f"Accuracy:      {accuracy:.1f}% ({sum(r.accuracy for r in results)}/{len(results)})")
    print(f"Total tokens:  {total_tokens}")
    print(f"Avg tokens:    {avg_tokens:.1f}")
    print(f"Avg latency:   {avg_latency:.2f}s")
    print(f"{'=' * 80}\n")

    return results


def compare_approaches(
    experiments: list[Experiment],
    approaches: dict[str, tuple[Callable, Callable]],
) -> dict[str, list[ExperimentResult]]:
    """
    Compare multiple approaches on the same set of experiments.

    Args:
        experiments: List of experiments to run
        approaches: Dict mapping approach_name -> (retrieve_fn, evaluate_fn)

    Returns:
        Dict mapping approach_name -> list of ExperimentResults
    """
    all_results = {}

    for approach_name, (retrieve_fn, evaluate_fn) in approaches.items():
        results = run_batch(experiments, retrieve_fn, evaluate_fn, approach_name)
        all_results[approach_name] = results

    # Print comparison table
    print(f"\n{'=' * 80}")
    print("COMPARISON")
    print(f"{'=' * 80}")
    print(f"{'Approach':<20} {'Accuracy':<12} {'Avg Tokens':<12} {'Avg Latency':<12}")
    print(f"{'-' * 80}")

    for approach_name, results in all_results.items():
        accuracy = sum(r.accuracy for r in results) / len(results) * 100
        avg_tokens = sum(r.total_tokens for r in results) / len(results)
        avg_latency = sum(r.latency_seconds for r in results) / len(results)

        print(
            f"{approach_name:<20} {accuracy:>6.1f}%     {avg_tokens:>8.1f}     {avg_latency:>8.2f}s"
        )

    print(f"{'=' * 80}\n")

    return all_results


if __name__ == "__main__":
    import argparse
    import os
    import sys

    from test_cases import TEST_EXPERIMENTS

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run grounded search experiments with different approaches"
    )
    parser.add_argument(
        "--approaches",
        nargs="+",
        choices=["stub", "gemini_grounded", "perplexity", "openai_websearch"],
        help="Specific approach(es) to run (default: all available)",
    )
    parser.add_argument(
        "--experiments",
        type=int,
        help="Number of experiments to run (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available approaches and exit",
    )
    args = parser.parse_args()

    # Import all available approaches
    from approaches.stub import evaluate as stub_evaluate
    from approaches.stub import retrieve as stub_retrieve

    # Build approaches dict based on available API keys
    all_approaches = {
        "stub": (stub_retrieve, stub_evaluate),
    }

    # Add real approaches if API keys are available
    if os.getenv("GOOGLE_API_KEY"):
        from approaches.gemini_grounded import (
            evaluate as gemini_evaluate,
        )
        from approaches.gemini_grounded import (
            retrieve as gemini_retrieve,
        )

        all_approaches["gemini_grounded"] = (gemini_retrieve, gemini_evaluate)

    if os.getenv("PERPLEXITY_API_KEY"):
        from approaches.perplexity import (
            evaluate as perplexity_evaluate,
        )
        from approaches.perplexity import (
            retrieve as perplexity_retrieve,
        )

        all_approaches["perplexity"] = (perplexity_retrieve, perplexity_evaluate)

    if os.getenv("OPENAI_API_KEY"):
        from approaches.openai_websearch import (
            evaluate as openai_evaluate,
        )
        from approaches.openai_websearch import (
            retrieve as openai_retrieve,
        )

        all_approaches["openai_websearch"] = (openai_retrieve, openai_evaluate)

    # Handle --list flag
    if args.list:
        print("\nAvailable approaches:")
        print("-" * 60)
        for name in ["stub", "gemini_grounded", "perplexity", "openai_websearch"]:
            status = "✓ Available" if name in all_approaches else "✗ No API key"
            print(f"  {name:<25} {status}")
        print()
        sys.exit(0)

    # Filter approaches based on --approaches argument
    if args.approaches:
        approaches = {}
        for name in args.approaches:
            if name in all_approaches:
                approaches[name] = all_approaches[name]
            else:
                print(f"✗ Error: '{name}' requires API key but none found")
                print("  Set the required environment variable in .env")
                sys.exit(1)
    else:
        approaches = all_approaches

    # Select experiments
    experiments = TEST_EXPERIMENTS
    if args.experiments:
        experiments = TEST_EXPERIMENTS[: args.experiments]

    # Run comparison across selected approaches
    print(f"\nComparing {len(approaches)} approach(es) on {len(experiments)} test case(s)...")
    all_results = compare_approaches(experiments, approaches)

    # Flush Langfuse data
    langfuse.flush()

    print("\n✓ Results logged to Langfuse")
    print(f"  View at: {os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')}")
    print("  Project: badlmaninc/torale\n")
