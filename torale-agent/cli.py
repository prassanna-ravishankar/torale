"""CLI for Torale agent evaluation."""

import asyncio
import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agent import MonitoringDeps, create_monitoring_agent

app = typer.Typer(help="Torale Agent Evaluation CLI")
eval_app = typer.Typer(help="Run and manage evaluations")
app.add_typer(eval_app, name="eval")

console = Console()

CASES_PATH = Path(__file__).parent / "evals" / "cases.yaml"
GENERATED_DIR = Path(__file__).parent / "evals" / "generated"


@app.command()
def query(
    prompt: str = typer.Argument(..., help="Prompt to send to the agent"),
    model: str = typer.Option(
        "google-gla:gemini-3.1-flash-lite-preview", help="Model to use"
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Show only raw output (no formatting)"
    ),
):
    """Run a query against the agent for ad-hoc testing."""
    asyncio.run(_query_async(prompt, model, raw))


async def _query_async(prompt: str, model: str, raw: bool):
    if not raw:
        console.print(f"\n[bold]Running query with model [cyan]{model}[/cyan][/bold]\n")

    start_time = time.perf_counter()

    try:
        agent = create_monitoring_agent(model)
        deps = MonitoringDeps(user_id="cli-user", task_id="cli-query")
        result = await agent.run(prompt, deps=deps)
        latency_ms = (time.perf_counter() - start_time) * 1000

        output_json = result.output.model_dump_json(indent=2)

        if raw:
            print(output_json)
        else:
            console.print(f"[green]Success![/green] ({latency_ms:.0f}ms)\n")
            console.print(output_json)

    # Only catch expected agent/model errors
    except (ValueError, RuntimeError, KeyError, AttributeError) as e:
        latency_ms = (time.perf_counter() - start_time) * 1000

        if raw:
            print(f"ERROR: {e}", file=sys.stderr)
        else:
            console.print(f"[red]Error:[/red] ({latency_ms:.0f}ms)")
            console.print(str(e))
        raise typer.Exit(1)


@eval_app.command()
def run(
    model: str = typer.Option(
        "google-gla:gemini-3.1-flash-lite-preview",
        help="Model to evaluate",
    ),
    case: str | None = typer.Option(None, help="Specific case name to run"),
    limit: int | None = typer.Option(None, help="Limit to first N test cases"),
    passes: int = typer.Option(
        1, help="Number of sequential passes per case (multi-pass)"
    ),
    max_concurrency: int = typer.Option(1, help="Max concurrent case evaluations"),
    with_dynamic: bool = typer.Option(
        False, "--with-dynamic", help="Include latest dynamic cases"
    ),
    dataset: Path | None = typer.Option(
        None, help="Path to a specific dataset YAML file"
    ),
):
    """Run evaluation suite with specified model."""
    asyncio.run(
        _run_async(model, case, limit, passes, max_concurrency, with_dynamic, dataset)
    )


async def _run_async(
    model: str,
    case_name: str | None,
    limit: int | None,
    passes: int,
    max_concurrency: int,
    with_dynamic: bool,
    dataset_path: Path | None,
):
    from evals.models import MonitoringDataset
    from evals.runner import load_dataset, merge_datasets, run_eval

    # Load dataset
    if dataset_path:
        ds = load_dataset(dataset_path)
    elif with_dynamic:
        latest = _find_latest_generated()
        ds = merge_datasets(CASES_PATH, latest)
    else:
        ds = load_dataset(CASES_PATH)

    # Filter and slice cases in one pass
    cases = list(ds.cases)
    if case_name:
        cases = [c for c in cases if c.name == case_name]
        if not cases:
            console.print(f"[red]Error: Case '{case_name}' not found[/red]")
            raise typer.Exit(1)
    if limit is not None:
        cases = cases[:limit]

    if not cases:
        console.print("[yellow]No cases to evaluate after filtering[/yellow]")
        raise typer.Exit(0)

    # Set passes on all cases
    if passes > 1:
        for c in cases:
            c.inputs.passes = passes

    ds = MonitoringDataset(cases=cases, evaluators=ds.evaluators)

    console.print(
        f"\n[bold]Running {len(cases)} case(s) with model [cyan]{model}[/cyan]"
        f" ({passes} pass{'es' if passes > 1 else ''} each)[/bold]\n"
    )

    report = await run_eval(
        ds,
        model=model,
        max_concurrency=max_concurrency,
    )
    report.print(include_input=True, include_output=True)


@eval_app.command(name="list")
def list_cases():
    """List all test cases."""
    from evals.runner import load_dataset

    try:
        ds = load_dataset(CASES_PATH)
    except FileNotFoundError:
        console.print(f"[red]Error: Cases file not found at {CASES_PATH}[/red]")
        raise typer.Exit(1)

    table = Table(title="Test Cases", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Search Query", max_width=60)
    table.add_column("Notify")

    for case in ds.cases:
        table.add_row(
            case.name or "",
            case.inputs.category,
            case.inputs.search_query,
            case.inputs.notify_behavior,
        )

    console.print(table)
    console.print(f"\n[bold]{len(ds.cases)} test cases[/bold]")


@eval_app.command()
def generate():
    """Generate dynamic cases from live data (weather, stocks, news, sports)."""
    asyncio.run(_generate_async())


async def _generate_async():
    from evals.dynamic import generate_and_save

    console.print("\n[bold]Generating dynamic cases...[/bold]\n")

    try:
        path = await generate_and_save(GENERATED_DIR)
        console.print(f"[green]Generated cases saved to:[/green] {path}")
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _find_latest_generated() -> Path | None:
    """Find the most recent generated dataset file."""
    if not GENERATED_DIR.exists():
        return None
    files = sorted(
        GENERATED_DIR.glob("*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return files[0] if files else None


if __name__ == "__main__":
    app()
