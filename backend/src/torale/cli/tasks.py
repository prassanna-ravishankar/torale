import json
import os
from typing import Optional
from uuid import UUID

import httpx
import typer
from rich import print
from rich.console import Console
from rich.table import Table

from torale.cli.auth import load_config

console = Console()
task_app = typer.Typer()


def get_client() -> httpx.Client:
    """Get HTTP client with authentication headers.

    Authentication modes (in order of precedence):
    1. TORALE_NOAUTH=1 - Skip authentication (local dev only)
    2. API key from config file
    """
    # Check for noauth mode
    if os.getenv("TORALE_NOAUTH") == "1":
        api_url = os.getenv("TORALE_API_URL", "http://localhost:8000")
        return httpx.Client(base_url=api_url, follow_redirects=True)

    # Load config for API key
    config = load_config()
    if not config:
        print("[red]✗ Not authenticated.[/red]")
        print("[cyan]To authenticate:[/cyan]")
        print("  1. Generate an API key at https://torale.ai")
        print("  2. Run: torale auth set-api-key")
        print()
        print("[cyan]For local development without auth:[/cyan]")
        print("  export TORALE_NOAUTH=1")
        raise typer.Exit(1)

    # Check for API key
    api_key = config.get("api_key")
    if not api_key:
        print("[red]✗ No API key found in config.[/red]")
        print("[cyan]Run: torale auth set-api-key[/cyan]")
        raise typer.Exit(1)

    headers = {"Authorization": f"Bearer {api_key}"}
    api_url = config.get("api_url", "http://localhost:8000")
    return httpx.Client(base_url=api_url, headers=headers, follow_redirects=True)


@task_app.command("create")
def create_task(
    name: str = typer.Argument(..., help="Task name"),
    schedule: str = typer.Option(..., "--schedule", "-s", help="Cron schedule expression"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="LLM prompt"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="LLM model to use"),
    max_tokens: int = typer.Option(1000, "--max-tokens", help="Maximum tokens for response"),
):
    """Create a new scheduled task"""
    with get_client() as client:
        task_data = {
            "name": name,
            "schedule": schedule,
            "executor_type": "llm_text",
            "config": {
                "prompt": prompt,
                "model": model,
                "max_tokens": max_tokens,
            },
        }
        
        try:
            response = client.post("/api/v1/tasks", json=task_data)
            response.raise_for_status()
            task = response.json()
            print(f"[green]✓ Task created successfully![/green]")
            print(f"[cyan]ID: {task['id']}[/cyan]")
            print(f"[cyan]Name: {task['name']}[/cyan]")
            print(f"[cyan]Schedule: {task['schedule']}[/cyan]")
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to create task: {e.response.text}[/red]")
            raise typer.Exit(1)


@task_app.command("list")
def list_tasks(
    active_only: bool = typer.Option(False, "--active", help="Show only active tasks"),
):
    """List all tasks"""
    with get_client() as client:
        params = {}
        if active_only:
            params["is_active"] = True
        
        try:
            response = client.get("/api/v1/tasks", params=params)
            response.raise_for_status()
            tasks = response.json()
            
            if not tasks:
                print("[yellow]No tasks found.[/yellow]")
                return
            
            table = Table(title="Your Tasks")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Schedule", style="yellow")
            table.add_column("Active", style="magenta")
            table.add_column("Created", style="blue")
            
            for task in tasks:
                table.add_row(
                    task["id"][:8] + "...",
                    task["name"],
                    task["schedule"],
                    "✓" if task["is_active"] else "✗",
                    task["created_at"][:19],
                )
            
            console.print(table)
            
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to list tasks: {e.response.text}[/red]")
            raise typer.Exit(1)


