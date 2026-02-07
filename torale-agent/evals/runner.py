"""Evaluation runner for the Torale monitoring agent."""

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent import create_monitoring_agent


@dataclass
class TestCase:
    """A test case from the cases.jsonl file."""

    name: str
    category: str
    search_query: str
    condition_description: str
    notify_behavior: str


@dataclass
class EvalResult:
    """Result from running a single evaluation."""

    case_name: str
    model: str
    run_number: int
    timestamp: str
    latency_ms: float
    response: dict[str, Any] | None
    error: str | None


async def load_cases(path: Path) -> list[TestCase]:
    """Load test cases from JSONL file."""
    cases = []
    with path.open() as f:
        for line in f:
            data = json.loads(line)
            cases.append(
                TestCase(
                    name=data["name"],
                    category=data["category"],
                    search_query=data["search_query"],
                    condition_description=data["condition_description"],
                    notify_behavior=data["notify_behavior"],
                )
            )
    return cases


async def run_single_eval(
    case: TestCase, model: str, run_number: int
) -> EvalResult:
    """Run a single evaluation with specified model."""
    timestamp = datetime.now(UTC).isoformat()
    start_time = time.perf_counter()

    # Build agent prompt with mock context for tools
    # Note: Tools like search_memories and add_memory require user_id and task_id
    # but those aren't critical for evals - the agent should primarily use perplexity_search
    prompt = f"""Analyze this monitoring task:

Search Query: {case.search_query}
Condition: {case.condition_description}
Category: {case.category}

User ID: eval-user
Task ID: eval-{case.name.lower().replace(' ', '-')}

Execute the search and determine if the condition is met.

IMPORTANT: Return ONLY valid JSON matching the MonitoringResponse schema. Do not include markdown code fences, explanations, or any text outside the JSON object."""

    try:
        # Create agent with specified model
        agent = create_monitoring_agent(model)

        # Call agent directly (no HTTP, no A2A protocol)
        result = await agent.run(prompt)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Convert MonitoringResponse to dict
        response_content = result.output.model_dump()

        return EvalResult(
            case_name=case.name,
            model=model,
            run_number=run_number,
            timestamp=timestamp,
            latency_ms=latency_ms,
            response=response_content,
            error=None,
        )

    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Try to extract any useful context from the error
        error_msg = str(e)
        response_debug = None

        # Check if this is a validation retry error with underlying details
        if "Exceeded maximum retries" in error_msg:
            error_msg = f"{error_msg} - Agent output failed validation after retries"

            # Try to get the last failed output from the exception chain
            # The validation error might have the actual output in the exception context
            import traceback
            tb = traceback.format_exception(type(e), e, e.__traceback__)
            tb_str = "".join(tb)

            # Try to extract output from error messages in traceback
            response_debug = {
                "error_type": type(e).__name__,
                "traceback_preview": tb_str[-1000:] if len(tb_str) > 1000 else tb_str,
            }

        return EvalResult(
            case_name=case.name,
            model=model,
            run_number=run_number,
            timestamp=timestamp,
            latency_ms=latency_ms,
            response=response_debug,
            error=error_msg,
        )


async def run_eval_suite(
    cases: list[TestCase], model: str, runs: int
) -> list[EvalResult]:
    """Run evaluation suite for all cases."""
    results = []

    for case in cases:
        for run_num in range(1, runs + 1):
            result = await run_single_eval(case, model, run_num)
            results.append(result)

    return results


def save_results(results: list[EvalResult], output_dir: Path) -> Path:
    """Save evaluation results to JSON file."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    model = results[0].model if results else "unknown"
    filename = f"{timestamp}_{model}.json"
    output_path = output_dir / filename

    # Convert results to dicts
    results_data = [
        {
            "case_name": r.case_name,
            "model": r.model,
            "run_number": r.run_number,
            "timestamp": r.timestamp,
            "latency_ms": r.latency_ms,
            "response": r.response,
            "error": r.error,
        }
        for r in results
    ]

    with output_path.open("w") as f:
        json.dump(results_data, f, indent=2)

    return output_path
