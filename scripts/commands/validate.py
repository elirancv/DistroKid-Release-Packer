"""
Validate command - Validate configuration files.
"""

import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from validate_config import validate_release_config, validate_artist_defaults
from rich_utils import console, print_success, print_error, print_warning

app = typer.Typer(name="validate", help="Validate configuration files")


@app.command()
def validate(
    config_path: Path = typer.Argument(..., help="Path to configuration file"),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="Enable strict validation"),
    schema: bool = typer.Option(False, "--schema", "-s", help="Show schema details"),
):
    """
    Validate a configuration file against the schema.
    
    This command checks:
    - JSON syntax validity
    - Required fields presence
    - Field types and formats
    - Schema compliance
    
    Example:
        distrokid validate configs/release.json
        distrokid validate configs/release.json --no-strict
        distrokid validate configs/artist-defaults.json
    """
    if not config_path.exists():
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Config File Not Found[/bold red]\n\n"
            f"[white]Path:[/white] [yellow]{config_path}[/yellow]\n\n"
            f"[bold cyan]Solution:[/bold cyan]\n"
            f"  • Verify the file path is correct\n"
            f"  • Check that the file exists in the specified location",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    
    # Determine config type
    is_artist_defaults = "artist-defaults" in config_path.name.lower()
    
    try:
        if is_artist_defaults:
            is_valid, errors = validate_artist_defaults(config_path, strict=strict)
        else:
            is_valid, errors = validate_release_config(config_path, strict=strict)
        
        # Create results table with beautiful styling
        table = Table(
            title="[bold bright_cyan]🔍 Validation Results[/bold bright_cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold bright_cyan on bright_blue",
            border_style="bright_cyan"
        )
        table.add_column("Check", style="bold bright_cyan", no_wrap=True)
        table.add_column("Status", style="bold", justify="center")
        table.add_column("Details", style="bright_white")
        
        # File existence
        table.add_row("[bright_cyan]📄 File exists[/bright_cyan]", "[bold bright_green]✓[/bold bright_green]", f"[bright_white]{config_path}[/bright_white]")
        
        # JSON syntax and UTF-8 encoding
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                json.load(f)
            table.add_row("[bright_cyan]📋 JSON syntax[/bright_cyan]", "[bold bright_green]✓[/bold bright_green]", "[bright_green]Valid JSON[/bright_green]")
            table.add_row("[bright_cyan]🔤 UTF-8 encoding[/bright_cyan]", "[bold bright_green]✓[/bold bright_green]", "[bright_green]Valid UTF-8[/bright_green]")
        except UnicodeDecodeError as e:
            table.add_row("[bright_cyan]📋 JSON syntax[/bright_cyan]", "[bold bright_red]✗[/bold bright_red]", "[bright_red]Cannot parse (encoding error)[/bright_red]")
            table.add_row("[bright_cyan]🔤 UTF-8 encoding[/bright_cyan]", "[bold bright_red]✗[/bold bright_red]", f"[bright_red]Invalid UTF-8: {e}[/bright_red]")
            is_valid = False
            errors.insert(0, f"File encoding error: {e}. Save file as UTF-8 encoding.")
        except json.JSONDecodeError as e:
            table.add_row("[bright_cyan]📋 JSON syntax[/bright_cyan]", "[bold bright_red]✗[/bold bright_red]", f"[bright_red]Invalid JSON: {e}[/bright_red]")
            table.add_row("[bright_cyan]🔤 UTF-8 encoding[/bright_cyan]", "[bold bright_green]✓[/bold bright_green]", "[bright_green]Valid UTF-8[/bright_green]")
            is_valid = False
        
        # Schema validation
        if is_valid:
            table.add_row("[bright_cyan]✅ Schema validation[/bright_cyan]", "[bold bright_green]✓[/bold bright_green]", "[bright_green]Passed[/bright_green]")
        else:
            table.add_row("[bright_cyan]✅ Schema validation[/bright_cyan]", "[bold bright_red]✗[/bold bright_red]", f"[bright_red]{len(errors)} error(s)[/bright_red]")
        
        console.print()
        console.print(table)
        console.print()
        
        # Show errors if any with beautiful formatting
        if errors:
            from rich.panel import Panel
            error_text = "\n".join(f"  [bright_red]•[/bright_red] [bright_white]{error}[/bright_white]" for error in errors)
            error_panel = Panel(
                error_text,
                title="[bold bright_red]⚠️  Validation Errors[/bold bright_red]",
                border_style="bright_red",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print(error_panel)
            console.print()
        
        # Show schema info if requested
        if schema:
            console.print()
            schema_path = Path(__file__).parent.parent.parent / "schemas"
            if is_artist_defaults:
                schema_file = schema_path / "artist_defaults_schema.json"
            else:
                schema_file = schema_path / "release_schema.json"
            
            if schema_file.exists():
                console.print(f"[bold]Schema file:[/bold] {schema_file}")
                try:
                    import json
                    with open(schema_file, "r", encoding="utf-8") as f:
                        schema_data = json.load(f)
                    from rich.json import JSON
                    console.print(JSON.from_data(schema_data))
                except Exception as e:
                    console.print(f"[dim]Could not display schema: {e}[/dim]")
            else:
                console.print(f"[yellow]Schema file not found: {schema_file}[/yellow]")
        
        if is_valid:
            from rich.panel import Panel
            success_panel = Panel(
                "[bold bright_green]✓ Configuration is valid![/bold bright_green]",
                title="[bold bright_green]🎉 Success[/bold bright_green]",
                border_style="bright_green",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print(success_panel)
            raise typer.Exit(0)
        else:
            from rich.panel import Panel
            fail_panel = Panel(
                "[bold bright_red]✗ Configuration validation failed[/bold bright_red]",
                title="[bold bright_red]❌ Validation Failed[/bold bright_red]",
                border_style="bright_red",
                box=box.DOUBLE,
                padding=(1, 2)
            )
            console.print(fail_panel)
            raise typer.Exit(1)
            
    except UnicodeDecodeError as e:
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Encoding Error[/bold red]\n\n"
            f"[white]File:[/white] [yellow]{config_path}[/yellow]\n"
            f"[white]Error:[/white] [yellow]{e}[/yellow]\n\n"
            f"[bold cyan]Solution:[/bold cyan]\n"
            f"  • Open the file in a text editor (VS Code, Notepad++)\n"
            f"  • Save it with UTF-8 encoding (File → Save As → Encoding: UTF-8)\n"
            f"  • Ensure no binary data or special characters are corrupted",
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
            f"[bold red on black]❌[/bold red on black] [bold red]Validation Error[/bold red]\n\n"
            f"[white]Error:[/white] [yellow]{e}[/yellow]\n\n"
            f"[bold cyan]Troubleshooting:[/bold cyan]\n"
            f"  • Verify the file is valid JSON\n"
            f"  • Check file permissions\n"
            f"  • Ensure file is saved as UTF-8 encoding",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        if schema:
            from rich.traceback import install
            install(show_locals=True)
            console.print_exception()
        raise typer.Exit(1)
