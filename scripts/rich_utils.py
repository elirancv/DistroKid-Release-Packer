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

# Global console instance with forced colors for maximum vibrancy
console = Console(force_terminal=True, color_system="truecolor")


def print_success(message: str):
    """Print a success message with vibrant colors."""
    console.print(f"[bold green on black]✓[/bold green on black] [bold green]{message}[/bold green]")


def print_error(message: str):
    """Print an error message with vibrant colors."""
    console.print(f"[bold red on black]✗[/bold red on black] [bold red]{message}[/bold red]")


def print_warning(message: str):
    """Print a warning message with vibrant colors."""
    console.print(f"[bold yellow on black]⚠[/bold yellow on black] [bold yellow]{message}[/bold yellow]")


def print_info(message: str):
    """Print an info message with vibrant colors."""
    console.print(f"[bold cyan on black]ℹ[/bold cyan on black] [bold cyan]{message}[/bold cyan]")


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


def print_config_table(config: dict, title: str = "Configuration"):
    """Print configuration as a professional Rich table."""
    table = Table(
        title=f"[bold cyan]{title}[/bold cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
        padding=(0, 1)
    )
    table.add_column("Setting", style="bold white", no_wrap=True)
    table.add_column("Value", style="cyan")
    
    # Core fields
    if "title" in config:
        table.add_row("Title", f"[bold]{config['title']}[/bold]")
    if "artist" in config:
        table.add_row("Artist", f"[bold]{config['artist']}[/bold]")
    if "genre" in config:
        table.add_row("Genre", str(config["genre"]))
    if "bpm" in config:
        table.add_row("BPM", str(config["bpm"]))
    if "release_date" in config:
        table.add_row("Release Date", str(config["release_date"]))
    if "release_dir" in config:
        table.add_row("Release Directory", f"[dim]{config['release_dir']}[/dim]")
    
    # Boolean flags
    if "tag_audio" in config:
        status = "[bold green]✓ Enabled[/bold green]" if config["tag_audio"] else "[dim]Disabled[/dim]"
        table.add_row("Tag Audio", status)
    if "validate_cover" in config:
        status = "[bold green]✓ Enabled[/bold green]" if config["validate_cover"] else "[dim]Disabled[/dim]"
        table.add_row("Validate Cover", status)
    if "validate_compliance" in config:
        status = "[bold green]✓ Enabled[/bold green]" if config["validate_compliance"] else "[dim]Disabled[/dim]"
        table.add_row("Validate Compliance", status)
    if "organize_stems" in config:
        status = "[bold green]✓ Enabled[/bold green]" if config["organize_stems"] else "[dim]Disabled[/dim]"
        table.add_row("Organize Stems", status)
    if "tag_stems" in config:
        status = "[bold green]✓ Enabled[/bold green]" if config["tag_stems"] else "[dim]Disabled[/dim]"
        table.add_row("Tag Stems", status)
    
    # URLs and paths
    if "suno_url" in config and config["suno_url"]:
        table.add_row("Suno URL", f"[dim]{config['suno_url']}[/dim]")
    if "suno_metadata_file" in config and config["suno_metadata_file"]:
        table.add_row("Suno Metadata File", f"[dim]{config['suno_metadata_file']}[/dim]")
    if "source_audio_dir" in config and config["source_audio_dir"]:
        table.add_row("Source Audio Dir", f"[dim]{config['source_audio_dir']}[/dim]")
    if "source_stems_dir" in config and config["source_stems_dir"]:
        table.add_row("Source Stems Dir", f"[dim]{config['source_stems_dir']}[/dim]")
    if "cover_art_path" in config and config["cover_art_path"]:
        table.add_row("Cover Art Path", f"[dim]{config['cover_art_path']}[/dim]")
    
    # Additional fields (display as-is for other keys)
    for key, value in config.items():
        if key not in ["title", "artist", "genre", "bpm", "release_date", "release_dir",
                      "tag_audio", "validate_cover", "validate_compliance", "organize_stems", "tag_stems",
                      "suno_url", "suno_metadata_file", "source_audio_dir", "source_stems_dir", "cover_art_path",
                      "debug", "_comment", "_comments"]:
            if isinstance(value, bool):
                status = "[bold green]✓ Enabled[/bold green]" if value else "[dim]Disabled[/dim]"
                table.add_row(key.replace("_", " ").title(), status)
            elif value is not None and value != "":
                table.add_row(key.replace("_", " ").title(), str(value))
    
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

