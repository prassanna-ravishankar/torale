"""Evaluation runner for the Torale monitoring agent."""

import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent import create_monitoring_agent

logger = logging.getLogger(__name__)


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


def load_cases(path: Path) -> list[TestCase]:
    """Load test cases from JSONL file."""
    cases = []
    try:
        with path.open() as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                try:
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
                except json.JSONDecodeError as e:
                    raise ValueError(f"Malformed JSON in cases file at line {line_num}: {e}") from e
                except KeyError as e:
                    raise ValueError(f"Missing required field {e} in cases file at line {line_num}") from e
    except FileNotFoundError:
        raise  # Re-raise as-is, handled by caller

    return cases


async def run_single_eval(
    case: TestCase, model: str, run_number: int
) -> EvalResult:
    """Run a single evaluation with specified model."""
    timestamp = datetime.now(UTC).isoformat()
    start_time = time.perf_counter()

    # Build agent prompt with mock context for tools.
    # Mock user_id and task_id are provided so memory tools will function,
    # though evals primarily test search and decision-making capabilities.
    prompt = f"""Analyze this monitoring task:

Search Query: {case.search_query}
Condition: {case.condition_description}
Category: {case.category}

User ID: eval-user
Task ID: eval-{case.name.lower().replace(' ', '-')}

Execute the search and determine if the condition is met.

IMPORTANT: Return ONLY valid JSON matching the MonitoringResponse schema. Do not include markdown code fences, explanations, or any text outside the JSON object."""

    try:
        agent = create_monitoring_agent(model)
        result = await agent.run(prompt)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

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

    # Only catch expected agent/model errors - let programming errors propagate
    except (ValueError, RuntimeError, KeyError, AttributeError) as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        error_msg = str(e)
        response_debug = None

        # Check if this is a validation retry error with underlying details
        if "Exceeded maximum retries" in error_msg:
            error_msg = f"{error_msg} - Agent output failed validation after retries"

            # Try to extract traceback for debugging
            try:
                import traceback
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                tb_str = "".join(tb)
                response_debug = {
                    "error_type": type(e).__name__,
                    "traceback_preview": tb_str[-1000:] if len(tb_str) > 1000 else tb_str,
                }
            except Exception:
                # If traceback extraction fails, just save error type
                response_debug = {"error_type": type(e).__name__}

        # Log the failure
        logger.error(
            f"Evaluation failed: case={case.name}, model={model}, run={run_number}, "
            f"latency_ms={latency_ms:.0f}, error={error_msg}"
        )

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
    """Save evaluation results to JSON file.

    File naming: {timestamp}_{model}.json where timestamp is YYYYmmdd_HHMMSS.
    This format allows the CLI's compare command to find results by model name
    and sort chronologically.
    """
    if not results:
        raise ValueError("Cannot save empty results list")

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    model = results[0].model
    filename = f"{timestamp}_{model}.json"
    output_path = output_dir / filename

    # Ensure output directory exists
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise RuntimeError(f"Cannot create results directory: {e}") from e

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

    try:
        with output_path.open("w") as f:
            json.dump(results_data, f, indent=2)
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to write results to {output_path}: {e}")
        raise RuntimeError(f"Cannot save results file: {e}") from e

    logger.info(f"Saved {len(results)} results to {output_path}")
    return output_path
