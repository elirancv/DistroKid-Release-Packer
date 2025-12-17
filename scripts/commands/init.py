"""
Init command - Initialize project structure.
"""

import sys
import shutil
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from rich_utils import console, print_success, print_error, print_warning, print_info

app = typer.Typer(name="init", help="Initialize project structure")


def check_dependency(name: str, import_name: str = None) -> bool:
    """Check if a dependency is installed."""
    if import_name is None:
        import_name = name
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
    skip_deps: bool = typer.Option(False, "--skip-deps", help="Skip dependency check"),
):
    """
    Initialize project structure.
    
    This command:
    - Creates runtime directories (input, output, logs)
    - Copies example configs if missing
    - Checks dependencies
    - Creates .gitignore entries if needed
    
    Example:
        distrokid init
        distrokid init --force
    """
    project_root = Path(__file__).parent.parent.parent
    runtime_dir = project_root / "runtime"
    configs_dir = project_root / "configs"
    
    from rich.panel import Panel
    console.print()
    title_panel = Panel(
        "[bold bright_cyan]🚀 [bold bright_magenta]Initializing DistroKid Release Packer[/bold bright_magenta][/bold bright_cyan]\n[dim white]Setting up your project structure...[/dim white]",
        border_style="bright_cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(title_panel)
    console.print()
    
    steps_completed = []
    steps_failed = []
    
    # Step 1: Create runtime directories
    console.print("[bold bright_yellow]📁[/bold bright_yellow] [bold bright_magenta]Step 1:[/bold bright_magenta] Creating runtime directories...")
    try:
        dirs_to_create = [
            runtime_dir / "input",
            runtime_dir / "output",
            runtime_dir / "logs",
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [bold bright_green]✓[/bold bright_green] [bright_green]{dir_path.relative_to(project_root)}[/bright_green]")
        
        steps_completed.append("Runtime directories")
        console.print()
    except Exception as e:
        steps_failed.append(f"Runtime directories: {e}")
        print_error(f"Failed to create runtime directories: {e}")
        console.print()
    
    # Step 2: Copy example configs
    console.print()
    console.print("[bold bright_yellow]⚙️[/bold bright_yellow]  [bold bright_magenta]Step 2:[/bold bright_magenta] Setting up configuration files...")
    try:
        config_files = [
            ("release.example.json", "release.json"),
            ("artist-defaults.example.json", "artist-defaults.json"),
        ]
        
        for example_name, target_name in config_files:
            example_path = configs_dir / example_name
            target_path = configs_dir / target_name
            
            if not example_path.exists():
                console.print(f"  [yellow]⚠[/yellow] Example file not found: {example_name}")
                continue
            
            if target_path.exists() and not force:
                console.print(f"  [dim]⊘[/dim] [dim white]{target_name}[/dim white] [dim](already exists, use --force to overwrite)[/dim]")
            else:
                shutil.copy2(example_path, target_path)
                console.print(f"  [bold bright_green]✓[/bold bright_green] [bright_green]Created {target_name}[/bright_green]")
        
        steps_completed.append("Configuration files")
        console.print()
    except Exception as e:
        steps_failed.append(f"Configuration files: {e}")
        print_error(f"Failed to setup configuration files: {e}")
        console.print()
    
    # Step 3: Check dependencies
    if not skip_deps:
        console.print()
        console.print("[bold bright_yellow]📦[/bold bright_yellow] [bold bright_magenta]Step 3:[/bold bright_magenta] Checking dependencies...")
        try:
            required_deps = [
                ("mutagen", "mutagen"),
                ("Pillow", "PIL"),
                ("rich", "rich"),
                ("jsonschema", "jsonschema"),
                ("typer", "typer"),
            ]
            
            missing_deps = []
            for dep_name, import_name in required_deps:
                if check_dependency(dep_name, import_name):
                    console.print(f"  [bold bright_green]✓[/bold bright_green] [bright_green]{dep_name}[/bright_green]")
                else:
                    console.print(f"  [bold bright_red]✗[/bold bright_red] [bright_red]{dep_name} (missing)[/bright_red]")
                    missing_deps.append(dep_name)
            
            if missing_deps:
                console.print()
                print_warning(f"Missing dependencies: {', '.join(missing_deps)}")
                console.print("  Install with: [cyan]pip install -r requirements.txt[/cyan]")
                steps_failed.append(f"Dependencies: {len(missing_deps)} missing")
            else:
                steps_completed.append("Dependencies")
            
            console.print()
        except Exception as e:
            steps_failed.append(f"Dependencies check: {e}")
            print_error(f"Failed to check dependencies: {e}")
            console.print()
    else:
        console.print("[bold]Step 3:[/bold] Skipping dependency check")
        console.print()
    
    # Step 4: Check .gitignore
    console.print()
    console.print("[bold bright_yellow]🔍[/bold bright_yellow] [bold bright_magenta]Step 4:[/bold bright_magenta] Checking .gitignore...")
    try:
        gitignore_path = project_root / ".gitignore"
        runtime_entries = [
            "runtime/",
            "runtime/input/",
            "runtime/output/",
            "runtime/logs/",
        ]
        
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text(encoding="utf-8")
            missing_entries = [
                entry for entry in runtime_entries
                if entry not in gitignore_content
            ]
            
            if missing_entries:
                console.print("  [yellow]⚠[/yellow] Some runtime entries missing from .gitignore")
                console.print("  [dim]Consider adding:[/dim]")
                for entry in missing_entries:
                    console.print(f"    [dim]{entry}[/dim]")
            else:
                console.print("  [bold bright_green]✓[/bold bright_green] [bright_green].gitignore looks good[/bright_green]")
        else:
            console.print("  [yellow]⚠[/yellow] .gitignore not found")
            console.print("  [dim]Consider creating .gitignore with runtime/ entries[/dim]")
        
        steps_completed.append(".gitignore check")
        console.print()
    except Exception as e:
        steps_failed.append(f".gitignore check: {e}")
        print_warning(f"Could not check .gitignore: {e}")
        console.print()
    
    # Summary
    console.print()
    console.print("[bold magenta]📊 Initialization Summary:[/bold magenta]")
    console.print()
    
    summary_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_cyan on bright_blue",
        border_style="bright_cyan",
        title="[bold bright_cyan]Initialization Summary[/bold bright_cyan]"
    )
    summary_table.add_column("Step", style="bold bright_cyan", no_wrap=True)
    summary_table.add_column("Status", style="bold", justify="center")
    
    for step in steps_completed:
        summary_table.add_row(f"[bright_cyan]{step}[/bright_cyan]", "[bold bright_green]✓ Completed[/bold bright_green]")
    
    for step in steps_failed:
        summary_table.add_row(f"[bright_cyan]{step}[/bright_cyan]", "[bold bright_red]✗ Failed[/bold bright_red]")
    
    console.print(summary_table)
    console.print()
    
    if steps_failed:
        from rich.panel import Panel
        warning_panel = Panel(
            f"[bold bright_yellow]⚠ Initialization completed with {len(steps_failed)} issue(s)[/bold bright_yellow]",
            title="[bold bright_yellow]⚠ Warning[/bold bright_yellow]",
            border_style="bright_yellow",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(warning_panel)
        console.print()
        console.print("[bold bright_cyan]💡 Next steps:[/bold bright_cyan]")
        console.print("  [bright_cyan]1.[/bright_cyan] Review the errors above")
        console.print("  [bright_cyan]2.[/bright_cyan] Install missing dependencies: [bold bright_white]pip install -r requirements.txt[/bold bright_white]")
        console.print("  [bright_cyan]3.[/bright_cyan] Edit configuration files in [bright_white]configs/[/bright_white]")
        raise typer.Exit(1)
    else:
        from rich.panel import Panel
        success_panel = Panel(
            "[bold bright_green]✓ Project initialized successfully![/bold bright_green]\n[dim white]You're ready to start packing releases![/dim white]",
            title="[bold bright_green]🎉 Success[/bold bright_green]",
            border_style="bright_green",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(success_panel)
        console.print()
        console.print("[bold bright_cyan]💡 Next steps:[/bold bright_cyan]")
        console.print("  [bright_cyan]1.[/bright_cyan] Edit [bold bright_white]configs/release.json[/bold bright_white] with your track details")
        console.print("  [bright_cyan]2.[/bright_cyan] Edit [bold bright_white]configs/artist-defaults.json[/bold bright_white] with your artist defaults")
        console.print("  [bright_cyan]3.[/bright_cyan] Place audio files in [bold bright_white]runtime/input/[/bold bright_white]")
        console.print("  [bright_cyan]4.[/bright_cyan] Run: [bold bright_cyan]distrokid pack configs/release.json[/bold bright_cyan]")
        console.print()
        raise typer.Exit(0)
