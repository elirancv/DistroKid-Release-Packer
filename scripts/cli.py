#!/usr/bin/env python3
"""
DistroKid Release Packer - Main Rich CLI

Modern command-line interface using Typer and Rich for managing releases.
"""

import sys
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == 'win32':
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

import typer
from rich.console import Console
from rich.panel import Panel
from rich import box
from typing import Optional

# Initialize Rich console with forced colors
console = Console(force_terminal=True, color_system="truecolor")

# Create Typer app
app = typer.Typer(
    name="distrokid",
    help="DistroKid Release Packer - CLI for managing music releases",
    add_completion=False,
    rich_markup_mode="rich",
)

# Import and register command modules
from commands import config, logs
from commands.pack import pack as pack_command
from commands.batch import batch as batch_command
from commands.validate import validate as validate_command
from commands.status import status as status_command
from commands.init import init as init_command
from commands.check import check as check_command

# Register commands with subcommands as typer apps
app.add_typer(config.app, name="config")
app.add_typer(logs.app, name="logs")

# Register direct commands
app.command()(pack_command)
app.command()(batch_command)
app.command()(validate_command)
app.command()(status_command)
app.command()(init_command)
app.command()(check_command)


def version_callback(value: bool):
    """Show version information."""
    if value:
        try:
            # Try to read version from pyproject.toml
            import re
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                content = pyproject_path.read_text(encoding='utf-8')
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version = match.group(1)
                else:
                    version = "1.0.0"
            else:
                version = "1.0.0"
        except Exception:
            version = "1.0.0"
        
        from rich.panel import Panel
        version_panel = Panel(
            f"[bold bright_cyan]🎵 [bold bright_magenta]DistroKid[/bold bright_magenta] [bold bright_cyan]Release Packer[/bold bright_cyan][/bold bright_cyan]\n[bold bright_magenta]Version:[/bold bright_magenta] [bright_white]{version}[/bright_white]",
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(version_panel)
        raise typer.Exit()


def main():
    """Main entry point for the CLI."""
    app()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit",
    ),
):
    """
    DistroKid Release Packer - CLI for managing music releases.
    
    Automate the complete workflow from Suno export to DistroKid-ready files.
    """
    pass


if __name__ == "__main__":
    app()
