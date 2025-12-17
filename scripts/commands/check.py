"""
Check command - Verify system requirements.
"""

import sys
import subprocess
from pathlib import Path
from typing import Tuple
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from rich_utils import console, print_success, print_warning, print_error

app = typer.Typer(name="check", help="Check system requirements and dependencies")


def check_python_version() -> Tuple[bool, str]:
    """Check Python version."""
    import sys
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and version.minor >= 8:
        return True, version_str
    else:
        return False, version_str


def check_dependency(name: str, import_name: str = None, required: bool = True) -> Tuple[bool, str, str]:
    """Check if a dependency is installed."""
    if import_name is None:
        import_name = name
    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "installed")
        return True, "Installed", version
    except ImportError:
        status = "Required" if required else "Optional"
        return False, "Not installed", status


def check_ffmpeg() -> Tuple[bool, str]:
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from output
            version_line = result.stdout.split("\n")[0]
            return True, version_line
        return False, "Not found"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "Not found"


def check_nodejs() -> Tuple[bool, str]:
    """Check if Node.js is available."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "Not found"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "Not found"


@app.command()
def check(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """
    Check system requirements and dependencies.
    
    Verifies:
    - Python version
    - Required dependencies
    - Optional dependencies (ffmpeg, Node.js)
    - File permissions
    - Disk space
    """
    from rich.panel import Panel
    console.print()
    title_panel = Panel(
        "[bold bright_cyan]🔍 [bold bright_magenta]System Requirements Check[/bold bright_magenta][/bold bright_cyan]\n[dim white]Verifying dependencies and system health[/dim white]",
        border_style="bright_cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(title_panel)
    console.print()
    
    project_root = Path(__file__).parent.parent.parent
    all_checks_passed = True
    
    # Python Version
    console.print("[bold bright_yellow]🐍[/bold bright_yellow] [bold bright_magenta]Python Version:[/bold bright_magenta]")
    py_ok, py_version = check_python_version()
    if py_ok:
        console.print(f"  [bold bright_green]✓[/bold bright_green] [bright_green]Python {py_version}[/bright_green] [dim white](required: 3.8+)[/dim white]")
    else:
        console.print(f"  [bold bright_red]✗[/bold bright_red] [bright_red]Python {py_version}[/bright_red] [dim white](required: 3.8+)[/dim white]")
        all_checks_passed = False
    console.print()
    
    # Required Dependencies
    console.print("[bold bright_yellow]📦[/bold bright_yellow] [bold bright_magenta]Required Dependencies:[/bold bright_magenta]")
    req_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan on bright_blue",
        border_style="bright_cyan",
        title="[bold bright_cyan]Required Packages[/bold bright_cyan]"
    )
    req_table.add_column("Package", style="bold bright_cyan", no_wrap=True)
    req_table.add_column("Status", style="bold", justify="center")
    req_table.add_column("Version", style="bright_white")
    
    required_deps = [
        ("mutagen", "mutagen", True),
        ("Pillow", "PIL", True),
        ("rich", "rich", True),
        ("jsonschema", "jsonschema", True),
        ("typer", "typer", True),
    ]
    
    for dep_name, import_name, required in required_deps:
        installed, status, version = check_dependency(dep_name, import_name, required)
        if installed:
            req_table.add_row(f"[bright_cyan]{dep_name}[/bright_cyan]", "[bold bright_green]✓[/bold bright_green] [bright_green]Installed[/bright_green]", f"[bright_white]{version}[/bright_white]")
        else:
            req_table.add_row(f"[bright_cyan]{dep_name}[/bright_cyan]", "[bold bright_red]✗[/bold bright_red] [bright_red]Missing[/bright_red]", "[dim]N/A[/dim]")
            all_checks_passed = False
    
    console.print(req_table)
    console.print()
    
    # Optional Dependencies
    console.print()
    console.print("[bold bright_yellow]🔧[/bold bright_yellow] [bold bright_magenta]Optional Dependencies:[/bold bright_magenta]")
    opt_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan on bright_blue",
        border_style="bright_cyan",
        title="[bold bright_cyan]Optional Packages[/bold bright_cyan]"
    )
    opt_table.add_column("Package", style="bold bright_cyan", no_wrap=True)
    opt_table.add_column("Status", style="bold", justify="center")
    opt_table.add_column("Details", style="bright_white")
    
    # Audio analysis (librosa, soundfile)
    librosa_ok, _, librosa_ver = check_dependency("librosa", "librosa", False)
    soundfile_ok, _, soundfile_ver = check_dependency("soundfile", "soundfile", False)
    
    if librosa_ok and soundfile_ok:
        opt_table.add_row("[bright_cyan]Audio Analysis[/bright_cyan]", "[bold bright_green]✓[/bold bright_green] [bright_green]Available[/bright_green]", f"[bright_white]librosa {librosa_ver}, soundfile {soundfile_ver}[/bright_white]")
    else:
        opt_table.add_row("[bright_cyan]Audio Analysis[/bright_cyan]", "[bold bright_yellow]⚠[/bold bright_yellow] [bright_yellow]Partial[/bright_yellow]", "[bright_white]Required for clipping detection[/bright_white]")
    
    # FFmpeg
    ffmpeg_ok, ffmpeg_info = check_ffmpeg()
    if ffmpeg_ok:
        opt_table.add_row("[bright_cyan]FFmpeg[/bright_cyan]", "[bold bright_green]✓[/bold bright_green] [bright_green]Available[/bright_green]", f"[bright_white]{ffmpeg_info.split()[2] if len(ffmpeg_info.split()) > 2 else 'installed'}[/bright_white]")
    else:
        opt_table.add_row("[bright_cyan]FFmpeg[/bright_cyan]", "[bold bright_yellow]⚠[/bold bright_yellow] [bright_yellow]Not found[/bright_yellow]", "[bright_white]Required for audio clipping fix[/bright_white]")
    
    # Node.js
    node_ok, node_ver = check_nodejs()
    if node_ok:
        opt_table.add_row("[bright_cyan]Node.js[/bright_cyan]", "[bold bright_green]✓[/bold bright_green] [bright_green]Available[/bright_green]", f"[bright_white]{node_ver}[/bright_white]")
    else:
        opt_table.add_row("[bright_cyan]Node.js[/bright_cyan]", "[bold bright_yellow]⚠[/bold bright_yellow] [bright_yellow]Not found[/bright_yellow]", "[bright_white]Required for JavaScript variant[/bright_white]")
    
    console.print(opt_table)
    console.print()
    
    # Windows-specific checks
    if sys.platform == 'win32':
        console.print()
        console.print("[bold bright_yellow]🪟[/bold bright_yellow] [bold bright_magenta]Windows-Specific:[/bold bright_magenta]")
        win_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold bright_cyan on bright_blue",
            border_style="bright_cyan",
            title="[bold bright_cyan]Windows Features[/bold bright_cyan]"
        )
        win_table.add_column("Check", style="bold bright_cyan", no_wrap=True)
        win_table.add_column("Status", style="bold", justify="center")
        
        try:
            import win32api
            win_table.add_row("[bright_cyan]Long path support[/bright_cyan]", "[bold bright_green]✓[/bold bright_green] [bright_green]Available (pywin32)[/bright_green]")
        except ImportError:
            win_table.add_row("[bright_cyan]Long path support[/bright_cyan]", "[bold bright_yellow]⚠[/bold bright_yellow] [bright_yellow]Not enabled[/bright_yellow]", "[bright_white]Install pywin32 for long path support[/bright_white]")
        
        console.print(win_table)
        console.print()
    
    # File Permissions
    console.print()
    console.print("[bold bright_yellow]🔐[/bold bright_yellow] [bold bright_magenta]File Permissions:[/bold bright_magenta]")
    perm_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan on bright_blue",
        border_style="bright_cyan",
        title="[bold bright_cyan]Directory Permissions[/bold bright_cyan]"
    )
    perm_table.add_column("Directory", style="bold bright_cyan", no_wrap=True)
    perm_table.add_column("Status", style="bold", justify="center")
    
    runtime_dir = project_root / "runtime"
    configs_dir = project_root / "configs"
    
    for dir_path, name in [(runtime_dir, "runtime/"), (configs_dir, "configs/")]:
        if dir_path.exists():
            try:
                # Try to create a test file
                test_file = dir_path / ".test_write"
                test_file.touch()
                test_file.unlink()
                perm_table.add_row(f"[bright_cyan]{name}[/bright_cyan]", "[bold bright_green]✓[/bold bright_green] [bright_green]Writable[/bright_green]")
            except Exception:
                perm_table.add_row(f"[bright_cyan]{name}[/bright_cyan]", "[bold bright_red]✗[/bold bright_red] [bright_red]Not writable[/bright_red]")
                all_checks_passed = False
        else:
            perm_table.add_row(f"[bright_cyan]{name}[/bright_cyan]", "[bold bright_yellow]⚠[/bold bright_yellow] [bright_yellow]Does not exist[/bright_yellow]")
    
    console.print(perm_table)
    console.print()
    
    # Disk Space
    console.print()
    console.print("[bold bright_yellow]💾[/bold bright_yellow] [bold bright_magenta]Disk Space:[/bold bright_magenta]")
    try:
        import shutil
        stat = shutil.disk_usage(project_root)
        free_gb = stat.free / (1024 ** 3)
        free_pct = (stat.free / stat.total) * 100
        
        if free_gb < 0.5:
            console.print(f"  [bold bright_red]✗[/bold bright_red] [bright_red]Low disk space:[/bright_red] [bright_white]{free_gb:.2f} GB free ({free_pct:.1f}%)[/bright_white]")
            console.print("  [dim white]Recommend at least 500 MB free space[/dim white]")
            all_checks_passed = False
        else:
            console.print(f"  [bold bright_green]✓[/bold bright_green] [bright_green]Sufficient disk space:[/bright_green] [bright_white]{free_gb:.2f} GB free ({free_pct:.1f}%)[/bright_white]")
    except Exception:
        console.print("  [bold bright_yellow]⚠[/bold bright_yellow] [bright_yellow]Could not check disk space[/bright_yellow]")
    console.print()
    
    # Summary
    console.print()
    from rich.panel import Panel
    if all_checks_passed:
        success_panel = Panel(
            "[bold bright_green]✓ All required checks passed![/bold bright_green]\n[dim white]Your system is ready to go![/dim white]",
            title="[bold bright_green]🎉 Success[/bold bright_green]",
            border_style="bright_green",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(success_panel)
        raise typer.Exit(0)
    else:
        error_panel = Panel(
            "[bold bright_red]✗ Some checks failed[/bold bright_red]\n[dim white]Please install missing dependencies[/dim white]",
            title="[bold bright_red]❌ Issues Found[/bold bright_red]",
            border_style="bright_red",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(error_panel)
        console.print()
        console.print("[bold bright_cyan]💡 To install dependencies:[/bold bright_cyan]")
        console.print("  [bright_cyan]pip install -r requirements.txt[/bright_cyan]")
        raise typer.Exit(1)