@task_app.command("get")
def get_task(task_id: str):
    """Get details of a specific task"""
    with get_client() as client:
        try:
            response = client.get(f"/api/v1/tasks/{task_id}")
            response.raise_for_status()
            task = response.json()
            
            print(f"[bold cyan]Task Details[/bold cyan]")
            print(f"[cyan]ID:[/cyan] {task['id']}")
            print(f"[cyan]Name:[/cyan] {task['name']}")
            print(f"[cyan]Schedule:[/cyan] {task['schedule']}")
            print(f"[cyan]Active:[/cyan] {'Yes' if task['is_active'] else 'No'}")
            print(f"[cyan]Executor:[/cyan] {task['executor_type']}")
            print(f"[cyan]Created:[/cyan] {task['created_at']}")
            print(f"[cyan]Config:[/cyan]")
            print(json.dumps(task['config'], indent=2))
            
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to get task: {e.response.text}[/red]")
            raise typer.Exit(1)


@task_app.command("update")
def update_task(
    task_id: str,
    name: Optional[str] = typer.Option(None, "--name", "-n"),
    schedule: Optional[str] = typer.Option(None, "--schedule", "-s"),
    active: Optional[bool] = typer.Option(None, "--active/--inactive"),
):
    """Update a task"""
    with get_client() as client:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if schedule is not None:
            update_data["schedule"] = schedule
        if active is not None:
            update_data["is_active"] = active
        
        if not update_data:
            print("[yellow]No updates specified.[/yellow]")
            return
        
        try:
            response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
            response.raise_for_status()
            task = response.json()
            print(f"[green]✓ Task updated successfully![/green]")
            print(f"[cyan]Name: {task['name']}[/cyan]")
            print(f"[cyan]Schedule: {task['schedule']}[/cyan]")
            print(f"[cyan]Active: {'Yes' if task['is_active'] else 'No'}[/cyan]")
            
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to update task: {e.response.text}[/red]")
            raise typer.Exit(1)


@task_app.command("delete")
def delete_task(
    task_id: str,
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a task"""
    if not confirm:
        confirm = typer.confirm(f"Are you sure you want to delete task {task_id}?")
        if not confirm:
            print("[yellow]Deletion cancelled.[/yellow]")
            return
    
    with get_client() as client:
        try:
            response = client.delete(f"/api/v1/tasks/{task_id}")
            response.raise_for_status()
            print(f"[green]✓ Task deleted successfully![/green]")
            
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to delete task: {e.response.text}[/red]")
            raise typer.Exit(1)


@task_app.command("execute")
def execute_task(task_id: str):
    """Manually execute a task"""
    with get_client() as client:
        try:
            response = client.post(f"/api/v1/tasks/{task_id}/execute")
            response.raise_for_status()
            execution = response.json()
            print(f"[green]✓ Task execution started![/green]")
            print(f"[cyan]Execution ID: {execution['id']}[/cyan]")
            print(f"[cyan]Status: {execution['status']}[/cyan]")
            
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to execute task: {e.response.text}[/red]")
            raise typer.Exit(1)


@task_app.command("logs")
def get_logs(
    task_id: str,
    limit: int = typer.Option(10, "--limit", "-l", help="Number of executions to show"),
):
    """Get execution logs for a task"""
    with get_client() as client:
        try:
            response = client.get(f"/api/v1/tasks/{task_id}/executions", params={"limit": limit})
            response.raise_for_status()
            executions = response.json()
            
            if not executions:
                print("[yellow]No executions found.[/yellow]")
                return
            
            table = Table(title=f"Execution Logs (Task: {task_id[:8]}...)")
            table.add_column("Execution ID", style="cyan", no_wrap=True)
            table.add_column("Status", style="green")
            table.add_column("Started", style="yellow")
            table.add_column("Completed", style="blue")
            
            for execution in executions:
                status_color = {
                    "success": "green",
                    "failed": "red",
                    "running": "yellow",
                    "pending": "cyan",
                }.get(execution["status"], "white")
                
                table.add_row(
                    execution["id"][:8] + "...",
                    f"[{status_color}]{execution['status']}[/{status_color}]",
                    execution["started_at"][:19] if execution["started_at"] else "-",
                    execution["completed_at"][:19] if execution.get("completed_at") else "-",
                )
            
            console.print(table)
            
        except httpx.HTTPStatusError as e:
            print(f"[red]✗ Failed to get logs: {e.response.text}[/red]")
            raise typer.Exit(1)