"""
Pack command - Process a single release.
"""

import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich import box

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from orchestrator import run_release_workflow, load_config
from logger_config import setup_logging
from rich_utils import console, print_error, print_success

app = typer.Typer(name="pack", help="Process a single release")


@app.command()
def pack(
    config_path: Path = typer.Argument(..., help="Path to release.json configuration file"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Validate only, don't process"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """
    Process a single release from configuration file.
    
    This command runs the complete workflow:
    - Extract Suno version info (if provided)
    - Rename and organize audio files
    - Organize stems (if enabled)
    - Tag audio files with ID3v2 metadata
    - Validate cover art
    - Run compliance checks
    - Generate release metadata
    """
    # Initialize logging
    setup_logging(log_level="DEBUG" if debug else "INFO", log_to_file=True, log_to_console=False)
    
    if not config_path.exists():
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Config File Not Found[/bold red]\n\n"
            f"[white]Path:[/white] [yellow]{config_path}[/yellow]\n\n"
            f"[bold cyan]Quick Setup:[/bold cyan]\n"
            f"  1. Copy [cyan]configs/release.example.json[/cyan] to [cyan]configs/release.json[/cyan]\n"
            f"  2. Edit [cyan]configs/release.json[/cyan] with your track details\n"
            f"  3. Run: [bold cyan]distrokid pack configs/release.json[/bold cyan]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    
    try:
        # Load config first (needed for both dry-run and normal execution)
        config = load_config(str(config_path), validate=True)
        
        if dry_run:
            validation_panel = Panel(
                f"[bold bright_cyan]🔍 Validating Configuration[/bold bright_cyan]\n\n"
                f"[white]Config:[/white] [bold cyan]{config_path}[/bold cyan]",
                border_style="cyan",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print()
            console.print(validation_panel)
            console.print()
            
            # Display configuration in Rich table format
            from rich_utils import print_config_table
            print_config_table(config, "Configuration")
            console.print()
            
            success_panel = Panel(
                f"[bold green on black]✓[/bold green on black] [bold green]Configuration is Valid[/bold green]\n\n"
                f"[dim]All checks passed. Run without --dry-run to process the release.[/dim]",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print()
            console.print(success_panel)
            console.print()
            raise typer.Exit(0)
        
        loading_panel = Panel(
            f"[bold bright_cyan]📦 Processing Release[/bold bright_cyan]\n\n"
            f"[white]Config:[/white] [bold cyan]{config_path}[/bold cyan]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(loading_panel)
        console.print()
        
        # Display configuration in Rich table format
        from rich_utils import print_config_table
        print_config_table(config, "Configuration")
        console.print()
        
        # Enable debug mode in config if requested
        if debug:
            config["debug"] = True
        
        success = run_release_workflow(config, config_path=str(config_path))
        
        if success:
            success_panel = Panel(
                f"[bold green on black]✓[/bold green on black] [bold green]Release Packed Successfully![/bold green]\n\n"
                f"[dim]Check runtime/output/ for your processed files.[/dim]",
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print()
            console.print(success_panel)
            console.print()
        else:
            error_panel = Panel(
                f"[bold red on black]❌[/bold red on black] [bold red]Release Processing Failed[/bold red]\n\n"
                f"[dim]Check the logs for details: [cyan]distrokid logs view[/cyan][/dim]",
                border_style="red",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print()
            console.print(error_panel)
            console.print()
        
        raise typer.Exit(0 if success else 1)
        
    except ValueError as e:
        # Check if error message already contains Rich markup
        error_msg = str(e)
        if "❌" in error_msg or "[bold" in error_msg:
            # Already formatted with Rich
            error_panel = Panel(
                error_msg,
                border_style="red",
                box=box.DOUBLE,
                padding=(1, 2)
            )
        else:
            error_panel = Panel(
                f"[bold red on black]❌[/bold red on black] [bold red]Configuration Error[/bold red]\n\n"
                f"[white]{error_msg}[/white]\n\n"
                f"[bold cyan]Troubleshooting:[/bold cyan]\n"
                f"  • Validate JSON syntax (use jsonlint.com or similar)\n"
                f"  • Check that all required fields are present\n"
                f"  • Verify fields are not empty\n"
                f"  • Ensure file is saved as UTF-8 encoding\n"
                f"  • See [cyan]configs/release.example.json[/cyan] for reference",
                border_style="red",
                box=box.DOUBLE,
                padding=(1, 2)
            )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    except ImportError as e:
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Dependency Error[/bold red]\n\n"
            f"[white]Missing module:[/white] [yellow]{e}[/yellow]\n\n"
            f"[bold cyan]Solution:[/bold cyan]\n"
            f"  • Install missing dependencies: [bold cyan]pip install -r requirements.txt[/bold cyan]\n"
            f"  • Or install specific package: [bold cyan]pip install {str(e).split()[-1]}[/bold cyan]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    except Exception as e:
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Unexpected Error[/bold red]\n\n"
            f"[white]Error:[/white] [yellow]{e}[/yellow]\n\n"
            f"[bold cyan]Troubleshooting:[/bold cyan]\n"
            f"  • Check that release.json is valid JSON\n"
            f"  • Verify all file paths exist\n"
            f"  • See [cyan]docs/QUICK_START.md[/cyan] for help\n"
            f"  • Run with [cyan]--debug[/cyan] for detailed traceback",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        if debug:
            from rich.traceback import install
            install(show_locals=True)
            console.print_exception()
        raise typer.Exit(1)
