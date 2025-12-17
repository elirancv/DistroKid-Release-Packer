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
from rich.color import Color

# Add scripts directory to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Create output directory
output_dir = Path(__file__).parent.parent / "assets" / "screenshots"
output_dir.mkdir(parents=True, exist_ok=True)

# Create console with HTML export capability - smaller width for better screenshots
# Force UTF-8 encoding to avoid Windows encoding issues
import io
import sys
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

console = Console(record=True, width=80, file=io.StringIO(), force_terminal=False)

# GitHub dark theme - matches GitHub's dark mode background (#0d1117)
GITHUB_DARK_THEME = TerminalTheme(
    background=(13, 17, 23),  # #0d1117 - GitHub dark background
    foreground=(201, 209, 217),  # #c9d1d9 - GitHub light text
    normal=[
        (201, 209, 217),  # #c9d1d9 - default text
        (248, 81, 73),    # #f85149 - red
        (56, 193, 114),   # #38c372 - green
        (187, 128, 9),    # #bb8009 - yellow
        (88, 166, 255),   # #58a6ff - blue
        (207, 99, 144),   # #cf6390 - magenta
        (125, 200, 216),  # #7dc8d8 - cyan
        (139, 148, 158),  # #8b949e - white (dim)
    ],
    bright=[
        (201, 209, 217),  # #c9d1d9 - bright default
        (248, 81, 73),    # #f85149 - bright red
        (56, 193, 114),   # #38c372 - bright green
        (187, 128, 9),    # #bb8009 - bright yellow
        (88, 166, 255),   # #58a6ff - bright blue
        (207, 99, 144),   # #cf6390 - bright magenta
        (125, 200, 216),  # #7dc8d8 - bright cyan
        (201, 209, 217),  # #c9d1d9 - bright white
    ],
)

def export_to_html(content_func, filename, title):
    """Run a function that prints Rich content and export to HTML."""
    console.clear()
    console.print(f"[bold cyan]# {title}[/bold cyan]\n")
    content_func()
    
    html = console.export_html(
        theme=GITHUB_DARK_THEME,
        clear=True,
        code_format="<pre style='font-family: Consolas, Monaco, monospace; font-size: 14px; background-color: #0d1117; color: #c9d1d9; padding: 20px; margin: 0;'>{code}</pre>"
    )
    
    # Ensure we have a full HTML document with dark background
    if not html.strip().startswith('<!DOCTYPE'):
        # Wrap in full HTML document if it's just a fragment
        html = f"""<!DOCTYPE html>
<html style="background-color: #0d1117 !important;">
<head>
<meta charset="UTF-8">
<style>
* {{
    background-color: #0d1117 !important;
}}
html {{
    background-color: #0d1117 !important;
}}
body {{
    background-color: #0d1117 !important;
    margin: 0 !important;
    padding: 0 !important;
    color: #c9d1d9 !important;
}}
pre {{
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
}}
code {{
    background-color: #0d1117 !important;
}}
span {{
    background-color: transparent !important;
}}
</style>
</head>
<body style="background-color: #0d1117 !important; margin: 0 !important; padding: 0 !important;">
{html}
</body>
</html>"""
    else:
        # Inject dark background into existing HTML document
        html = html.replace('<body>', '<body style="background-color: #0d1117 !important; margin: 0 !important; padding: 0 !important;">')
        html = html.replace('<html>', '<html style="background-color: #0d1117 !important;">')
        # Add comprehensive style tag
        dark_theme_css = """
<style>
* {
    background-color: #0d1117 !important;
}
html {
    background-color: #0d1117 !important;
}
body {
    background-color: #0d1117 !important;
    margin: 0 !important;
    padding: 0 !important;
    color: #c9d1d9 !important;
}
pre {
    background-color: #0d1117 !important;
    color: #c9d1d9 !important;
}
code {
    background-color: #0d1117 !important;
}
span {
    background-color: transparent !important;
}
</style>"""
        if '</head>' in html:
            html = html.replace('</head>', dark_theme_css + '</head>')
        elif '<head>' in html and '</head>' not in html:
            html = html.replace('<head>', '<head>' + dark_theme_css)
    
    output_file = output_dir / filename
    output_file.write_text(html, encoding="utf-8")
    print(f"✅ Exported {title} to {output_file}")
    return output_file

