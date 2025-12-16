#!/usr/bin/env python3
"""
DistroKid Release Packer - Main Orchestrator

Runs the complete release workflow from Suno export to DistroKid-ready files.
"""

import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

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


def load_user_settings():
    """Load user settings from artist-defaults.json (if exists)."""
    settings_file = Path("artist-defaults.json")
    if not settings_file.exists():
        return {}

    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
            # Filter out comment fields
            return {k: v for k, v in settings.items() if not k.startswith("_")}
    except (json.JSONDecodeError, UnicodeDecodeError):
        # If artist-defaults.json is invalid, just return empty dict
        return {}


def load_config(config_path):
    """Load configuration from JSON file, merging with user settings."""
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load user settings first (defaults)
    user_settings = load_user_settings()

    # Load release-specific config
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            release_config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in config file '{config_path}':\n"
            f"  Error: {e.msg}\n"
            f"  Line {e.lineno}, column {e.colno}\n"
            f"  Fix the JSON syntax and try again."
        )
    except UnicodeDecodeError as e:
        raise ValueError(
            f"Config file '{config_path}' is not valid UTF-8 text.\n"
            f"  Error: {e}\n"
            f"  Ensure the file is saved as UTF-8."
        )

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


def validate_config(config):
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
        warnings.append("'source_audio_dir' not specified, using default: ./exports")

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


def sanitize_filename(name):
    """Remove invalid filesystem characters from filename."""
    if not name:
        return "Unknown"

    # Remove invalid characters for Windows/Unix
    invalid_chars = '<>:"/\\|?*'
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, "_")

    # Remove leading/trailing dots and spaces (Windows issue)
    sanitized = sanitized.strip(". ")

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


def acquire_workflow_lock(release_dir):
    """Prevent concurrent workflow execution."""
    lock_file = Path(release_dir) / ".workflow.lock"

    if lock_file.exists():
        # Check if lock is stale (older than 1 hour)
        lock_age = time.time() - lock_file.stat().st_mtime
        if lock_age > 3600:
            print_warning(f"Removing stale lock file (age: {lock_age/60:.1f} minutes)")
            lock_file.unlink()
        else:
            raise RuntimeError(
                f"Workflow already in progress for {release_dir}.\n"
                f"  Lock file: {lock_file}\n"
                f"  If no workflow is running, delete the lock file manually."
            )

    # Create lock file
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(f"PID: {os.getpid()}\nTime: {datetime.now().isoformat()}\n")
    return lock_file


def release_workflow_lock(lock_file):
    """Release workflow lock."""
    if lock_file and lock_file.exists():
        lock_file.unlink()


def check_disk_space(path, required_mb=100):
    """Check if sufficient disk space is available."""
    stat = shutil.disk_usage(path)
    free_mb = stat.free / (1024 * 1024)

    if free_mb < required_mb:
        raise RuntimeError(
            f"Insufficient disk space: {free_mb:.1f}MB free, "
            f"need at least {required_mb}MB"
        )

    return True


def save_release_metadata(artist, title, metadata, output_dir):
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
    with open(metadata_file, "w") as f:
        json.dump(release_metadata, f, indent=2)

    print_success(f"Generated release metadata: {metadata_file}")
    return metadata_file


def run_release_workflow(config):
    """Run the complete release workflow."""
    validate_config(config)
    validate_dependencies()

    # Sanitize user input
    artist = sanitize_filename(config["artist"])
    title = sanitize_filename(config["title"])

    debug_mode = config.get("debug", False)

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

    release_dir = Path(config.get("release_dir", f"./Releases/{title}"))

    # Acquire workflow lock and check disk space
    lock_file = None
    try:
        lock_file = acquire_workflow_lock(release_dir)
        check_disk_space(release_dir, required_mb=500)  # Conservative estimate

        # Step 1: Extract Suno version (if URL provided)
        version_info = None
        if config.get("suno_url"):
            current_step += 1
            print_step(current_step, total_steps, "Extracting Suno version info")
            version_info = extract_suno_version_from_url(config["suno_url"])
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
                rename_audio_files(
                    artist=artist,
                    title=title,
                    source_dir=config.get("source_audio_dir", "./exports"),
                    dest_dir=release_dir / "Audio",
                    overwrite=config.get("overwrite_existing", False),
                )
                console.print()
            except Exception as e:
                print_error(f"Error renaming audio files: {e}")

                if debug_mode:
                    import traceback
                    from rich.traceback import install
                    install(show_locals=True)
                    console.print_exception()
                else:
                    print_info("Run with 'debug: true' in config for full traceback")
                console.print()

                if config.get("strict_mode", False):
                    return False

        # Step 3: Organize stems (if applicable)
        if config.get("organize_stems", False):
            current_step += 1
            print_step(current_step, total_steps, "Organizing stems")
            try:
                organize_stems(
                    artist=artist,
                    title=title,
                    source_dir=config.get("source_stems_dir", "./exports/stems"),
                    stems_dir=release_dir / "Stems",
                    overwrite=config.get("overwrite_existing", False),
                )
                console.print()
            except Exception as e:
                print_error(f"Error organizing stems: {e}")

                if debug_mode:
                    from rich.traceback import install
                    install(show_locals=True)
                    console.print_exception()
                else:
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
                print_error(f"Error tagging stems: {e}")

                if debug_mode:
                    from rich.traceback import install
                    install(show_locals=True)
                    console.print_exception()
                else:
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
                    print_error(f"Error tagging audio: {e}")

                    if debug_mode:
                        from rich.traceback import install
                        install(show_locals=True)
                        console.print_exception()
                    else:
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

                        # Rename the file
                        try:
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
                            print_error(f"Could not auto-fix clipping: {e}")
                            if debug_mode:
                                import traceback

                                traceback.print_exc()
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
            "release_dir": "./Releases/DeepDive",
            "suno_url": "https://suno.com/song/abc123xyz?v=3.5.2",
            "source_audio_dir": "./exports",
            "source_stems_dir": "./exports/stems",
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
