"""
Config command - Manage configuration files.
"""

import sys
import json
import shutil
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
from rich import box

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from rich_utils import console, print_success, print_error, print_warning, print_info

app = typer.Typer(name="config", help="Manage configuration files")


@app.command()
def show(
    config_path: Path = typer.Argument(..., help="Path to configuration file"),
):
    """
    Display configuration file with Rich JSON formatting.
    
    Example:
        distrokid config show configs/release.json
        distrokid config show configs/artist-defaults.json
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
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        from rich.panel import Panel
        from rich_utils import print_config_table
        console.print()
        title_panel = Panel(
            f"[bold bright_cyan]⚙️  Configuration File[/bold bright_cyan]\n[dim white]{config_path}[/dim white]",
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(title_panel)
        console.print()
        
        # Display configuration in Rich table format instead of JSON
        print_config_table(config_data, "Configuration")
        console.print()
        
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
    except json.JSONDecodeError as e:
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Invalid JSON[/bold red]\n\n"
            f"[white]File:[/white] [yellow]{config_path}[/yellow]\n"
            f"[white]Error:[/white] [yellow]{e}[/yellow]\n\n"
            f"[bold cyan]Solution:[/bold cyan]\n"
            f"  • Validate JSON syntax (use jsonlint.com or similar)\n"
            f"  • Check for missing commas, brackets, or quotes\n"
            f"  • Ensure file is valid JSON format",
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
            f"[bold red on black]❌[/bold red on black] [bold red]Error[/bold red]\n\n"
            f"[white]Error:[/white] [yellow]{e}[/yellow]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)


@app.command()
def create(
    config_type: str = typer.Argument(..., help="Type of config: 'release' or 'artist-defaults'"),
    output_path: Path = typer.Option(None, "--output", "-o", help="Output path (default: configs/{type}.json)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
):
    """
    Create a new configuration file from example.
    
    Example:
        distrokid config create release
        distrokid config create artist-defaults
        distrokid config create release --output my-release.json
    """
    project_root = Path(__file__).parent.parent.parent
    configs_dir = project_root / "configs"
    
    # Determine example file and output file
    if config_type.lower() in ["release", "release.json"]:
        example_file = configs_dir / "release.example.json"
        default_output = configs_dir / "release.json"
    elif config_type.lower() in ["artist-defaults", "artist-defaults.json", "artist"]:
        example_file = configs_dir / "artist-defaults.example.json"
        default_output = configs_dir / "artist-defaults.json"
    else:
        console.print(f"[bold bright_red]❌ Error:[/bold bright_red] [bright_red]Unknown config type:[/bright_red] [bright_yellow]{config_type}[/bright_yellow]")
        console.print("  [bright_cyan]Valid types:[/bright_cyan] [bright_white]'release' or 'artist-defaults'[/bright_white]")
        raise typer.Exit(1)
    
    if output_path is None:
        output_path = default_output
    elif output_path.is_dir():
        output_path = output_path / default_output.name
    
    # Check if example exists
    if not example_file.exists():
        console.print(f"[bold bright_red]❌ Error:[/bold bright_red] [bright_red]Example file not found:[/bright_red] [bright_yellow]{example_file}[/bright_yellow]")
        raise typer.Exit(1)
    
    # Check if output exists
    if output_path.exists() and not force:
        console.print(f"[bold bright_red]❌ Error:[/bold bright_red] [bright_red]File already exists:[/bright_red] [bright_yellow]{output_path}[/bright_yellow]")
        console.print("  [bright_cyan]Use --force to overwrite[/bright_cyan]")
        raise typer.Exit(1)
    
    try:
        # Copy example to output
        shutil.copy2(example_file, output_path)
        from rich.panel import Panel
        success_panel = Panel(
            f"[bold bright_green]✓ Created configuration file:[/bold bright_green] [bright_white]{output_path}[/bright_white]",
            title="[bold bright_green]🎉 Success[/bold bright_green]",
            border_style="bright_green",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(success_panel)
        console.print()
        console.print("[bold bright_cyan]💡 Next steps:[/bold bright_cyan]")
        console.print(f"  [bright_cyan]1.[/bright_cyan] Edit [bright_white]{output_path}[/bright_white] with your details")
        console.print(f"  [bright_cyan]2.[/bright_cyan] Run: [bold bright_cyan]distrokid config show {output_path}[/bold bright_cyan] to view")
        console.print()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to create config: {e}")
        raise typer.Exit(1)


@app.command()
def edit(
    config_path: Path = typer.Argument(..., help="Path to configuration file"),
    editor: str = typer.Option(None, "--editor", "-e", help="Editor to use (default: system default)"),
):
    """
    Open configuration file in editor.
    
    Example:
        distrokid config edit configs/release.json
        distrokid config edit configs/release.json --editor code
    """
    if not config_path.exists():
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Config File Not Found[/bold red]\n\n"
            f"[white]Path:[/white] [yellow]{config_path}[/yellow]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    
    import subprocess
    import os
    
    # Determine editor
    if editor:
        editor_cmd = editor
    else:
        # Try to find default editor
        editor_cmd = os.environ.get("EDITOR")
        if not editor_cmd:
            # Fallback to common editors
            if sys.platform == "win32":
                editor_cmd = "notepad"
            elif sys.platform == "darwin":
                editor_cmd = "open"
            else:
                editor_cmd = "nano"
    
    try:
        # Open file in editor
        if sys.platform == "win32" and editor_cmd == "notepad":
            subprocess.Popen([editor_cmd, str(config_path)])
        elif sys.platform == "darwin" and editor_cmd == "open":
            subprocess.Popen([editor_cmd, "-t", str(config_path)])
        else:
            subprocess.run([editor_cmd, str(config_path)])
        
        print_success(f"Opened {config_path} in {editor_cmd}")
        
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Editor not found: {editor_cmd}")
        console.print("  Please specify an editor with --editor")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to open editor: {e}")
        raise typer.Exit(1)


@app.command()
def list(
    configs_dir: Path = typer.Option(None, "--dir", "-d", help="Directory to search (default: configs/)"),
):
    """
    List all configuration files.
    
    Example:
        distrokid config list
        distrokid config list --dir ./my-configs
    """
    project_root = Path(__file__).parent.parent.parent
    
    if configs_dir is None:
        configs_dir = project_root / "configs"
    
    if not configs_dir.exists():
        error_panel = Panel(
            f"[bold red on black]❌[/bold red on black] [bold red]Directory Not Found[/bold red]\n\n"
            f"[white]Path:[/white] [yellow]{configs_dir}[/yellow]",
            border_style="red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print()
        console.print(error_panel)
        console.print()
        raise typer.Exit(1)
    
    # Find all JSON files
    config_files = sorted(configs_dir.glob("*.json"))
    
    if not config_files:
        console.print(f"[dim]No configuration files found in {configs_dir}[/dim]")
        raise typer.Exit(0)
    
    # Create table
    table = Table(
        title=f"[bold bright_cyan]📁 Configuration Files in {configs_dir}[/bold bright_cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan on bright_blue",
        border_style="bright_cyan"
    )
    table.add_column("File", style="bold bright_cyan", no_wrap=True)
    table.add_column("Type", style="bold bright_magenta")
    table.add_column("Status", style="bold", justify="center")
    table.add_column("Size", style="bright_white")
    
    for config_file in config_files:
        file_name = config_file.name
        is_example = "example" in file_name.lower()
        file_type = "Example" if is_example else "Active"
        
        try:
            size = config_file.stat().st_size
            size_kb = size / 1024
            size_str = f"{size_kb:.1f} KB"
        except Exception:
            size_str = "N/A"
        
        if is_example:
            status = "[bright_yellow]Template[/bright_yellow]"
        else:
            status = "[bold bright_green]Active[/bold bright_green]"
        
        table.add_row(f"[bright_cyan]{file_name}[/bright_cyan]", f"[bright_magenta]{file_type}[/bright_magenta]", status, f"[bright_white]{size_str}[/bright_white]")
    
    console.print()
    console.print(table)
    console.print()
