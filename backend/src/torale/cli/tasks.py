"""CLI commands for task management using the Torale SDK."""

import json

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from torale.sdk import Torale
from torale.sdk.exceptions import AuthenticationError, ToraleError

console = Console()
task_app = typer.Typer()


def get_client() -> Torale:
    """
    Get Torale SDK client with authentication.

    Authentication modes (in order of precedence):
    1. TORALE_NOAUTH=1 - Skip authentication (local dev only)
    2. API key from environment variable or config file

    Returns:
        Torale client instance

    Raises:
        typer.Exit: If authentication fails
    """
    try:
        return Torale()
    except AuthenticationError:
        print("[red]✗ Not authenticated.[/red]")
        print("[cyan]To authenticate:[/cyan]")
        print("  1. Generate an API key at https://torale.ai")
        print("  2. Run: torale auth set-api-key")
        print()
        print("[cyan]For local development without auth:[/cyan]")
        print("  export TORALE_NOAUTH=1")
        raise typer.Exit(1) from None


@task_app.command("create")
def create_task(
    query: str = typer.Option(..., "--query", "-q", help="What to monitor"),
    condition: str = typer.Option(..., "--condition", "-c", help="When to trigger notification"),
    name: str | None = typer.Option(
        None, "--name", "-n", help="Task name (auto-generated if not provided)"
    ),
    schedule: str = typer.Option("0 9 * * *", "--schedule", "-s", help="Cron schedule expression"),
    notify_behavior: str = typer.Option(
        "once", "--notify-behavior", help="When to notify: once, always, track_state"
    ),
    webhook: str | None = typer.Option(None, "--webhook", "-w", help="Webhook URL to call"),
    model: str = typer.Option("gemini-2.0-flash-exp", "--model", "-m", help="LLM model to use"),
):
    """
    Create a new monitoring task.

    Example:
        torale task create \\
            --query "When is iPhone 16 being released?" \\
            --condition "A specific release date is announced" \\
            --webhook "https://myapp.com/alert"
    """
    with get_client() as client:
        try:
            # Build notifications list
            notifications = []
            if webhook:
                notifications.append({"type": "webhook", "url": webhook})

            # Generate name if not provided
            if not name:
                name = f"Monitor: {query[:50]}"

            # Create task using SDK
            task = client.tasks.create(
                name=name,
                search_query=query,
                condition_description=condition,
                schedule=schedule,
                notify_behavior=notify_behavior,
                notifications=notifications,
                config={"model": model},
            )

            print("[green]✓ Task created successfully![/green]")
            print(f"[cyan]ID: {task.id}[/cyan]")
            print(f"[cyan]Name: {task.name}[/cyan]")
            print(f"[cyan]Schedule: {task.schedule}[/cyan]")
            print(f"[cyan]Query: {task.search_query}[/cyan]")
            print(f"[cyan]Condition: {task.condition_description}[/cyan]")

        except ToraleError as e:
            print(f"[red]✗ Failed to create task: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("list")
def list_tasks(
    active_only: bool = typer.Option(False, "--active", help="Show only active tasks"),
):
    """List all monitoring tasks."""
    with get_client() as client:
        try:
            tasks = client.tasks.list(active=active_only if active_only else None)

            if not tasks:
                print("[yellow]No tasks found.[/yellow]")
                return

            table = Table(title="Your Monitoring Tasks")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Query", style="yellow")
            table.add_column("Schedule", style="magenta")
            table.add_column("Active", style="blue")
            table.add_column("Created", style="white")

            for task in tasks:
                table.add_row(
                    str(task.id)[:8] + "...",
                    task.name,
                    task.search_query[:40] + "..."
                    if len(task.search_query) > 40
                    else task.search_query,
                    task.schedule,
                    "✓" if task.is_active else "✗",
                    str(task.created_at)[:19],
                )

            console.print(table)

        except ToraleError as e:
            print(f"[red]✗ Failed to list tasks: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("get")
def get_task(task_id: str):
    """Get details of a specific monitoring task."""
    with get_client() as client:
        try:
            task = client.tasks.get(task_id)

            print("[bold cyan]Task Details[/bold cyan]")
            print(f"[cyan]ID:[/cyan] {task.id}")
            print(f"[cyan]Name:[/cyan] {task.name}")
            print(f"[cyan]Query:[/cyan] {task.search_query}")
            print(f"[cyan]Condition:[/cyan] {task.condition_description}")
            print(f"[cyan]Schedule:[/cyan] {task.schedule}")
            print(f"[cyan]Notify Behavior:[/cyan] {task.notify_behavior}")
            print(f"[cyan]Active:[/cyan] {'Yes' if task.is_active else 'No'}")
            print(f"[cyan]Created:[/cyan] {task.created_at}")

            if task.notifications:
                print("[cyan]Notifications:[/cyan]")
                for notif in task.notifications:
                    print(f"  - {notif.type}: {notif.address or notif.url}")

            print("[cyan]Config:[/cyan]")
            print(json.dumps(task.config, indent=2))

            if task.last_known_state:
                print("[cyan]Last Known State:[/cyan]")
                print(json.dumps(task.last_known_state, indent=2))

        except ToraleError as e:
            print(f"[red]✗ Failed to get task: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("update")
def update_task(
    task_id: str,
    name: str | None = typer.Option(None, "--name", "-n"),
    schedule: str | None = typer.Option(None, "--schedule", "-s"),
    active: bool | None = typer.Option(None, "--active/--inactive"),
):
    """Update a monitoring task."""
    with get_client() as client:
        try:
            # Build update kwargs
            kwargs = {}
            if name is not None:
                kwargs["name"] = name
            if schedule is not None:
                kwargs["schedule"] = schedule
            if active is not None:
                kwargs["is_active"] = active

            if not kwargs:
                print("[yellow]No updates specified.[/yellow]")
                return

            task = client.tasks.update(task_id, **kwargs)
            print("[green]✓ Task updated successfully![/green]")
            print(f"[cyan]Name: {task.name}[/cyan]")
            print(f"[cyan]Schedule: {task.schedule}[/cyan]")
            print(f"[cyan]Active: {'Yes' if task.is_active else 'No'}[/cyan]")

        except ToraleError as e:
            print(f"[red]✗ Failed to update task: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("delete")
def delete_task(
    task_id: str,
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a monitoring task."""
    if not confirm:
        confirm = typer.confirm(f"Are you sure you want to delete task {task_id}?")
        if not confirm:
            print("[yellow]Deletion cancelled.[/yellow]")
            return

    with get_client() as client:
        try:
            client.tasks.delete(task_id)
            print("[green]✓ Task deleted successfully![/green]")

        except ToraleError as e:
            print(f"[red]✗ Failed to delete task: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("execute")
def execute_task(task_id: str):
    """Manually execute a monitoring task (test run)."""
    with get_client() as client:
        try:
            execution = client.tasks.execute(task_id)
            print("[green]✓ Task execution started![/green]")
            print(f"[cyan]Execution ID: {execution.id}[/cyan]")
            print(f"[cyan]Status: {execution.status}[/cyan]")

        except ToraleError as e:
            print(f"[red]✗ Failed to execute task: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("logs")
def get_logs(
    task_id: str,
    limit: int = typer.Option(10, "--limit", "-l", help="Number of executions to show"),
):
    """Get execution logs for a monitoring task."""
    with get_client() as client:
        try:
            executions = client.tasks.executions(task_id, limit=limit)

            if not executions:
                print("[yellow]No executions found.[/yellow]")
                return

            table = Table(title=f"Execution Logs (Task: {task_id[:8]}...)")
            table.add_column("Execution ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="green")
            table.add_column("Condition Met", style="yellow")
            table.add_column("Started", style="blue")
            table.add_column("Completed", style="white")

            for execution in executions:
                status_color = {
                    "success": "green",
                    "failed": "red",
                    "running": "yellow",
                    "pending": "cyan",
                }.get(
                    execution.status.value
                    if hasattr(execution.status, "value")
                    else execution.status,
                    "white",
                )

                table.add_row(
                    str(execution.id)[:8] + "...",
                    f"[{status_color}]{execution.status}[/{status_color}]",
                    "✓" if execution.condition_met else "✗",
                    str(execution.started_at)[:19] if execution.started_at else "-",
                    str(execution.completed_at)[:19] if execution.completed_at else "-",
                )

            console.print(table)

        except ToraleError as e:
            print(f"[red]✗ Failed to get logs: {str(e)}[/red]")
            raise typer.Exit(1) from e


@task_app.command("notifications")
def get_notifications(
    task_id: str,
    limit: int = typer.Option(10, "--limit", "-l", help="Number of notifications to show"),
):
    """Get notifications (executions where condition was met)."""
    with get_client() as client:
        try:
            notifications = client.tasks.notifications(task_id, limit=limit)

            if not notifications:
                print("[yellow]No notifications found.[/yellow]")
                return

            table = Table(title=f"Notifications (Task: {task_id[:8]}...)")
            table.add_column("Execution ID", style="cyan", no_wrap=True)
            table.add_column("Change Summary", style="green")
            table.add_column("Timestamp", style="blue")

            for notif in notifications:
                table.add_row(
                    str(notif.id)[:8] + "...",
                    notif.change_summary or "Condition met",
                    str(notif.started_at)[:19] if notif.started_at else "-",
                )

            console.print(table)

        except ToraleError as e:
            print(f"[red]✗ Failed to get notifications: {str(e)}[/red]")
            raise typer.Exit(1) from e
