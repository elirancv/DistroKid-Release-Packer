"""
Status command - Show project status and health.
"""

import sys
from pathlib import Path
from typing import Tuple
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from datetime import datetime
import shutil

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from rich_utils import console, print_success, print_warning, print_error

app = typer.Typer(name="status", help="Show project status and health")


def check_dependency(name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a dependency is installed."""
    if import_name is None:
        import_name = name
    try:
        __import__(import_name)
        return True, "Installed"
    except ImportError:
        return False, "Not installed"


def get_disk_space(path: Path) -> dict:
    """Get disk space information."""
    try:
        stat = shutil.disk_usage(path)
        return {
            "total_gb": stat.total / (1024 ** 3),
            "used_gb": (stat.total - stat.free) / (1024 ** 3),
            "free_gb": stat.free / (1024 ** 3),
            "free_percent": (stat.free / stat.total) * 100,
        }
    except Exception:
        return None


@app.command()
def status():
    """
    Show project status and health information.
    
    Displays:
    - Dependency status
    - Recent releases
    - Disk space
    - Log file status
    - Configuration files status
    """
    from rich.panel import Panel
    console.print()
    title_panel = Panel(
        "[bold cyan]🎵 [bold magenta]DistroKid[/bold magenta] [bold cyan]Release Packer[/bold cyan]\n[dim]Project Status Dashboard[/dim]",
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(title_panel)
    console.print()
    
    project_root = Path(__file__).parent.parent.parent
    runtime_dir = project_root / "runtime"
    configs_dir = project_root / "configs"
    logs_dir = runtime_dir / "logs"
    output_dir = runtime_dir / "output"
    
    # Dependency Status
    console.print("[bold yellow]📦[/bold yellow] [bold magenta]Dependencies:[/bold magenta]")
    deps_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan on blue",
        border_style="cyan",
        title="[bold cyan]Dependencies Status[/bold cyan]"
    )
    deps_table.add_column("Package", style="bold cyan", no_wrap=True)
    deps_table.add_column("Status", style="bold", justify="center")
    deps_table.add_column("Version", style="white")
    
    dependencies = [
        ("mutagen", "mutagen"),
        ("Pillow", "PIL"),
        ("librosa", "librosa"),
        ("soundfile", "soundfile"),
        ("rich", "rich"),
        ("jsonschema", "jsonschema"),
        ("typer", "typer"),
    ]
    
    for dep_name, import_name in dependencies:
        installed, status_text = check_dependency(dep_name, import_name)
        if installed:
            try:
                module = __import__(import_name)
                version = getattr(module, "__version__", "unknown")
                status_icon = "[bold green on black]✓[/bold green on black]"
                status_text_colored = "[bold green]Installed[/bold green]"
            except Exception:
                version = "unknown"
                status_icon = "[bold green on black]✓[/bold green on black]"
                status_text_colored = "[bold green]Installed[/bold green]"
        else:
            version = "[dim]N/A[/dim]"
            status_icon = "[bold red on black]✗[/bold red on black]"
            status_text_colored = "[bold red]Missing[/bold red]"
        
        deps_table.add_row(f"[bold cyan]{dep_name}[/bold cyan]", f"{status_icon} {status_text_colored}", f"[white]{version}[/white]")
    
    console.print(deps_table)
    console.print()
    
    # Configuration Files
    console.print()
    console.print("[bold yellow]⚙️[/bold yellow]  [bold magenta]Configuration Files:[/bold magenta]")
    configs_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan on blue",
        border_style="cyan",
        title="[bold cyan]Configuration Status[/bold cyan]"
    )
    configs_table.add_column("File", style="bold cyan", no_wrap=True)
    configs_table.add_column("Status", style="bold", justify="center")
    
    config_files = [
        ("configs/release.json", "Release config"),
        ("configs/artist-defaults.json", "Artist defaults"),
    ]
    
    for file_path, description in config_files:
        full_path = project_root / file_path
        if full_path.exists():
            configs_table.add_row(f"[bold cyan]{description}[/bold cyan]", "[bold green on black]✓[/bold green on black] [bold green]Exists[/bold green]")
        else:
            example_path = project_root / file_path.replace(".json", ".example.json")
            if example_path.exists():
                configs_table.add_row(f"[bold cyan]{description}[/bold cyan]", "[bold yellow on black]⚠[/bold yellow on black] [bold yellow]Missing (example available)[/bold yellow]")
            else:
                configs_table.add_row(f"[bold cyan]{description}[/bold cyan]", "[bold red on black]✗[/bold red on black] [bold red]Missing[/bold red]")
    
    console.print(configs_table)
    console.print()
    
    # Disk Space
    console.print()
    console.print("[bold yellow]💾[/bold yellow] [bold magenta]Disk Space:[/bold magenta]")
    disk_info = get_disk_space(project_root)
    if disk_info:
        disk_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan on blue",
            border_style="cyan",
            title="[bold cyan]Disk Usage[/bold cyan]"
        )
        disk_table.add_column("Metric", style="bold cyan", no_wrap=True)
        disk_table.add_column("Value", style="bold white")
        
        disk_table.add_row("[bold cyan]Total[/bold cyan]", f"[white]{disk_info['total_gb']:.2f} GB[/white]")
        disk_table.add_row("[bold cyan]Used[/bold cyan]", f"[yellow]{disk_info['used_gb']:.2f} GB[/yellow]")
        disk_table.add_row("[bold cyan]Free[/bold cyan]", f"[green]{disk_info['free_gb']:.2f} GB[/green]")
        
        free_pct = disk_info['free_percent']
        if free_pct < 10:
            free_status = f"[bold red on black]{free_pct:.1f}%[/bold red on black]"
        elif free_pct < 20:
            free_status = f"[bold yellow on black]{free_pct:.1f}%[/bold yellow on black]"
        else:
            free_status = f"[bold green on black]{free_pct:.1f}%[/bold green on black]"
        
        disk_table.add_row("[bold cyan]Free %[/bold cyan]", free_status)
        console.print(disk_table)
    else:
        console.print("[dim]Could not determine disk space[/dim]")
    console.print()
    
    # Recent Releases
    console.print()
    console.print("[bold yellow]🎼[/bold yellow] [bold magenta]Recent Releases:[/bold magenta]")
    if output_dir.exists():
        release_dirs = sorted(
            [d for d in output_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:5]
        
        if release_dirs:
            releases_table = Table(
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan on blue",
                border_style="cyan",
                title="[bold cyan]Recent Releases[/bold cyan]"
            )
            releases_table.add_column("Release", style="bold cyan", no_wrap=True)
            releases_table.add_column("Modified", style="white")
            
            for release_dir in release_dirs:
                mtime = datetime.fromtimestamp(release_dir.stat().st_mtime)
                releases_table.add_row(f"[bold cyan]{release_dir.name}[/bold cyan]", f"[white]{mtime.strftime('%Y-%m-%d %H:%M')}[/white]")
            
            console.print(releases_table)
        else:
            console.print("[dim]No releases found[/dim]")
    else:
        console.print("[dim]Output directory does not exist[/dim]")
    console.print()
    
    # Log Files
    console.print()
    console.print("[bold yellow]📋[/bold yellow] [bold magenta]Log Files:[/bold magenta]")
    if logs_dir.exists():
        log_files = sorted(
            logs_dir.glob("*.log"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:5]
        
        if log_files:
            logs_table = Table(
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan on blue",
                border_style="cyan",
                title="[bold cyan]Log Files[/bold cyan]"
            )
            logs_table.add_column("File", style="bold cyan", no_wrap=True)
            logs_table.add_column("Size", style="white")
            logs_table.add_column("Modified", style="white")
            
            for log_file in log_files:
                size = log_file.stat().st_size
                size_mb = size / (1024 * 1024)
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                logs_table.add_row(
                    f"[bold cyan]{log_file.name}[/bold cyan]",
                    f"[white]{size_mb:.2f} MB[/white]",
                    f"[white]{mtime.strftime('%Y-%m-%d %H:%M')}[/white]"
                )
            
            console.print(logs_table)
        else:
            console.print("[dim]No log files found[/dim]")
    else:
        console.print("[dim]Logs directory does not exist[/dim]")
    console.print()
