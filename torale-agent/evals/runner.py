"""Evaluation runner for the Torale monitoring agent."""

import json
import logging
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent import MonitoringDeps, create_monitoring_agent

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    name: str
    category: str
    search_query: str
    condition_description: str
    notify_behavior: str


@dataclass
class EvalResult:
    case_name: str
    model: str
    run_number: int
    timestamp: str
    latency_ms: float
    response: dict[str, Any] | None
    error: str | None


def load_cases(path: Path) -> list[TestCase]:
    """Load test cases from a JSONL file."""
    cases = []
    with path.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
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

    return cases


async def run_single_eval(
    case: TestCase, model: str, run_number: int
) -> EvalResult:
    """Run a single evaluation case against the specified model."""
    timestamp = datetime.now(UTC).isoformat()
    start_time = time.perf_counter()

    prompt = f"""Analyze this monitoring task:

Search Query: {case.search_query}
Condition: {case.condition_description}
Category: {case.category}

Execute the search and determine if the condition is met.

IMPORTANT: Return ONLY valid JSON matching the MonitoringResponse schema. Do not include markdown code fences, explanations, or any text outside the JSON object."""

    # Pass user_id and task_id via dependencies (secure, not LLM-controlled)
    deps = MonitoringDeps(
        user_id="eval-user",
        task_id=f"eval-{case.name.lower().replace(' ', '-')}"
    )

    try:
        agent = create_monitoring_agent(model)
        result = await agent.run(prompt, deps=deps)
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

            try:
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                tb_str = "".join(tb)
                response_debug = {
                    "error_type": type(e).__name__,
                    "traceback_preview": tb_str[-1000:] if len(tb_str) > 1000 else tb_str,
                }
            except Exception:
                response_debug = {"error_type": type(e).__name__}

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
    """Run all cases sequentially, repeating each case for the given number of runs."""
    return [
        await run_single_eval(case, model, run_num)
        for case in cases
        for run_num in range(1, runs + 1)
    ]


def save_results(results: list[EvalResult], output_dir: Path) -> Path:
    """Save results to {timestamp}_{model}.json for chronological sorting and model lookup."""
    if not results:
        raise ValueError("Cannot save empty results list")

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{results[0].model}.json"
    output_path = output_dir / filename

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Cannot create results directory: {e}") from e

    results_data = [asdict(r) for r in results]

    try:
        with output_path.open("w") as f:
            json.dump(results_data, f, indent=2)
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Cannot save results file: {e}") from e

    logger.info(f"Saved {len(results)} results to {output_path}")
    return output_path
