#!/usr/bin/env python3
"""
Rich utilities for consistent, beautiful terminal output across all scripts.

Provides standardized styling, panels, progress indicators, and status messages.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.markdown import Markdown
from rich import box

# Global console instance
console = Console()


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green][OK][/bold green] {message}")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red][ERROR][/bold red] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow][WARN][/bold yellow] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[bold blue][INFO][/bold blue] {message}")


def print_step(step_num: int, total_steps: int, message: str, icon: str = None):
    """Print a workflow step with progress indicator."""
    console.print(f"[bold cyan][{step_num}/{total_steps}][/bold cyan] {message}")


def print_header(message: str):
    """Print a section header."""
    console.print(f"\n[bold magenta]{message}[/bold magenta]\n")


def print_subheader(message: str):
    """Print a subsection header."""
    console.print(f"[bold]{message}[/bold]")


def create_panel(content: str, title: str = "", border_style: str = "blue"):
    """Create and print a styled panel."""
    panel = Panel(content, title=title, border_style=border_style, box=box.ROUNDED)
    console.print(panel)


def create_table(title: str, columns: list, rows: list = None):
    """Create a styled table."""
    table = Table(title=title, box=box.SIMPLE, show_header=True, header_style="bold magenta")
    
    for col in columns:
        table.add_column(col)
    
    if rows:
        for row in rows:
            table.add_row(*row)
    
    return table


def print_table(title: str, columns: list, rows: list = None):
    """Create and print a styled table."""
    table = create_table(title, columns, rows)
    console.print(table)


def print_json(data: dict, title: str = ""):
    """Pretty print JSON data."""
    from rich.json import JSON
    json_obj = JSON.from_data(data)
    if title:
        console.print(f"[bold]{title}[/bold]")
    console.print(json_obj)


def print_markdown(content: str):
    """Print markdown content."""
    console.print(Markdown(content))


def create_progress():
    """Create a progress bar context manager."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )


def print_workflow_start():
    """Print workflow start banner."""
    console.print()
    console.print("[bold]DistroKid Release Packer[/bold]")
    console.print("[dim]Starting workflow...[/dim]")
    console.print()


def print_workflow_complete(release_dir: str):
    """Print workflow completion message."""
    console.print()
    console.print("[bold green]Workflow completed successfully[/bold green]")
    console.print(f"[dim]Output directory:[/dim] {release_dir}")
    console.print()


def print_workflow_error(message: str):
    """Print workflow error message."""
    console.print()
    console.print("[bold red]Workflow Error[/bold red]")
    console.print(f"[red]{message}[/red]")
    console.print()


def print_config_summary(config: dict):
    """Print a formatted configuration summary."""
    table = Table(title="Configuration Summary", box=box.ROUNDED, show_header=True)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    table.add_row("Artist", config.get("artist", "N/A"))
    table.add_row("Title", config.get("title", "N/A"))
    table.add_row("Release Directory", config.get("release_dir", "N/A"))
    table.add_row("Genre", config.get("genre", "N/A"))
    table.add_row("BPM", str(config.get("bpm", "N/A")))
    
    console.print(table)


def print_file_list(files: list, title: str = "Files"):
    """Print a formatted list of files."""
    if not files:
        console.print(f"[dim]No {title.lower()} found.[/dim]")
        return
    
    table = Table(title=title, box=box.SIMPLE, show_header=False)
    table.add_column("File", style="cyan")
    
    for file in files:
        table.add_row(str(file))
    
    console.print(table)

