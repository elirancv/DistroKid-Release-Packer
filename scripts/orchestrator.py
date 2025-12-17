#!/usr/bin/env python3
"""
DistroKid Release Packer - Main Orchestrator

Runs the complete release workflow from Suno export to DistroKid-ready files.
"""

import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from extract_suno_version import (
    extract_suno_version_from_url,
    extract_from_metadata_file,
)
from rename_audio_files import rename_audio_files
from organize_stems import organize_stems
from tag_stems import batch_tag_stems
from tag_audio_id3 import tag_audio_file
from validate_cover_art import validate_cover_art
from validate_compliance import full_compliance_check, validate_audio_file
from fix_clipping import fix_clipping_ffmpeg
from validate_config import validate_release_config, validate_artist_defaults
from logger_config import setup_logging, get_logger
from retry_utils import retry, RetryContext, RetryableError, NonRetryableError
from rich_utils import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_step,
    print_workflow_start,
    print_workflow_complete,
    print_workflow_error,
    create_progress,
)

# Initialize logging
logger = get_logger("orchestrator")

# Windows long path support (optional)
if sys.platform == 'win32':
    try:
        import win32api
        win32api.SetLongPathEnabled(True)
        logger.debug("Windows long path support enabled")
    except ImportError:
        logger.warning(
            "Long path support not enabled on Windows. "
            "Install pywin32 for long path support: pip install pywin32"
        )
    except Exception as e:
        logger.debug(f"Could not enable long path support: {e}")


def load_user_settings():
    """Load user settings from artist-defaults.json (if exists)."""
    # Check configs/ first, then root for backward compatibility
    settings_file = Path("configs/artist-defaults.json")
    if not settings_file.exists():
        settings_file = Path("artist-defaults.json")
    if not settings_file.exists():
        logger.debug("artist-defaults.json not found, using empty defaults")
        return {}

    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
            # Filter out comment fields
            filtered = {k: v for k, v in settings.items() if not k.startswith("_")}
            
            # Validate schema (non-strict by default for artist-defaults)
            is_valid, errors = validate_artist_defaults(settings_file, strict=False)
            if not is_valid:
                logger.warning(f"artist-defaults.json validation errors: {', '.join(errors)}")
            
            logger.info(f"Loaded artist defaults from {settings_file}")
            return filtered
    except json.JSONDecodeError as e:
        logger.error(f"Failed to load artist-defaults.json (invalid JSON): {e}")
        # If artist-defaults.json is invalid, just return empty dict
        return {}
    except UnicodeDecodeError as e:
        logger.error(f"Failed to load artist-defaults.json (encoding error): {e}")
        # If artist-defaults.json has encoding issues, just return empty dict
        # The error will be caught when loading the release config if needed
        return {}


