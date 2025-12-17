"""
Batch command - Process multiple releases.
"""

import sys
from pathlib import Path
import typer
from rich.console import Console

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from batch_processor import process_batch
from logger_config import setup_logging
from rich_utils import console

app = typer.Typer(name="batch", help="Process multiple releases in batch")


@app.command()
def batch(
    directory: Path = typer.Argument(..., help="Directory containing release.json files"),
    pattern: str = typer.Option("release*.json", "--pattern", "-p", help="File pattern to match"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate only, don't process"),
    continue_on_error: bool = typer.Option(True, "--continue-on-error/--stop-on-error", help="Continue processing on errors"),
):
    """
    Process multiple releases in batch.
    
    This command finds all release configuration files matching the pattern
    in the specified directory and processes them sequentially.
    
    Example:
        distrokid batch ./releases
        distrokid batch ./releases --pattern "release-*.json"
        distrokid batch ./releases --dry-run
    """
    # Initialize logging
    setup_logging(log_level="INFO", log_to_file=True, log_to_console=False)
    
    from rich.panel import Panel
    from rich import box
    
    if not directory.exists():
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Directory Not Found[/bold red]\n\n"
            f"[white]Path:[/white] [yellow]{directory}[/yellow]\n\n"
            f"[bold cyan]Solution:[/bold cyan]\n"
            f"  • Verify the directory path is correct\n"
            f"  • Ensure the directory exists before running batch",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    
    if not directory.is_dir():
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Path is Not a Directory[/bold red]\n\n"
            f"[white]Path:[/white] [yellow]{directory}[/yellow]\n\n"
            f"[bold cyan]Solution:[/bold cyan]\n"
            f"  • Provide a directory path, not a file path",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    
    try:
        batch_panel = Panel(
            f"[bold bright_cyan]📦 Batch Processing[/bold bright_cyan]\n\n"
            f"[white]Directory:[/white] [bold cyan]{directory}[/bold cyan]\n"
            f"[white]Pattern:[/white] [bold cyan]{pattern}[/bold cyan]\n"
            f"[white]Mode:[/white] [bold cyan]{'Dry Run (Validation Only)' if dry_run else 'Full Processing'}[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(batch_panel)
        console.print()
        
        results = process_batch(
            config_dir=directory,
            pattern=pattern,
            continue_on_error=continue_on_error,
            dry_run=dry_run,
        )
        
        # Exit with error code if any failed
        failed = sum(1 for r in results.values() if r.get("status") == "error")
        success_count = sum(1 for r in results.values() if r.get("status") == "success")
        total = len(results)
        
        if failed == 0:
            success_panel = Panel(
                f"[bold green on black]✓[/bold green on black] [bold green]Batch Processing Complete[/bold green]\n\n"
                f"[white]Processed:[/white] [bold green]{success_count}/{total}[/bold green] releases\n"
                f"[dim]Check runtime/output/ for processed files.[/dim]",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print()
            console.print(success_panel)
            console.print()
        else:
            error_panel = Panel(
                f"[bold red on black]❌[/bold red on black] [bold red]Batch Processing Completed with Errors[/bold red]\n\n"
                f"[white]Success:[/white] [bold green]{success_count}[/bold green] | "
                f"[white]Failed:[/white] [bold red]{failed}[/bold red] | "
                f"[white]Total:[/white] [bold cyan]{total}[/bold cyan]\n\n"
                f"[dim]Check the logs for details: [cyan]distrokid logs view[/cyan][/dim]",
                border_style="red",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print()
            console.print(error_panel)
            console.print()
        
        raise typer.Exit(1 if failed > 0 else 0)
        
    except Exception as e:
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Batch Processing Failed[/bold red]\n\n"
            f"[white]Error:[/white] [yellow]{e}[/yellow]\n\n"
            f"[bold cyan]Troubleshooting:[/bold cyan]\n"
            f"  • Verify all config files are valid JSON\n"
            f"  • Check file permissions\n"
            f"  • See [cyan]docs/QUICK_START.md[/cyan] for help",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
