#!/usr/bin/env python3
"""
DistroKid Release Packer - Main CLI Entry Point

Simple command-line interface for the release packer.
Usage: python pack.py [command] [options]
"""

import sys
import json
import os
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for Windows console
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Fallback for older Python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add scripts to path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from orchestrator import run_release_workflow, load_config
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich import box

console = Console()


def show_help():
    """Show help message."""
    help_text = """
[bold cyan]DistroKid Release Packer - CLI Tool[/bold cyan]

[bold]USAGE:[/bold]
  [green]python pack.py <release.json>[/green]           Run complete workflow
  [green]python pack.py --help[/green]                  Show this help
  [green]python pack.py --example[/green]                Show example config

[bold]COMMANDS:[/bold]
  [cyan]pack <release.json>[/cyan]                     Process release with config file
  
[bold]EXAMPLES:[/bold]
  [dim]python pack.py release.json[/dim]
  [dim]python pack.py my-release.json[/dim]

[bold]QUICK START:[/bold]
  1. Copy release.example.json to release.json
  2. Edit release.json with your track details
  3. Run: [green]python pack.py release.json[/green]

[bold]For more info, see:[/bold]
  - docs/QUICK_START.md
  - scripts/README.md
  - docs/HOW_IT_WORKS.md
"""
    panel = Panel(help_text, title="[bold green]Help[/bold green]", border_style="green", box=box.ROUNDED)
    console.print(panel)


def show_example_config():
    """Show example configuration."""
    example = {
        "artist": "Your Artist Name",
        "title": "Your Track Title",
        "release_dir": "./Releases/YourTrack",
        "suno_url": "https://suno.com/song/your-track-id?v=3.5.2",
        "source_audio_dir": "./exports",
        "source_stems_dir": "./exports/stems",
        "genre": "Deep House",
        "bpm": 122,
        "id3_metadata": {
            "album": "Your Album Name",
            "year": "2025",
            "composer": "Your Name + Suno AI",
            "publisher": "Independent"
        },
        "organize_stems": True,
        "tag_stems": False,
        "tag_audio": True,
        "validate_compliance": True,
        "strict_mode": False
    }
    
    console.print()
    console.print("[bold]Example release.json:[/bold]")
    json_obj = JSON.from_data(example)
    console.print(json_obj)
    console.print()
    console.print("[dim]Save this as 'release.json' and edit with your details.[/dim]")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command in ["--help", "-h", "help"]:
        show_help()
        sys.exit(0)
    
    if command in ["--example", "-e", "example"]:
        show_example_config()
        sys.exit(0)
    
    # Assume it's a config file path
    config_path = command
    
    if not Path(config_path).exists():
        console.print(f"[bold red][ERROR] Config file not found:[/bold red] {config_path}")
        console.print()
        console.print("[bold]Create a config file first:[/bold]")
        console.print("  [cyan]1.[/cyan] Copy release.example.json to release.json")
        console.print("  [cyan]2.[/cyan] Edit release.json with your track details")
        console.print("  [cyan]3.[/cyan] Run: [green]python pack.py release.json[/green]")
        sys.exit(1)
    
    try:
        console.print(f"[bold]Loading configuration:[/bold] {config_path}")
        console.print()
        config = load_config(config_path)
        success = run_release_workflow(config)
        
        # Exit with appropriate code (orchestrator already prints status messages)
        sys.exit(0 if success else 1)
            
    except ValueError as e:
        console.print()
        console.print(f"[bold red]✗ Configuration Error:[/bold red] {e}")
        console.print()
        console.print("[bold]Troubleshooting:[/bold]")
        console.print("  [cyan]-[/cyan] Validate JSON syntax (use jsonlint.com or similar)")
        console.print("  [cyan]-[/cyan] Check that all required fields are present")
        console.print("  [cyan]-[/cyan] Verify fields are not empty")
        console.print("  [cyan]-[/cyan] See config.example.json for reference")
        sys.exit(1)
    except ImportError as e:
        console.print()
        console.print(f"[bold red]✗ Dependency Error:[/bold red] {e}")
        console.print()
        console.print("[bold]Troubleshooting:[/bold]")
        console.print("  [cyan]-[/cyan] Install missing dependencies: [green]pip install -r requirements.txt[/green]")
        sys.exit(1)
    except Exception as e:
        console.print()
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        console.print()
        console.print("[bold]Troubleshooting:[/bold]")
        console.print("  [cyan]-[/cyan] Check that release.json is valid JSON")
        console.print("  [cyan]-[/cyan] Verify all file paths exist")
        console.print("  [cyan]-[/cyan] See docs/QUICK_START.md for help")
        sys.exit(1)


if __name__ == "__main__":
    main()