def load_config(config_path, validate: bool = True):
    """Load configuration from JSON file, merging with user settings."""
    config_file = Path(config_path)
    
    logger.info(f"Loading configuration from {config_file}")

    if not config_file.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load user settings first (defaults)
    user_settings = load_user_settings()

    # Load release-specific config
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            release_config = json.load(f)
        logger.debug(f"Successfully parsed JSON from {config_file}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {config_path}: {e}")
        raise ValueError(
            f"Invalid JSON in config file '{config_path}':\n"
            f"  Error: {e.msg}\n"
            f"  Line {e.lineno}, column {e.colno}\n"
            f"  Fix the JSON syntax and try again."
        )
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error in {config_path}: {e}")
        # Provide a more helpful error message
        error_msg = (
            f"❌ [bold red]Encoding Error[/bold red]\n\n"
            f"Config file '[yellow]{config_path}[/yellow]' is not valid UTF-8 text.\n\n"
            f"[dim]Error details:[/dim] {e}\n\n"
            f"[bold]Solution:[/bold]\n"
            f"  • Open the file in a text editor (VS Code, Notepad++)\n"
            f"  • Save it with UTF-8 encoding (File → Save As → Encoding: UTF-8)\n"
            f"  • Ensure no binary data or special characters are corrupted\n"
            f"  • If the file was copied, ensure it was copied as text, not binary"
        )
        raise ValueError(error_msg)
    
    # Validate against schema (strict by default, opt-out with strict_schema_validation: false)
    if validate:
        strict_validation = release_config.get("strict_schema_validation", True)  # Default to True
        is_valid, errors = validate_release_config(config_file, strict=strict_validation)
        if not is_valid:
            error_msg = "\n".join(f"  - {e}" for e in errors)
            if strict_validation:
                logger.error(f"Schema validation failed in strict mode: {config_path}")
                raise ValueError(f"Schema validation failed:\n{error_msg}")
            else:
                logger.warning(f"Schema validation errors in {config_path}:\n{error_msg}")
                # Only warn if explicitly opted out of strict mode

    # Merge: user settings as defaults, release config overrides
    merged_config = {}

    # Apply default artist if not specified
    if "artist" not in release_config and "default_artist" in user_settings:
        merged_config["artist"] = user_settings["default_artist"]

    # Apply default publisher if not specified in id3_metadata
    if "id3_metadata" in release_config:
        if (
            "publisher" not in release_config["id3_metadata"]
            and "default_publisher" in user_settings
        ):
            if "id3_metadata" not in merged_config:
                merged_config["id3_metadata"] = release_config["id3_metadata"].copy()
            merged_config["id3_metadata"]["publisher"] = user_settings[
                "default_publisher"
            ]

    # Apply default composer template and track number if id3_metadata exists
    if "id3_metadata" in release_config:
        # Apply default composer template if not specified
        if (
            "composer" not in release_config["id3_metadata"]
            and "default_composer_template" in user_settings
        ):
            if "id3_metadata" not in merged_config:
                merged_config["id3_metadata"] = release_config["id3_metadata"].copy()
            artist = release_config.get(
                "artist", user_settings.get("default_artist", "Artist")
            )
            composer_template = user_settings["default_composer_template"]
            merged_config["id3_metadata"]["composer"] = composer_template.format(
                artist=artist
            )

        # Apply default track number if not specified
        if "tracknumber" not in release_config["id3_metadata"]:
            if "id3_metadata" not in merged_config:
                merged_config["id3_metadata"] = release_config["id3_metadata"].copy()

            default_track = user_settings.get("default_track_number", "1")
            default_total = user_settings.get("default_total_tracks", "1")

            # Format: "1" for singles, "1/5" for multi-track
            if default_total == "1":
                merged_config["id3_metadata"]["tracknumber"] = default_track
            else:
                merged_config["id3_metadata"][
                    "tracknumber"
                ] = f"{default_track}/{default_total}"
    # Note: We don't auto-create id3_metadata just for track numbers
    # Track numbers are optional and should be explicitly set in release.json

    # Merge everything: user settings → release config → merged overrides
    final_config = {**user_settings, **release_config, **merged_config}

    # Clean up: remove default_* keys from final config (they're only for merging)
    final_config = {
        k: v for k, v in final_config.items() if not k.startswith("default_")
    }

    return final_config


