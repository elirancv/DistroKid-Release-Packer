"""
Logs command - View and manage log files.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich import box

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from rich_utils import console, print_success, print_error, print_warning

app = typer.Typer(name="logs", help="View and manage log files")


def get_logs_dir() -> Path:
    """Get the logs directory path."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "runtime" / "logs"


@app.command(name="list")
def list_logs():
    """
    List all log files.
    
    Example:
        distrokid logs list
    """
    logs_dir = get_logs_dir()
    
    if not logs_dir.exists():
        console.print(f"[dim]Logs directory does not exist: {logs_dir}[/dim]")
        raise typer.Exit(0)
    
    log_files = sorted(
        logs_dir.glob("*.log"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not log_files:
        console.print("[dim]No log files found[/dim]")
        raise typer.Exit(0)
    
    table = Table(
        title="[bold cyan]📋 Log Files[/bold cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan on blue",
        border_style="cyan"
    )
    table.add_column("File", style="bold cyan", no_wrap=True)
    table.add_column("Size", style="white")
    table.add_column("Modified", style="white")
    
    for log_file in log_files:
        try:
            size = log_file.stat().st_size
            size_mb = size / (1024 * 1024)
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            table.add_row(
                f"[bold cyan]{log_file.name}[/bold cyan]",
                f"[white]{size_mb:.2f} MB[/white]",
                f"[white]{mtime.strftime('%Y-%m-%d %H:%M:%S')}[/white]"
            )
        except Exception:
            table.add_row(f"[bold cyan]{log_file.name}[/bold cyan]", "[dim]N/A[/dim]", "[dim]N/A[/dim]")
    
    console.print()
    console.print(table)
    console.print()


@app.command()
def view(
    log_file: Path = typer.Argument(None, help="Log file to view (default: most recent)"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log file (like tail -f)"),
):
    """
    View log file with syntax highlighting.
    
    Example:
        distrokid logs view
        distrokid logs view release_packer_20251217.log
        distrokid logs view --lines 100
        distrokid logs view --follow
    """
    logs_dir = get_logs_dir()
    
    if not logs_dir.exists():
        console.print(f"[bold red on black]❌[/bold red on black] [bold red]Error:[/bold red] [red]Logs directory does not exist:[/red] [yellow]{logs_dir}[/yellow]")
        raise typer.Exit(1)
    
    # If no file specified, use most recent
    if log_file is None:
        log_files = sorted(
            logs_dir.glob("*.log"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if not log_files:
            console.print("[bold red on black]❌[/bold red on black] [bold red]Error:[/bold red] [red]No log files found[/red]")
            raise typer.Exit(1)
        log_file = log_files[0]
        console.print(f"[dim]Using most recent log:[/dim] [bold cyan]{log_file.name}[/bold cyan]")
        console.print()
    else:
        # If relative path, check in logs dir
        if not log_file.is_absolute():
            log_file = logs_dir / log_file
    
    if not log_file.exists():
        console.print(f"[bold red on black]❌[/bold red on black] [bold red]Error:[/bold red] [red]Log file not found:[/red] [yellow]{log_file}[/yellow]")
        raise typer.Exit(1)
    
    try:
        if follow:
            # Follow mode (like tail -f)
            from rich.panel import Panel
            follow_panel = Panel(
                f"[bold cyan]📋 Following log file:[/bold cyan] [white]{log_file.name}[/white]\n[dim]Press Ctrl+C to stop[/dim]",
                border_style="cyan",
                box=box.ROUNDED
            )
            console.print(follow_panel)
            console.print()
            
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    # Go to end of file
                    f.seek(0, 2)
                    
                    while True:
                        line = f.readline()
                        if line:
                            # Filter out test-related entries
                            if "pytest-of-" in line or ("AppData\\Local\\Temp\\pytest" in line and "ERROR" not in line):
                                continue
                            # Remove trailing newline for syntax highlighting
                            line = line.rstrip("\n\r")
                            syntax = Syntax(line, "log", theme="monokai", word_wrap=True)
                            console.print(syntax)
                        else:
                            time.sleep(0.1)
            except KeyboardInterrupt:
                console.print()
                console.print("[dim]Stopped following[/dim]")
        else:
            # Read last N lines
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            from rich.panel import Panel
            info_panel = Panel(
                f"[bold cyan]📋 Log file:[/bold cyan] [white]{log_file.name}[/white]\n[dim]Showing last {len(last_lines)} lines[/dim]",
                border_style="cyan",
                box=box.ROUNDED
            )
            console.print(info_panel)
            console.print()
            
            # Filter out test-related entries for cleaner output
            filtered_lines = []
            for line in last_lines:
                # Skip pytest test files and temporary test directories
                is_test_file = (
                    "pytest-of-" in line or 
                    "AppData\\Local\\Temp\\pytest" in line or
                    ("test_" in line.lower() and "invalid_utf8.json" in line)
                )
                
                # Keep the line if:
                # 1. It's not a test file, OR
                # 2. It's a test file but contains a real ERROR/CRITICAL (not just test setup)
                if not is_test_file:
                    filtered_lines.append(line)
                elif is_test_file and ("ERROR" in line or "CRITICAL" in line):
                    # Only keep test-related lines if they're actual errors
                    # But skip the pytest temp directory paths
                    if "AppData\\Local\\Temp\\pytest" not in line and "pytest-of-" not in line:
                        filtered_lines.append(line)
            
            # Display with syntax highlighting
            content = "".join(filtered_lines if filtered_lines else last_lines)
            syntax = Syntax(content, "log", theme="monokai", word_wrap=True, line_numbers=False)
            console.print(syntax)
            console.print()
            
    except Exception as e:
        console.print(f"[bold red on black]❌[/bold red on black] [bold red]Error:[/bold red] [red]Failed to read log file:[/red] [yellow]{e}[/yellow]")
        raise typer.Exit(1)


@app.command()
def tail(
    log_file: Path = typer.Argument(None, help="Log file to tail (default: most recent)"),
    lines: int = typer.Option(20, "--lines", "-n", help="Number of lines to show"),
):
    """
    Show last lines of log file (alias for view --lines N).
    
    Example:
        distrokid logs tail
        distrokid logs tail --lines 50
    """
    # Delegate to view command
    view(log_file=log_file, lines=lines, follow=False)


@app.command()
def clear(
    older_than_days: int = typer.Option(30, "--older-than", "-d", help="Delete logs older than N days"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without deleting"),
):
    """
    Clear old log files.
    
    Example:
        distrokid logs clear
        distrokid logs clear --older-than 7
        distrokid logs clear --dry-run
    """
    logs_dir = get_logs_dir()
    
    if not logs_dir.exists():
        console.print(f"[dim]Logs directory does not exist: {logs_dir}[/dim]")
        raise typer.Exit(0)
    
    log_files = sorted(logs_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not log_files:
        console.print("[dim]No log files found[/dim]")
        raise typer.Exit(0)
    
    # Find old files
    cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
    old_files = [
        f for f in log_files
        if f.stat().st_mtime < cutoff_time
    ]
    
    if not old_files:
        console.print(f"[dim]No log files older than {older_than_days} days[/dim]")
        raise typer.Exit(0)
    
    if dry_run:
        from rich.panel import Panel
        dry_run_panel = Panel(
            f"[bold yellow]⚠ Would delete {len(old_files)} log file(s) older than {older_than_days} days:[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(dry_run_panel)
        console.print()
        for log_file in old_files:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            console.print(f"  [dim]{log_file.name}[/dim] [dim]({mtime.strftime('%Y-%m-%d')})[/dim]")
        console.print()
        console.print("[dim]Run without --dry-run to delete[/dim]")
        raise typer.Exit(0)
    
    # Delete old files
    deleted_count = 0
    total_size = 0
    
    for log_file in old_files:
        try:
            size = log_file.stat().st_size
            log_file.unlink()
            deleted_count += 1
            total_size += size
        except Exception as e:
            print_warning(f"Failed to delete {log_file.name}: {e}")
    
    if deleted_count > 0:
        size_mb = total_size / (1024 * 1024)
        print_success(f"Deleted {deleted_count} log file(s), freed {size_mb:.2f} MB")
    else:
        console.print("[dim]No files were deleted[/dim]")
