"""CLI for Torale agent evaluation."""

import asyncio
import json
import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agent import MonitoringDeps, create_monitoring_agent
from evals.runner import load_cases, run_single_eval, save_results

app = typer.Typer(help="Torale Agent Evaluation CLI")
eval_app = typer.Typer(help="Run and manage evaluations")
app.add_typer(eval_app, name="eval")

console = Console()

CASES_PATH = Path(__file__).parent / "evals" / "cases.jsonl"
RESULTS_DIR = Path(__file__).parent / "evals" / "results"


def _load_results_file(path: Path) -> list[dict]:
    """Load and parse a JSON results file, exiting on failure."""
    try:
        with path.open() as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Results file {path.name} is corrupted: {e}[/red]")
        raise typer.Exit(1)
    except OSError as e:
        console.print(f"[red]Error: Cannot read {path.name}: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def query(
    prompt: str = typer.Argument(..., help="Prompt to send to the agent"),
    model: str = typer.Option("google-gla:gemini-3-flash-preview", help="Model to use"),
    raw: bool = typer.Option(False, "--raw", help="Show only raw output (no formatting)"),
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
    model: str = typer.Option("google-gla:gemini-3-flash-preview", help="Model to evaluate (e.g., google-gla:gemini-3-flash-preview, claude-3-5-sonnet-20241022)"),
    runs: int = typer.Option(1, help="Number of runs per case"),
    case: str | None = typer.Option(None, help="Specific case name to run"),
    limit: int | None = typer.Option(None, help="Limit to first N test cases"),
):
    """Run evaluation suite with specified model."""
    asyncio.run(_run_async(model, runs, case, limit))


async def _run_async(model: str, runs: int, case: str | None, limit: int | None):
    try:
        cases = load_cases(CASES_PATH)
    except FileNotFoundError:
        console.print(f"[red]Error: Cases file not found at {CASES_PATH}[/red]")
        raise typer.Exit(1)

    if case:
        cases = [c for c in cases if c.name == case]
        if not cases:
            console.print(f"[red]Error: Case '{case}' not found[/red]")
            raise typer.Exit(1)

    if limit is not None:
        cases = cases[:limit]

    if not cases:
        console.print("[yellow]No cases to evaluate after filtering[/yellow]")
        raise typer.Exit(0)

    console.print(
        f"\n[bold]Running {len(cases)} case(s) with model [cyan]{model}[/cyan] "
        f"({runs} run{'s' if runs > 1 else ''} each)[/bold]\n"
    )

    results = []
    total_evals = len(cases) * runs

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running evaluations...", total=total_evals)

        for case_obj in cases:
            for run_num in range(1, runs + 1):
                progress.update(
                    task,
                    description=f"[cyan]{case_obj.name}[/cyan] (run {run_num}/{runs})",
                )

                result = await run_single_eval(case_obj, model, run_num)
                results.append(result)
                progress.advance(task)

                status = "[green]✓[/green]" if result.error is None else "[red]✗[/red]"
                console.print(
                    f"  {status} {case_obj.name} (run {run_num}): "
                    f"{result.latency_ms:.0f}ms"
                )

    output_path = save_results(results, RESULTS_DIR)
    console.print(f"\n[green]Results saved to:[/green] {output_path}")

    success_count = sum(1 for r in results if r.error is None)
    avg_latency = sum(r.latency_ms for r in results) / len(results)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total: {len(results)}")
    console.print(f"  Success: [green]{success_count}[/green]")
    console.print(f"  Errors: [red]{len(results) - success_count}[/red]")
    console.print(f"  Avg Latency: {avg_latency:.0f}ms")


@eval_app.command(name="list")
def list_cases():
    """List all test cases."""
    asyncio.run(_list_async())


async def _list_async():
    try:
        cases = load_cases(CASES_PATH)
    except FileNotFoundError:
        console.print(f"[red]Error: Cases file not found at {CASES_PATH}[/red]")
        raise typer.Exit(1)

    table = Table(title="Test Cases", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Search Query", max_width=60)
    table.add_column("Notify")

    for case in cases:
        table.add_row(
            case.name,
            case.category,
            case.search_query,
            case.notify_behavior,
        )

    console.print(table)
    console.print(f"\n[bold]{len(cases)} test cases[/bold]")


@eval_app.command()
def results(limit: int = typer.Option(10, help="Number of recent results to show")):
    """Show recent evaluation results."""
    if not RESULTS_DIR.exists():
        console.print("[yellow]No results directory found[/yellow]")
        raise typer.Exit(0)

    result_files = sorted(
        RESULTS_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]

    if not result_files:
        console.print("[yellow]No results found[/yellow]")
        raise typer.Exit(0)

    table = Table(title="Recent Results", show_header=True, header_style="bold cyan")
    table.add_column("Timestamp")
    table.add_column("Model")
    table.add_column("Cases")
    table.add_column("Success")
    table.add_column("Avg Latency")

    for result_file in result_files:
        try:
            with result_file.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            console.print(f"[yellow]Warning: Skipping {result_file.name}: {e}[/yellow]")
            continue

        if not data:
            continue

        total = len(data)
        success = sum(1 for r in data if r["error"] is None)
        avg_latency = sum(r["latency_ms"] for r in data) / total
        timestamp = "_".join(result_file.stem.split("_")[:2])

        table.add_row(
            timestamp,
            data[0]["model"],
            str(len(set(r["case_name"] for r in data))),
            f"{success}/{total}",
            f"{avg_latency:.0f}ms",
        )

    console.print(table)


@eval_app.command()
def compare(model1: str, model2: str):
    """Compare two models side-by-side."""
    if not RESULTS_DIR.exists():
        console.print("[yellow]No results directory found[/yellow]")
        raise typer.Exit(0)

    def find_latest_for_model(model: str) -> Path | None:
        matching = [f for f in RESULTS_DIR.glob("*.json") if model in f.name]
        if not matching:
            return None
        return max(matching, key=lambda p: p.stat().st_mtime)

    file1 = find_latest_for_model(model1)
    file2 = find_latest_for_model(model2)

    if not file1:
        console.print(f"[red]No results found for model: {model1}[/red]")
        raise typer.Exit(1)
    if not file2:
        console.print(f"[red]No results found for model: {model2}[/red]")
        raise typer.Exit(1)

    data1 = _load_results_file(file1)
    data2 = _load_results_file(file2)

    table = Table(
        title=f"Model Comparison: {model1} vs {model2}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric")
    table.add_column(model1, style="green")
    table.add_column(model2, style="blue")

    def calc_metrics(data):
        if not data:
            return 0, 0, 0.0
        success = sum(1 for r in data if r["error"] is None)
        total = len(data)
        avg_latency = sum(r["latency_ms"] for r in data) / total
        return success, total, avg_latency

    s1, t1, l1 = calc_metrics(data1)
    s2, t2, l2 = calc_metrics(data2)

    table.add_row("Total Runs", str(t1), str(t2))
    table.add_row("Successful", str(s1), str(s2))
    table.add_row("Success Rate", f"{s1/t1*100:.1f}%" if t1 > 0 else "N/A", f"{s2/t2*100:.1f}%" if t2 > 0 else "N/A")
    table.add_row("Avg Latency", f"{l1:.0f}ms", f"{l2:.0f}ms")

    console.print(table)


if __name__ == "__main__":
    app()