def pack_workflow_start():
    """Generate pack workflow start output."""
    from rich.panel import Panel
    from rich import box
    
    loading_panel = Panel(
        "[bold bright_cyan]Processing Release[/bold bright_cyan]\n\n"
        "[white]Config:[/white] [bold cyan]configs/release.json[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(loading_panel)
    console.print()

def pack_workflow_success():
    """Generate pack workflow success output."""
    from rich.panel import Panel
    from rich import box
    
    success_panel = Panel(
        "[bold green]✓ Release Packed Successfully![/bold green]\n\n"
        "[dim]Output: runtime/output/My Awesome Track/[/dim]\n"
        "[dim]  ├── Audio/Artist - Title.mp3[/dim]\n"
        "[dim]  ├── Cover/Artist - Title - Cover.jpg[/dim]\n"
        "[dim]  └── Metadata/Artist - Title - Metadata.json[/dim]",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(success_panel)
    console.print()

def pack_workflow_steps():
    """Generate pack workflow steps output."""
    from rich.panel import Panel
    from rich import box
    
    console.print("[bold cyan][1/7][/bold cyan] Validating configuration...")
    console.print("[bold green]✓[/bold green] Configuration valid")
    console.print()
    console.print("[bold cyan][2/7][/bold cyan] Extracting Suno version...")
    console.print("[bold green]✓[/bold green] Version: 4.0.0")
    console.print()
    console.print("[bold cyan][3/7][/bold cyan] Renaming audio files...")
    console.print("[bold green]✓[/bold green] Audio/Artist - Title.mp3")
    console.print()
    console.print("[bold cyan][4/7][/bold cyan] Tagging with ID3v2 metadata...")
    console.print("[bold green]✓[/bold green] Metadata embedded")
    console.print()
    console.print("[bold cyan][5/7][/bold cyan] Validating cover art...")
    console.print("[bold green]✓[/bold green] Cover art valid (3000x3000, 2.1MB)")
    console.print()
    console.print("[bold cyan][6/7][/bold cyan] Running compliance checks...")
    console.print("[bold green]✓[/bold green] All checks passed")
    console.print()
    console.print("[bold cyan][7/7][/bold cyan] Generating metadata...")
    console.print("[bold green]✓[/bold green] Metadata.json created")
    console.print()

def pack_dry_run():
    """Generate pack dry-run validation output."""
    from rich.panel import Panel
    from rich import box
    
    validation_panel = Panel(
        "[bold bright_cyan]Validating Configuration[/bold bright_cyan]\n\n"
        "[white]Config:[/white] [bold cyan]configs/release.json[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(validation_panel)
    console.print()
    
    success_panel = Panel(
        "[bold green]✓ Configuration is Valid[/bold green]\n\n"
        "[dim]All checks passed. Run without --dry-run to process.[/dim]",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(success_panel)
    console.print()

def html_to_png(html_file: Path, png_file: Path):
    """Convert HTML file to PNG using headless browser (if available)."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                # Browser not installed
                if "Executable doesn't exist" in str(e) or "BrowserType.launch" in str(e):
                    return None  # Signal that browser needs installation
                raise
            
            page = browser.new_page(viewport={"width": 900, "height": 600})
            # Set dark background to match GitHub
            page.goto(f"file://{html_file.absolute()}")
            # Inject CSS to ensure dark background - override ALL possible backgrounds
            page.add_style_tag(content="""
                * {
                    background-color: #0d1117 !important;
                }
                body {
                    background-color: #0d1117 !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                html {
                    background-color: #0d1117 !important;
                }
                pre {
                    background-color: #0d1117 !important;
                    color: #c9d1d9 !important;
                }
                code {
                    background-color: #0d1117 !important;
                }
                span {
                    background-color: transparent !important;
                }
            """)
            # Wait for content to render
            page.wait_for_timeout(1000)
            # Take screenshot with specific viewport size (not full page)
            # Use a larger timeout to ensure all styles are applied
            page.screenshot(path=str(png_file), full_page=False)
            browser.close()
            return True
    except ImportError:
        # Playwright not installed, skip PNG conversion
        return False
    except Exception as e:
        # Other errors - don't spam output
        return False

def main():
    """Generate all CLI screenshot HTML files and optionally convert to PNG."""
    print("Generating Rich CLI output HTML files for screenshots...\n")
    
    html_files = [
        export_to_html(pack_workflow_start, "pack-workflow-start.html", "Pack Workflow - Start"),
        export_to_html(pack_workflow_steps, "pack-workflow-steps.html", "Pack Workflow - Steps"),
        export_to_html(pack_workflow_success, "pack-workflow-success.html", "Pack Workflow - Success"),
        export_to_html(pack_dry_run, "pack-dry-run.html", "Pack - Dry Run Validation"),
    ]
    
    print(f"\n✅ All HTML files generated in: {output_dir}")
    
    # Try to convert HTML to PNG automatically
    print("\n🔄 Attempting to convert HTML to PNG images...")
    png_count = 0
    browser_needs_install = False
    
    for html_file in html_files:
        png_file = html_file.with_suffix('.png')
        result = html_to_png(html_file, png_file)
        
        if result is True:
            print(f"✅ Converted {html_file.name} → {png_file.name}")
            png_count += 1
        elif result is None:
            browser_needs_install = True
            break  # Stop trying if browser isn't installed
    
    if browser_needs_install:
        print("\n⚠️  Playwright browser not installed")
        print("\nTo enable automatic PNG conversion, run:")
        print("  python -m playwright install chromium")
        print("\nOr manually:")
        print("1. Open the HTML files in a browser")
        print("2. Take screenshots of each page")
        print("3. Save as PNG files in the same directory")
    elif png_count == 0:
        print("\n⚠️  PNG conversion skipped (playwright not installed)")
        print("\nTo enable automatic PNG conversion:")
        print("  pip install playwright")
        print("  python -m playwright install chromium")
    else:
        print(f"\n✅ Successfully converted {png_count}/{len(html_files)} HTML files to PNG")
    
    print("\n📝 HTML files are ready in assets/screenshots/")

if __name__ == "__main__":
    main()
