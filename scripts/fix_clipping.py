#!/usr/bin/env python3
"""
Fix audio clipping by normalizing to safe levels using ffmpeg.
"""

import subprocess
import sys
from pathlib import Path
from rich_utils import print_info, print_success, print_error, console

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7
        pass


def fix_clipping_ffmpeg(audio_path, output_path=None, target_db=-1.0):
    """
    Fix audio clipping by normalizing to target dB level using ffmpeg.

    Args:
        audio_path: Path to input audio file
        output_path: Path to output file (if None, overwrites input using temp file)
        target_db: Target dB level (default: -1.0 for safe headroom)

    Returns:
        Path to fixed audio file
    """
    audio_file = Path(audio_path)

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "ffmpeg not found. Install ffmpeg:\n"
            "  Windows: https://ffmpeg.org/download.html\n"
            "  Or: choco install ffmpeg\n"
            "  Or: winget install ffmpeg"
        )

    # Determine output path
    if output_path is None:
        output_path = audio_file
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # FFmpeg cannot write to the same file it's reading from
    # Use temp file if input and output are the same
    use_temp = str(audio_file.resolve()) == str(Path(output_path).resolve())
    temp_path = None

    if use_temp:
        # Create temp file in same directory
        temp_path = audio_file.with_suffix(f".temp{audio_file.suffix}")
        actual_output = temp_path
    else:
        actual_output = Path(output_path)
        actual_output.parent.mkdir(parents=True, exist_ok=True)

    # Build ffmpeg command
    # -i: input file
    # -af "volume=-1dB": Apply volume filter to reduce by 1 dB
    # -y: Overwrite output file if exists
    # -loglevel error: Only show errors
    cmd = [
        "ffmpeg",
        "-i",
        str(audio_file),
        "-af",
        f"volume={target_db}dB",
        "-y",  # Overwrite output
        "-loglevel",
        "error",
        str(actual_output),
    ]

    print_info(f"Fixing clipping: {audio_file.name}")
    console.print(f"   [dim]Target level:[/dim] {target_db} dB")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # If we used a temp file, replace original with it
        if use_temp:
            temp_path.replace(audio_file)
            print_success(f"Fixed audio saved: {audio_file.name}")

            # Remove encoder tag that FFmpeg adds (TSSE frame)
            # This is optional metadata and not needed for DistroKid
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3

                audio_mp3 = MP3(str(audio_file), ID3=ID3)
                if audio_mp3.tags and "TSSE" in audio_mp3.tags:
                    del audio_mp3.tags["TSSE"]
                    audio_mp3.save()
            except Exception:
                # If tagging cleanup fails, continue anyway
                pass

            return str(audio_file)
        else:
            print_success(f"Fixed audio saved: {actual_output.name}")

            # Remove encoder tag that FFmpeg adds (TSSE frame)
            try:
                from mutagen.mp3 import MP3
                from mutagen.id3 import ID3

                audio_mp3 = MP3(str(actual_output), ID3=ID3)
                if audio_mp3.tags and "TSSE" in audio_mp3.tags:
                    del audio_mp3.tags["TSSE"]
                    audio_mp3.save()
            except Exception:
                # If tagging cleanup fails, continue anyway
                pass

            return str(actual_output)

    except subprocess.CalledProcessError as e:
        # Clean up temp file on error
        if temp_path and temp_path.exists():
            temp_path.unlink()
        error_msg = e.stderr if e.stderr else "Unknown ffmpeg error"
        raise RuntimeError(f"ffmpeg failed: {error_msg}")


def fix_clipping_in_place(audio_path, target_db=-1.0):
    """
    Fix clipping by normalizing in place (overwrites original).

    Args:
        audio_path: Path to audio file
        target_db: Target dB level (default: -1.0)

    Returns:
        Path to fixed file (same as input)
    """
    # Create temporary output path
    audio_file = Path(audio_path)
    temp_path = audio_file.with_suffix(f".temp{audio_file.suffix}")

    try:
        # Fix to temp file
        fix_clipping_ffmpeg(audio_path, temp_path, target_db)

        # Replace original with fixed version
        temp_path.replace(audio_file)

        print_success(f"Original file updated: {audio_file.name}")
        return str(audio_file)

    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[bold]Usage:[/bold] [green]python fix_clipping.py <audio_file> [output_file] [target_db][/green]")
        console.print()
        console.print("[bold]Examples:[/bold]")
        console.print("  [dim]python fix_clipping.py track.mp3[/dim]")
        console.print("  [dim]python fix_clipping.py track.mp3 track-fixed.mp3[/dim]")
        console.print("  [dim]python fix_clipping.py track.mp3 track-fixed.mp3 -2.0[/dim]")
        sys.exit(1)

    audio_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    target_db = float(sys.argv[3]) if len(sys.argv) > 3 else -1.0

    try:
        if output_path:
            fix_clipping_ffmpeg(audio_path, output_path, target_db)
        else:
            fix_clipping_in_place(audio_path, target_db)
        console.print()
        print_success("Clipping fixed successfully!")
    except Exception as e:
        console.print()
        print_error(f"Error: {e}")
        sys.exit(1)