def validate_config(config: Dict) -> bool:
    """Validate required configuration fields and types."""
    errors = []
    warnings = []

    # Required fields
    required_fields = {"artist": str, "title": str}

    for field, expected_type in required_fields.items():
        if field not in config:
            errors.append(f"Missing required field: '{field}'")
        elif not isinstance(config[field], expected_type):
            errors.append(
                f"Field '{field}' must be {expected_type.__name__}, got {type(config[field]).__name__}"
            )
        elif not config[field] or not str(config[field]).strip():
            errors.append(f"Field '{field}' cannot be empty")

    # Type validation for optional fields
    type_checks = {
        "bpm": int,
        "explicit": bool,
        "organize_stems": bool,
        "tag_stems": bool,
        "tag_audio": bool,
        "validate_cover": bool,
        "validate_compliance": bool,
        "strict_mode": bool,
        "overwrite_existing": bool,
    }

    for field, expected_type in type_checks.items():
        if field in config and not isinstance(config[field], expected_type):
            errors.append(
                f"Field '{field}' must be {expected_type.__name__}, "
                f"got {type(config[field]).__name__}"
            )

    # Value range validation
    if "bpm" in config:
        bpm = config["bpm"]
        if not isinstance(bpm, int) or bpm < 1 or bpm > 300:
            errors.append(f"Field 'bpm' must be integer between 1-300, got {bpm}")

    # Path validation
    path_fields = ["source_audio_dir", "source_stems_dir", "release_dir"]
    for field in path_fields:
        if field in config and config[field]:
            path_val = Path(config[field])
            if field.startswith("source_") and not path_val.exists():
                warnings.append(f"Source directory does not exist: {config[field]}")

    # Validate nested id3_metadata structure
    if "id3_metadata" in config:
        if not isinstance(config["id3_metadata"], dict):
            errors.append("Field 'id3_metadata' must be an object")
        else:
            # Validate track number format if present
            if "tracknumber" in config["id3_metadata"]:
                tracknum = config["id3_metadata"]["tracknumber"]
                if isinstance(tracknum, str):
                    # If contains "/", must be "X/Total" format
                    if "/" in tracknum:
                        parts = tracknum.split("/")
                        if len(parts) != 2 or not all(p.isdigit() for p in parts):
                            errors.append(
                                f"Field 'id3_metadata.tracknumber' must be format 'X/Total', "
                                f"got '{tracknum}'"
                            )
                    # If no "/", must be a single digit or "X" format
                    elif not tracknum.isdigit():
                        errors.append(
                            f"Field 'id3_metadata.tracknumber' must be a number or 'X/Total' format, "
                            f"got '{tracknum}'"
                        )

    # Check for invalid characters in artist/title (will be sanitized)
    invalid_chars = '<>:"/\\|?*'
    for field in ["artist", "title"]:
        if field in config:
            value = str(config[field])
            found_invalid = [c for c in invalid_chars if c in value]
            if found_invalid:
                warnings.append(
                    f"Field '{field}' contains invalid characters: {found_invalid}. "
                    f"They will be replaced with '_'."
                )

    # Optional but recommended fields
    if "source_audio_dir" not in config:
        warnings.append("'source_audio_dir' not specified, using default: ./runtime/input")

    # Validate paths if provided
    if "release_dir" in config and config["release_dir"]:
        release_path = Path(config["release_dir"])
        if release_path.is_absolute() and not release_path.parent.exists():
            warnings.append(
                f"Release directory parent does not exist: {release_path.parent}"
            )

    if errors:
        raise ValueError(
            f"Configuration validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    if warnings:
        for warning in warnings:
            print_warning(warning)

    return True


def validate_path_safety(path_str: str, base_dir: Optional[str] = None) -> Path:
    """
    Ensure path is safe and within expected directory.
    
    Args:
        path_str: Path string to validate
        base_dir: Optional base directory to ensure path is within
    
    Returns:
        Resolved absolute Path
    
    Raises:
        ValueError: If path is unsafe (contains traversal or outside base_dir)
    """
    path = Path(path_str)
    
    # Resolve to absolute path
    abs_path = path.resolve()
    
    # Check for path traversal attempts
    if '..' in path.parts:
        raise ValueError(f"Path traversal not allowed: {path_str}")
    
    # If base_dir provided, ensure path is within it
    if base_dir:
        base_abs = Path(base_dir).resolve()
        try:
            abs_path.relative_to(base_abs)
        except ValueError:
            raise ValueError(
                f"Path {path_str} is outside allowed directory {base_dir}"
            )
    
    return abs_path


def sanitize_filename(name):
    """
    Remove invalid filesystem characters from filename.
    
    Note: This function sanitizes filename components only.
    For path traversal prevention, use validate_path_safety().
    """
    if not name:
        return "Unknown"

    # Remove invalid characters for Windows/Unix
    invalid_chars = '<>:"/\\|?*'
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")

    # Remove leading/trailing dots and spaces (Windows issue)
    sanitized = sanitized.strip(". ")

    # Windows reserved names (case-insensitive)
    # These will cause FileNotFoundError or PermissionError on Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Check if sanitized name (without extension) is reserved
    name_base = sanitized.rsplit('.', 1)[0].upper() if '.' in sanitized else sanitized.upper()
    if name_base in reserved_names:
        sanitized = f"_{sanitized}"  # Prefix with underscore

    # Limit length (filesystem limits + safety margin)
    max_length = 200
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Ensure not empty after sanitization
    if not sanitized:
        sanitized = "Unknown"

    return sanitized


def validate_dependencies():
    """Check that required dependencies are installed."""
    missing = []

    try:
        import mutagen
    except ImportError:
        missing.append("mutagen (required for ID3 tagging)")

    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow (required for cover art validation)")

    if missing:
        raise ImportError(
            "Missing required dependencies:\n"
            + "\n".join(f"  - {dep}" for dep in missing)
            + "\n\nInstall with: pip install -r requirements.txt"
        )

    return True


def acquire_workflow_lock(release_dir: Path) -> Path:
    """Prevent concurrent workflow execution (atomic)."""
    lock_file = Path(release_dir) / ".workflow.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic lock acquisition using exclusive file creation
    try:
        # Use O_EXCL equivalent: open with 'x' mode (exclusive creation)
        # This is atomic - raises FileExistsError if file already exists
        with open(lock_file, 'x') as f:
            f.write(f"PID: {os.getpid()}\nTime: {datetime.now().isoformat()}\n")
        logger.debug(f"Acquired workflow lock: {lock_file}")
        return lock_file
    except FileExistsError:
        # Lock exists - check if stale
        lock_age = time.time() - lock_file.stat().st_mtime
        if lock_age > 3600:
            # Try to remove stale lock (may still race, but safer)
            logger.warning(f"Found stale lock file (age: {lock_age/60:.1f} minutes), attempting removal")
            try:
                lock_file.unlink()
                # Retry acquisition once
                with open(lock_file, 'x') as f:
                    f.write(f"PID: {os.getpid()}\nTime: {datetime.now().isoformat()}\n")
                logger.info(f"Removed stale lock and acquired new lock: {lock_file}")
                return lock_file
            except (FileExistsError, FileNotFoundError):
                # Another process got it or removed it
                pass
        
        # Lock is active or another process got it
        raise RuntimeError(
            f"Workflow already in progress for {release_dir}.\n"
            f"  Lock file: {lock_file}\n"
            f"  If no workflow is running, delete the lock file manually."
        )


def release_workflow_lock(lock_file: Optional[Path]) -> None:
    """Release workflow lock."""
    if lock_file and lock_file.exists():
        lock_file.unlink()
        logger.debug(f"Released workflow lock: {lock_file}")


def check_disk_space(path: Path, required_mb: float = 100, operation: str = "") -> bool:
    """
    Check if sufficient disk space is available.
    
    Args:
        path: Path to check disk space for
        required_mb: Required space in MB
        operation: Optional operation description for error message
    
    Returns:
        True if sufficient space available
    
    Raises:
        RuntimeError: If insufficient disk space
    """
    stat = shutil.disk_usage(path)
    free_mb = stat.free / (1024 * 1024)

    if free_mb < required_mb:
        operation_text = f" for {operation}" if operation else ""
        raise RuntimeError(
            f"Insufficient disk space{operation_text}: {free_mb:.1f}MB free, "
            f"need at least {required_mb}MB"
        )

    return True


def save_release_metadata(artist: str, title: str, metadata: Dict, output_dir: Path) -> Path:
    """Save release metadata JSON."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    release_metadata = {
        "artist": artist,
        "title": title,
        "created_date": datetime.now().isoformat() + "Z",
        **metadata,
    }

    metadata_file = output_path / f"{artist} - {title} - Metadata.json"
    logger.debug(f"Saving metadata to {metadata_file}")
    
    # Atomic write: use temp file, then atomic rename
    temp_metadata = metadata_file.with_suffix('.tmp')
    try:
        with open(temp_metadata, "w", encoding="utf-8") as f:
            json.dump(release_metadata, f, indent=2)
        # Atomic rename - file appears atomically at final location
        temp_metadata.replace(metadata_file)
    except Exception:
        # Cleanup temp file on failure
        if temp_metadata.exists():
            temp_metadata.unlink()
        raise

    logger.info(f"Release metadata saved: {metadata_file}")
    print_success(f"Generated release metadata: {metadata_file}")
    return metadata_file


def run_release_workflow(config: Dict, config_path: Optional[str] = None) -> bool:
    """Run the complete release workflow."""
    logger.info("Starting release workflow")
    if config_path:
        logger.info(f"Config file: {config_path}")
    
    validate_config(config)
    validate_dependencies()

    # Sanitize user input
    artist = sanitize_filename(config["artist"])
    title = sanitize_filename(config["title"])
    
    logger.info(f"Processing release: {artist} - {title}")

    debug_mode = config.get("debug", False)
    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # Track workflow status
    workflow_errors = []
    compliance_passed = True

    print_workflow_start()

    # Count total steps for progress tracking
    total_steps = 0
    if config.get("suno_url") or config.get("suno_metadata_file"):
        total_steps += 1
    if config.get("rename_audio", True):
        total_steps += 1
    if config.get("organize_stems", False):
        total_steps += 1
    if config.get("tag_stems", False):
        total_steps += 1
    if config.get("tag_audio", True):
        total_steps += 1
    if config.get("validate_cover", True):
        total_steps += 1
    if config.get("validate_compliance", True):
        total_steps += 1
    if True:  # Save metadata is always done
        total_steps += 1

    current_step = 0

    release_dir_str = config.get("release_dir", f"./runtime/output/{title}")
    
    # Validate path safety (prevent traversal)
    try:
        release_dir = validate_path_safety(release_dir_str)
    except ValueError as e:
        logger.error(f"Invalid release directory path: {e}")
        raise ValueError(f"Invalid release directory: {e}")
    
    # Validate source paths if provided
    if "source_audio_dir" in config:
        try:
            validate_path_safety(config["source_audio_dir"])
        except ValueError as e:
            logger.error(f"Invalid source audio directory path: {e}")
            raise ValueError(f"Invalid source audio directory: {e}")
    
    if "source_stems_dir" in config:
        try:
            validate_path_safety(config["source_stems_dir"])
        except ValueError as e:
            logger.error(f"Invalid source stems directory path: {e}")
            raise ValueError(f"Invalid source stems directory: {e}")
    
    logger.info(f"Release directory: {release_dir}")

    # Acquire workflow lock and check disk space
    lock_file = None
    try:
        logger.debug("Acquiring workflow lock")
        lock_file = acquire_workflow_lock(release_dir)
        logger.debug("Checking disk space")
        check_disk_space(release_dir, required_mb=500, operation="workflow initialization")  # Conservative estimate

        # Step 1: Extract Suno version (if URL provided)
        version_info = None
        if config.get("suno_url"):
            current_step += 1
            print_step(current_step, total_steps, "Extracting Suno version info")
            logger.info(f"Extracting Suno version from URL: {config['suno_url']}")
            version_info = extract_suno_version_from_url(config["suno_url"])
            logger.info(f"Extracted version: {version_info.get('version')}, build: {version_info.get('build_id')}")
            print_success(f"Version: {version_info.get('version')}, Build: {version_info.get('build_id')}")
            console.print()
        elif config.get("suno_metadata_file"):
            current_step += 1
            print_step(current_step, total_steps, "Extracting Suno version from metadata")
            version_info = extract_from_metadata_file(config["suno_metadata_file"])
            if version_info:
                print_success(f"Version: {version_info.get('version')}, Build: {version_info.get('build_id')}")
                console.print()

        # Step 2: Rename audio files
        if config.get("rename_audio", True):
            current_step += 1
            print_step(current_step, total_steps, "Renaming and organizing audio files")
            try:
                source_dir = config.get("source_audio_dir", "./runtime/input")
                logger.info(f"Renaming audio files from {source_dir}")
                
                # Check disk space before large file operations
                # Estimate required space: check source file sizes
                source_path = Path(source_dir)
                if source_path.exists():
                    # Calculate total size of audio files
                    audio_files = [f for f in list(source_path.glob("*.mp3")) + list(source_path.glob("*.wav")) if f.is_file()]
                    total_size = sum(f.stat().st_size for f in audio_files)
                    required_mb = (total_size / (1024 * 1024)) * 1.1  # 10% safety margin
                    if required_mb > 0:
                        check_disk_space(release_dir, required_mb=required_mb, operation="audio file copy")
                
                # Use retry for file operations (transient I/O errors)
                max_retries = config.get("max_retries", 3)
                with RetryContext(
                    max_attempts=max_retries,
                    retryable_exceptions=(IOError, OSError, PermissionError)
                ):
                    rename_audio_files(
                        artist=artist,
                        title=title,
                        source_dir=source_dir,
                        dest_dir=release_dir / "Audio",
                        overwrite=config.get("overwrite_existing", False),
                    )
                
                logger.info("Audio files renamed successfully")
                console.print()
            except Exception as e:
                logger.error(f"Error renaming audio files: {e}", exc_info=True)
                print_error(f"Error renaming audio files: {e}")
                
                # Always log full context, even if not shown to user
                source_dir = config.get("source_audio_dir", "./runtime/input")
                dest_dir = str(release_dir / "Audio")
                logger.debug(f"Source dir: {source_dir}, Dest dir: {dest_dir}, "
                           f"Artist: {artist}, Title: {title}")
                
                if debug_mode:
                    import traceback
                    from rich.traceback import install
                    install(show_locals=True)
                    console.print_exception()
                else:
                    # Show at least file path in error message
                    print_info(f"Source: {source_dir}, Destination: {dest_dir}")
                    print_info("Run with 'debug: true' in config for full traceback")
                console.print()

                if config.get("strict_mode", False):
                    logger.error("Strict mode enabled, workflow failed")
                    return False

        # Step 3: Organize stems (if applicable)
        if config.get("organize_stems", False):
            current_step += 1
            print_step(current_step, total_steps, "Organizing stems")
            try:
                organize_stems(
                    artist=artist,
                    title=title,
                    source_dir=config.get("source_stems_dir", "./runtime/input/stems"),
                    stems_dir=release_dir / "Stems",
                    overwrite=config.get("overwrite_existing", False),
                )
                console.print()
            except Exception as e:
                logger.error(f"Error organizing stems: {e}", exc_info=True)
                print_error(f"Error organizing stems: {e}")
                
                # Always log full context
                source_stems_dir = config.get("source_stems_dir", "./runtime/input/stems")
                stems_dir = str(release_dir / "Stems")
                logger.debug(f"Source stems dir: {source_stems_dir}, Dest stems dir: {stems_dir}, "
                           f"Artist: {artist}, Title: {title}")

                if debug_mode:
                    from rich.traceback import install
                    install(show_locals=True)
                    console.print_exception()
                else:
                    print_info(f"Source: {source_stems_dir}, Destination: {stems_dir}")
                    print_info("Run with 'debug: true' in config for full traceback")
                console.print()

                if config.get("strict_mode", False):
                    return False

        # Step 4: Tag stems (if applicable)
        if config.get("tag_stems", False):
            current_step += 1
            print_step(current_step, total_steps, "Tagging stems")
            try:
                batch_tag_stems(
                    stems_dir=str(release_dir / "Stems"), artist=artist, title=title
                )
                console.print()
            except Exception as e:
                logger.error(f"Error tagging stems: {e}", exc_info=True)
                print_error(f"Error tagging stems: {e}")
                
                # Always log full context
                stems_dir = str(release_dir / "Stems")
                logger.debug(f"Stems directory: {stems_dir}, "
                           f"Artist: {artist}, Title: {title}")

                if debug_mode:
                    from rich.traceback import install
                    install(show_locals=True)
                    console.print_exception()
                else:
                    print_info(f"Stems directory: {stems_dir}")
                    print_info("Run with 'debug: true' in config for full traceback")
                console.print()

                if config.get("strict_mode", False):
                    return False

        # Step 5: Tag audio files
        if config.get("tag_audio", True):
            current_step += 1
            print_step(current_step, total_steps, "Tagging audio files with ID3v2")
            audio_file = release_dir / "Audio" / f"{artist} - {title}.mp3"
            cover_dir = release_dir / "Cover"

            # Find cover art (check both JPG and PNG)
            expected_cover_jpg = cover_dir / f"{artist} - {title} - Cover.jpg"
            expected_cover_png = cover_dir / f"{artist} - {title} - Cover.png"
            cover_file = None

            if expected_cover_jpg.exists():
                cover_file = expected_cover_jpg
            elif expected_cover_png.exists():
                cover_file = expected_cover_png

            if not audio_file.exists():
                print_warning(f"Audio file not found: {audio_file}")
                print_info("Skipping tagging step")
                console.print()
            else:
                metadata = config.get("id3_metadata", {})
                metadata.setdefault("title", title)
                metadata.setdefault("artist", artist)
                metadata.setdefault("publisher", "Independent")

                # Add album artist (defaults to artist if not specified) - TPE2 (Strongly Recommended)
                if "album_artist" not in metadata:
                    metadata["album_artist"] = artist

                # Add BPM if available in config - TBPM (Strongly Recommended)
                if config.get("bpm") and "bpm" not in metadata:
                    metadata["bpm"] = config.get("bpm")

                # Add ISRC if available in config - TSRC (Strongly Recommended)
                if config.get("isrc") and "isrc" not in metadata:
                    metadata["isrc"] = config.get("isrc")

                # Add language if available in config - TLAN (Strongly Recommended)
                if config.get("language") and "language" not in metadata:
                    metadata["language"] = config.get("language")
                    # Map common language names to ISO 639-2 codes
                    lang_map = {
                        "english": "eng",
                        "spanish": "spa",
                        "french": "fra",
                        "german": "deu",
                        "italian": "ita",
                        "portuguese": "por",
                        "japanese": "jpn",
                        "chinese": "zho",
                        "korean": "kor",
                    }
                    lang_lower = config.get("language", "").lower()
                    if lang_lower in lang_map:
                        metadata["language_code"] = lang_map[lang_lower]

                # Add version info to comment if available
                if version_info:
                    comment = metadata.get("comment", "")
                    version_str = version_info.get("version", "unknown")
                    build_str = version_info.get("build_id", "unknown")
                    # Format version nicely (v5, v3.5.2, etc.)
                    if version_str and not version_str.startswith("v"):
                        version_str = f"v{version_str}"
                    if build_str and build_str != "unknown":
                        version_comment = (
                            f"AI-generated with Suno {version_str}, Build {build_str}"
                        )
                    else:
                        version_comment = f"AI-generated with Suno {version_str}"
                    if comment:
                        metadata["comment"] = f"{comment} | {version_comment}"
                    else:
                        metadata["comment"] = version_comment

                # Encoder (TSSE) - Optional metadata, only add if explicitly provided
                # Note: This is NOT a DistroKid requirement, just optional transparency
                if metadata.get("encoder"):
                    pass  # Already in metadata, will be used
                # Don't auto-add encoder - it's optional metadata only

                try:
                    tag_audio_file(
                        audio_path=str(audio_file),
                        cover_path=(
                            str(cover_file)
                            if cover_file and cover_file.exists()
                            else None
                        ),
                        metadata=metadata,
                    )
                    print()
                except Exception as e:
                    logger.error(f"Error tagging audio: {e}", exc_info=True)
                    print_error(f"Error tagging audio: {e}")
                    
                    # Always log full context
                    audio_path = str(audio_file)
                    cover_path = str(cover_file) if cover_file and cover_file.exists() else "None"
                    logger.debug(f"Audio file: {audio_path}, Cover art: {cover_path}, "
                               f"Artist: {artist}, Title: {title}")

                    if debug_mode:
                        from rich.traceback import install
                        install(show_locals=True)
                        console.print_exception()
                    else:
                        print_info(f"Audio file: {audio_path}")
                        if cover_file and cover_file.exists():
                            print_info(f"Cover art: {cover_path}")
                        print_info("Run with 'debug: true' in config for full traceback")
                    console.print()

                    if config.get("strict_mode", False):
                        return False

        # Step 6: Find, rename, and validate cover art
        if config.get("validate_cover", True):
            current_step += 1
            print_step(current_step, total_steps, "Finding and validating cover art")
            cover_dir = release_dir / "Cover"
            expected_cover_jpg = cover_dir / f"{artist} - {title} - Cover.jpg"
            expected_cover_png = cover_dir / f"{artist} - {title} - Cover.png"
            cover_file = None

            # First, check if correctly named file already exists
            if expected_cover_jpg.exists():
                cover_file = expected_cover_jpg
            elif expected_cover_png.exists():
                cover_file = expected_cover_png
            else:
                # Look for any image file in Cover directory
                if cover_dir.exists():
                    image_files = (
                        list(cover_dir.glob("*.jpg"))
                        + list(cover_dir.glob("*.jpeg"))
                        + list(cover_dir.glob("*.png"))
                    )

                    if image_files:
                        # Found an image - rename it to match convention
                        found_file = image_files[0]
                        # Determine extension (prefer JPG, fallback to PNG)
                        if found_file.suffix.lower() in [".jpg", ".jpeg"]:
                            cover_file = expected_cover_jpg
                        else:
                            cover_file = expected_cover_png

                        # Atomic rename: use temp file pattern for safety
                        try:
                            # If destination exists, remove it first (for overwrite case)
                            if cover_file.exists():
                                cover_file.unlink()
                            # Atomic rename
                            found_file.rename(cover_file)
                            print_success(f"Renamed cover art: {found_file.name} → {cover_file.name}")
                        except Exception as e:
                            print_warning(f"Could not rename cover art: {e}")
                            cover_file = found_file  # Use original file

            if cover_file and cover_file.exists():
                result = validate_cover_art(str(cover_file))
                if not result["valid"]:
                    print_warning("Cover art validation failed")
                    console.print()
                    if config.get("strict_mode", False):
                        return False
            else:
                print_warning(f"Cover art not found in: {cover_dir}")
                print_info(f"Expected: {expected_cover_jpg.name} or {expected_cover_png.name}")
                print_info(f"Or place any .jpg/.png file in {cover_dir} and it will be renamed automatically")
                console.print()

        # Step 7: Full compliance check
        if config.get("validate_compliance", True):
            current_step += 1
            print_step(current_step, total_steps, "Running full compliance check")
            audio_file = release_dir / "Audio" / f"{artist} - {title}.mp3"
            cover_dir = release_dir / "Cover"
            cover_file = None

            # Find cover art (check both JPG and PNG)
            expected_cover_jpg = cover_dir / f"{artist} - {title} - Cover.jpg"
            expected_cover_png = cover_dir / f"{artist} - {title} - Cover.png"

            if expected_cover_jpg.exists():
                cover_file = expected_cover_jpg
            elif expected_cover_png.exists():
                cover_file = expected_cover_png

            metadata = config.get("id3_metadata", {})
            metadata.setdefault("title", title)
            metadata.setdefault("artist", artist)
            metadata.setdefault("genre", config.get("genre", ""))

            if audio_file.exists():
                # Check for clipping first and auto-fix if enabled
                try:
                    audio_result = validate_audio_file(str(audio_file))

                    # Auto-fix clipping if enabled and detected
                    if config.get("auto_fix_clipping", False) and audio_result.get(
                        "clipping_detected", False
                    ):
                        print_info("Auto-fixing clipping with ffmpeg...")
                        try:
                            # Fix clipping by normalizing to -1 dB
                            fix_clipping_ffmpeg(
                                str(audio_file),
                                str(audio_file),  # Overwrite original
                                target_db=-1.0,
                            )
                            print_success("Clipping fixed - re-running compliance check...")
                            console.print()
                        except Exception as e:
                            logger.error(f"Could not auto-fix clipping: {e}", exc_info=True)
                            print_error(f"Could not auto-fix clipping: {e}")
                            
                            # Always log full context
                            audio_path = str(audio_file)
                            logger.debug(f"Audio file: {audio_path}, "
                                       f"Artist: {artist}, Title: {title}")
                            
                            if debug_mode:
                                import traceback
                                traceback.print_exc()
                            else:
                                print_info(f"Audio file: {audio_path}")
                                print_info("Run with 'debug: true' in config for full traceback")
                            workflow_errors.append("Auto-fix clipping failed")
                except ImportError:
                    # fix_clipping module not available, skip auto-fix
                    pass
                except Exception as e:
                    # If validate_audio_file fails, continue anyway
                    if debug_mode:
                        print_warning(f"Could not check clipping: {e}")

                # Cover art is optional for compliance check
                cover_path_for_check = (
                    str(cover_file) if cover_file and cover_file.exists() else None
                )
                is_valid = full_compliance_check(
                    audio_path=str(audio_file),
                    cover_path=cover_path_for_check,
                    metadata=metadata,
                )

                compliance_passed = is_valid

                if not is_valid:
                    workflow_errors.append("Compliance check failed - see errors above")

                if not is_valid and config.get("strict_mode", False):
                    return False
            else:
                print_warning("Cannot run compliance check - audio file not found")
                console.print()

        # Step 8: Save release metadata
        current_step += 1
        print_step(current_step, total_steps, "Saving release metadata")
        release_metadata = {
            "genre": config.get("genre", ""),
            "bpm": config.get("bpm"),
            "key": config.get("key"),
            "explicit": config.get("explicit", False),
            "language": config.get("language", "English"),
            "mood": config.get("mood"),
            "target_regions": config.get("target_regions", []),
            "isrc": config.get("isrc", ""),
            "upc": config.get("upc", ""),
            "suno_version": version_info.get("version") if version_info else None,
            "suno_build_id": version_info.get("build_id") if version_info else None,
        }

        save_release_metadata(
            artist=artist,
            title=title,
            metadata=release_metadata,
            output_dir=release_dir / "Metadata",
        )

        # Final status message with statistics
        console.print()
        if workflow_errors or not compliance_passed:
            print_warning("Workflow completed with warnings/errors")
            print_info(f"Release files ready in: {release_dir}")
            if workflow_errors:
                console.print()
                print_warning(f"Issues found ({len(workflow_errors)}):")
                for error in workflow_errors:
                    console.print(f"  [dim]-[/dim] {error}")
            if not compliance_passed:
                console.print()
                print_error("Compliance check failed - review errors above before uploading")
            console.print()
            print_info("Tip: Fix errors or set 'strict_mode: false' to continue anyway")
        else:
            print_workflow_complete(str(release_dir))

        return compliance_passed and len(workflow_errors) == 0
    finally:
        # Always release lock, even on error
        release_workflow_lock(lock_file)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[bold]Usage:[/bold] [green]python orchestrator.py <release.json>[/green]")
        console.print()
        console.print("[bold]Example release.json:[/bold]")
        from rich.json import JSON
        example_config = {
            "artist": "YourArtistName",
            "title": "Deep Dive",
            "release_dir": "./runtime/output/DeepDive",
            "suno_url": "https://suno.com/song/abc123xyz?v=3.5.2",
            "source_audio_dir": "./runtime/input",
            "source_stems_dir": "./runtime/input/stems",
            "genre": "Deep House",
            "bpm": 122,
            "id3_metadata": {
                "album": "Summer Vibes EP",
                "year": "2025",
                "composer": "YourArtistName + Suno AI",
            },
            "organize_stems": True,
            "tag_stems": False,
            "validate_compliance": True,
            "strict_mode": False,
        }
        json_obj = JSON.from_data(example_config)
        console.print(json_obj)
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config = load_config(config_path)
        success = run_release_workflow(config)
        sys.exit(0 if success else 1)
    except Exception as e:
        from rich.traceback import install
        install(show_locals=True)
        print_workflow_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
