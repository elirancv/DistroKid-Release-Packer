#!/usr/bin/env python3
"""
Batch processing for multiple releases.

Processes all release.json files in a directory or matches a pattern.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from logger_config import get_logger
from rich_utils import console, print_success, print_error, print_warning, print_info, create_table
from validate_config import validate_release_config

logger = get_logger("batch_processor")


def find_release_configs(directory: Path, pattern: str = "release*.json") -> List[Path]:
    """
    Find all release configuration files in a directory.
    
    Args:
        directory: Directory to search
        pattern: Filename pattern (default: "release*.json")
    
    Returns:
        List of config file paths
    """
    directory = Path(directory)
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return []
    
    configs = list(directory.glob(pattern))
    # Exclude example files
    configs = [c for c in configs if "example" not in c.name.lower()]
    
    logger.info(f"Found {len(configs)} release config(s) in {directory}")
    return sorted(configs)


def process_batch(
    config_dir: Path,
    pattern: str = "release*.json",
    continue_on_error: bool = True,
    dry_run: bool = False,
) -> Dict[str, Dict]:
    """
    Process multiple release configurations in batch.
    
    Args:
        config_dir: Directory containing release.json files
        pattern: Filename pattern to match
        continue_on_error: Whether to continue processing if one fails
        dry_run: If True, only validate configs without processing
    
    Returns:
        Dictionary with results for each config file
    """
    import sys
    from pathlib import Path
    
    # Add scripts to path for imports
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    
    from orchestrator import load_config, run_release_workflow
    
    config_dir = Path(config_dir)
    config_files = find_release_configs(config_dir, pattern)
    
    if not config_files:
        logger.warning(f"No release configs found in {config_dir} matching pattern '{pattern}'")
        return {}
    
    results = {}
    total = len(config_files)
    
    console.print()
    console.print(f"[bold]Batch Processing: {total} release(s)[/bold]")
    console.print()
    
    for idx, config_file in enumerate(config_files, 1):
        console.print(f"[bold cyan][{idx}/{total}][/bold cyan] Processing: {config_file.name}")
        console.print()
        
        try:
            # Load and validate config
            logger.info(f"Loading config: {config_file}")
            config = load_config(config_file, validate=True)
            
            # Validate schema
            is_valid, errors = validate_release_config(config_file)
            if not is_valid:
                error_msg = "\n".join(f"  - {e}" for e in errors)
                logger.warning(f"Schema validation errors in {config_file}:\n{error_msg}")
                if not continue_on_error:
                    raise ValueError(f"Schema validation failed:\n{error_msg}")
            
            if dry_run:
                print_success(f"✓ Config valid: {config_file.name}")
                results[str(config_file)] = {
                    "status": "validated",
                    "config": config,
                    "errors": errors if not is_valid else []
                }
            else:
                # Run workflow
                logger.info(f"Running workflow for {config_file}")
                success = run_release_workflow(config, config_path=str(config_file))
                
                results[str(config_file)] = {
                    "status": "success" if success else "warnings",
                    "config": config,
                    "success": success
                }
                
                if success:
                    print_success(f"✓ Completed: {config_file.name}")
                else:
                    print_warning(f"⚠ Completed with warnings: {config_file.name}")
        
        except Exception as e:
            logger.error(f"Error processing {config_file}: {e}", exc_info=True)
            print_error(f"✗ Failed: {config_file.name} - {e}")
            
            results[str(config_file)] = {
                "status": "error",
                "error": str(e),
                "success": False
            }
            
            if not continue_on_error:
                console.print()
                print_error("Stopping batch processing due to error")
                break
        
        console.print()
    
    # Summary
    console.print()
    console.print("[bold]Batch Processing Summary[/bold]")
    console.print()
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    warning_count = sum(1 for r in results.values() if r.get("status") == "warnings")
    error_count = sum(1 for r in results.values() if r.get("status") == "error")
    
    table = create_table("Results", ["Status", "Count"])
    table.add_row("[bold green]Success[/bold green]", str(success_count))
    if warning_count > 0:
        table.add_row("[bold yellow]Warnings[/bold yellow]", str(warning_count))
    if error_count > 0:
        table.add_row("[bold red]Errors[/bold red]", str(error_count))
    table.add_row("[bold]Total[/bold]", str(total))
    
    console.print(table)
    console.print()
    
    logger.info(f"Batch processing complete: {success_count} success, {warning_count} warnings, {error_count} errors")
    
    return results

