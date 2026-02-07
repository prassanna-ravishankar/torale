"""CLI for Torale agent evaluation."""

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from evals.runner import load_cases, run_eval_suite, save_results

app = typer.Typer(help="Torale Agent Evaluation CLI")
eval_app = typer.Typer(help="Run and manage evaluations")
app.add_typer(eval_app, name="eval")

console = Console()

CASES_PATH = Path(__file__).parent / "evals" / "cases.jsonl"
RESULTS_DIR = Path(__file__).parent / "evals" / "results"


@app.command()
def query(
    prompt: str = typer.Argument(..., help="Prompt to send to the agent"),
    model: str = typer.Option("google-gla:gemini-3-flash-preview", help="Model to use"),
    raw: bool = typer.Option(False, "--raw", help="Show only raw output (no formatting)"),
):
    """Run a query against the agent (validation disabled for ad-hoc testing)."""
    asyncio.run(_query_async(prompt, model, raw))


async def _query_async(prompt: str, model: str, raw: bool):
    """Async implementation of query command."""
    import time
    from agent import create_monitoring_agent

    if not raw:
        console.print(f"\n[bold]Running query with model [cyan]{model}[/cyan][/bold]\n")

    start_time = time.perf_counter()

    try:
        # Create agent and run query
        agent = create_monitoring_agent(model)
        result = await agent.run(prompt)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Convert MonitoringResponse to JSON
        output_json = result.output.model_dump_json(indent=2)

        if raw:
            # Just print the raw JSON for piping
            print(output_json)
        else:
            console.print(f"[green]Success![/green] ({latency_ms:.0f}ms)\n")
            console.print(output_json)

    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        if raw:
            print(f"ERROR: {e}", file=__import__('sys').stderr)
            raise typer.Exit(1)
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
    """Async implementation of run command."""
    # Load cases
    try:
        cases = await load_cases(CASES_PATH)
    except FileNotFoundError:
        console.print(f"[red]Error: Cases file not found at {CASES_PATH}[/red]")
        raise typer.Exit(1)

    # Filter if specific case requested
    if case:
        cases = [c for c in cases if c.name == case]
        if not cases:
            console.print(f"[red]Error: Case '{case}' not found[/red]")
            raise typer.Exit(1)

    # Limit to first N cases if requested
    if limit is not None:
        cases = cases[:limit]

    console.print(
        f"\n[bold]Running {len(cases)} case(s) with model [cyan]{model}[/cyan] "
        f"({runs} run{'s' if runs > 1 else ''} each)[/bold]\n"
    )

    # Run evaluations with progress
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

                from evals.runner import run_single_eval

                result = await run_single_eval(case_obj, model, run_num)
                results.append(result)
                progress.advance(task)

                # Show result
                status = "[green]✓[/green]" if result.error is None else "[red]✗[/red]"
                console.print(
                    f"  {status} {case_obj.name} (run {run_num}): "
                    f"{result.latency_ms:.0f}ms"
                )

    # Save results
    output_path = save_results(results, RESULTS_DIR)
    console.print(f"\n[green]Results saved to:[/green] {output_path}")

    # Summary
    success_count = sum(1 for r in results if r.error is None)
    error_count = len(results) - success_count
    avg_latency = sum(r.latency_ms for r in results) / len(results)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total: {len(results)}")
    console.print(f"  Success: [green]{success_count}[/green]")
    console.print(f"  Errors: [red]{error_count}[/red]")
    console.print(f"  Avg Latency: {avg_latency:.0f}ms")


@eval_app.command()
def list():
    """List all test cases."""
    asyncio.run(_list_async())


async def _list_async():
    """Async implementation of list command."""
    try:
        cases = await load_cases(CASES_PATH)
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
        with result_file.open() as f:
            data = json.load(f)

        if not data:
            continue

        model = data[0]["model"]
        cases = len(set(r["case_name"] for r in data))
        success = sum(1 for r in data if r["error"] is None)
        total = len(data)
        avg_latency = sum(r["latency_ms"] for r in data) / total

        # Extract timestamp from filename
        timestamp = result_file.stem.split("_")[0]

        table.add_row(
            timestamp,
            model,
            str(cases),
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

    # Find latest results for each model
    def find_latest_for_model(model: str):
        matching = [
            f for f in RESULTS_DIR.glob("*.json") if model in f.name
        ]
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

    # Load results
    with file1.open() as f:
        data1 = json.load(f)
    with file2.open() as f:
        data2 = json.load(f)

    # Build comparison table
    table = Table(
        title=f"Model Comparison: {model1} vs {model2}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric")
    table.add_column(model1, style="green")
    table.add_column(model2, style="blue")

    # Calculate metrics
    def calc_metrics(data):
        success = sum(1 for r in data if r["error"] is None)
        total = len(data)
        avg_latency = sum(r["latency_ms"] for r in data) / total if total > 0 else 0
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
