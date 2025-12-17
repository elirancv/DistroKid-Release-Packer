#!/usr/bin/env python3
"""
Generate HTML exports of Rich CLI output for screenshot purposes.

This script runs various CLI commands and exports their Rich-formatted output
to HTML files that can be easily screenshot or converted to images.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.terminal_theme import TerminalTheme, MONOKAI

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Create output directory
output_dir = Path(__file__).parent.parent / "assets" / "screenshots"
output_dir.mkdir(parents=True, exist_ok=True)

# Create console with HTML export capability
console = Console(record=True, width=120)

def export_to_html(content_func, filename, title):
    """Run a function that prints Rich content and export to HTML."""
    console.clear()
    console.print(f"[bold cyan]# {title}[/bold cyan]\n")
    content_func()
    
    html = console.export_html(
        theme=MONOKAI,
        clear=True,
        code_format="<pre style='font-family: Consolas, Monaco, monospace; font-size: 14px;'>{code}</pre>"
    )
    
    output_file = output_dir / filename
    output_file.write_text(html, encoding="utf-8")
    print(f"✅ Exported {title} to {output_file}")
    return output_file

def status_dashboard():
    """Generate status dashboard output."""
    from commands.status import status
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
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
    
    deps_table.add_row("mutagen", "[bold green]✓[/bold green] [green]Installed[/green]", "1.47.0")
    deps_table.add_row("Pillow", "[bold green]✓[/bold green] [green]Installed[/green]", "10.0.0")
    deps_table.add_row("rich", "[bold green]✓[/bold green] [green]Installed[/green]", "13.0.0")
    console.print(deps_table)
    console.print()

def config_viewer():
    """Generate config viewer output."""
    from rich.json import JSON
    from rich.panel import Panel
    from rich import box
    
    config_data = {
        "title": "My Awesome Track",
        "artist": "Test Artist",
        "genre": "Electronic",
        "bpm": 128,
        "tag_audio": True,
        "validate_cover": True
    }
    
    title_panel = Panel(
        "[bold bright_cyan]⚙️  Configuration File[/bold bright_cyan]\n[dim white]configs/release.json[/dim white]",
        border_style="bright_cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(title_panel)
    console.print()
    console.print(JSON.from_data(config_data))
    console.print()

def system_check():
    """Generate system check output."""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    console.print("[bold bright_yellow]🐍[/bold bright_yellow] [bold bright_magenta]Python Version:[/bold bright_magenta]")
    console.print("  [bold bright_green]✓[/bold bright_green] [bright_green]Python 3.11.0[/bright_green] [dim white](required: 3.8+)[/dim white]")
    console.print()
    
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
    
    req_table.add_row("mutagen", "[bold bright_green]✓[/bold bright_green] [bright_green]Installed[/bright_green]", "1.47.0")
    req_table.add_row("Pillow", "[bold bright_green]✓[/bold bright_green] [bright_green]Installed[/bright_green]", "10.0.0")
    req_table.add_row("rich", "[bold bright_green]✓[/bold bright_green] [bright_green]Installed[/bright_green]", "13.0.0")
    
    console.print(req_table)
    console.print()
    
    success_panel = Panel(
        "[bold bright_green]✓ All required checks passed![/bold bright_green]\n[dim white]Your system is ready to go![/dim white]",
        title="[bold bright_green]🎉 Success[/bold bright_green]",
        border_style="bright_green",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(success_panel)

def error_panel():
    """Generate error panel output."""
    from rich.panel import Panel
    from rich import box
    
    error_panel = Panel(
        "[bold red on black]❌[/bold red on black] [bold red]Config File Not Found[/bold red]\n\n"
        "[white]Path:[/white] [yellow]configs/missing.json[/yellow]\n\n"
        "[bold cyan]Solution:[/bold cyan]\n"
        "  • Verify the file path is correct\n"
        "  • Check that the file exists in the specified location\n"
        "  • Create from example: [cyan]cp configs/release.example.json configs/release.json[/cyan]",
        border_style="red",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(error_panel)

def html_to_png(html_file: Path, png_file: Path):
    """Convert HTML file to PNG using headless browser (if available)."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"file://{html_file.absolute()}")
            # Wait for content to render
            page.wait_for_timeout(500)
            # Take screenshot
            page.screenshot(path=str(png_file), full_page=True)
            browser.close()
            return True
    except ImportError:
        # Playwright not installed, skip PNG conversion
        return False
    except Exception as e:
        print(f"⚠️  Could not convert {html_file.name} to PNG: {e}")
        return False

def main():
    """Generate all CLI screenshot HTML files and optionally convert to PNG."""
    print("Generating Rich CLI output HTML files for screenshots...\n")
    
    html_files = [
        export_to_html(status_dashboard, "status-dashboard.html", "Status Dashboard"),
        export_to_html(config_viewer, "config-viewer.html", "Configuration Viewer"),
        export_to_html(system_check, "system-check.html", "System Check"),
        export_to_html(error_panel, "error-panel.html", "Error Panel"),
    ]
    
    print(f"\n✅ All HTML files generated in: {output_dir}")
    
    # Try to convert HTML to PNG automatically
    print("\n🔄 Attempting to convert HTML to PNG images...")
    png_count = 0
    for html_file in html_files:
        png_file = html_file.with_suffix('.png')
        if html_to_png(html_file, png_file):
            print(f"✅ Converted {html_file.name} → {png_file.name}")
            png_count += 1
    
    if png_count == 0:
        print("\n⚠️  PNG conversion skipped (playwright not installed)")
        print("\nTo enable automatic PNG conversion:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print("\nOr manually:")
        print("1. Open the HTML files in a browser")
        print("2. Take screenshots of each page")
        print("3. Save as PNG files in the same directory")
    else:
        print(f"\n✅ Successfully converted {png_count}/{len(html_files)} HTML files to PNG")
    
    print("\n📝 Next step: Update README.md with the image links")

if __name__ == "__main__":
    main()
