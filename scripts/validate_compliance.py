import os
import wave
from pathlib import Path

try:
    from PIL import Image
    from mutagen.mp3 import MP3

    PIL_AVAILABLE = True
    MUTAGEN_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    MUTAGEN_AVAILABLE = False
    from rich_utils import print_warning
    if not PIL_AVAILABLE:
        print_warning("PIL/Pillow not installed. Install with: pip install Pillow")
    if not MUTAGEN_AVAILABLE:
        print_warning("mutagen not installed. Install with: pip install mutagen")

try:
    import librosa
    import soundfile as sf

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


MAX_AUDIO_SIZE_MB = 500
MAX_COVER_SIZE_MB = 5
REQUIRED_DIMENSIONS = (3000, 3000)
MIN_DURATION_SECONDS = 1
MAX_DURATION_SECONDS = 7200  # 2 hours
RECOMMENDED_SAMPLE_RATES = [44100, 48000]


def validate_audio_file(audio_path):
    """Validate audio file meets DistroKid requirements."""
    errors = []
    warnings = []

    file_path = Path(audio_path)

    if not file_path.exists():
        return {
            "valid": False,
            "errors": [f"Audio file not found: {audio_path}"],
            "warnings": [],
            "file_size_mb": None,
            "duration": None,
        }

    # Check file format
    valid_formats = [".wav", ".mp3", ".flac", ".m4a"]
    if file_path.suffix.lower() not in valid_formats:
        errors.append(
            f"Invalid format: {file_path.suffix}. Must be WAV, MP3, FLAC, or M4A"
        )

    # Check file size (500MB limit)
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb > MAX_AUDIO_SIZE_MB:
        errors.append(
            f"File too large: {file_size_mb:.2f}MB (max {MAX_AUDIO_SIZE_MB}MB)"
        )

    # Check duration and sample rate
    duration = None
    sample_rate = None

    try:
        if file_path.suffix.lower() == ".wav":
            with wave.open(str(audio_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()  # bytes per sample
                bit_depth = sample_width * 8  # convert to bits

                # Check channels (should be stereo = 2)
                if channels != 2:
                    warnings.append(f"Channels: {channels} (recommended: 2 for stereo)")

                # Check bit depth (should be 16 or 24)
                if bit_depth not in [16, 24]:
                    warnings.append(
                        f"Bit depth: {bit_depth}-bit (recommended: 16-bit or 24-bit)"
                    )
        elif MUTAGEN_AVAILABLE:
            # Use mutagen for MP3, FLAC, M4A
            audio = None
            channels = None
            bit_depth = None

            if file_path.suffix.lower() == ".mp3":
                audio = MP3(audio_path)
                # MP3 is lossy, bit depth is not meaningful
                channels = (
                    audio.info.channels if hasattr(audio.info, "channels") else None
                )
            else:
                # Try as FLAC or M4A
                try:
                    if file_path.suffix.lower() == ".flac":
                        from mutagen.flac import FLAC

                        audio = FLAC(audio_path)
                        # FLAC can have bit depth info
                        if hasattr(audio.info, "bits_per_sample"):
                            bit_depth = audio.info.bits_per_sample
                        channels = (
                            audio.info.channels
                            if hasattr(audio.info, "channels")
                            else None
                        )
                    elif file_path.suffix.lower() == ".m4a":
                        from mutagen.mp4 import MP4

                        audio = MP4(audio_path)
                        # M4A is lossy, bit depth is not meaningful
                        channels = (
                            audio.info.channels
                            if hasattr(audio.info, "channels")
                            else None
                        )
                except ImportError:
                    warnings.append("mutagen FLAC/MP4 support not available")

            if audio:
                duration = audio.info.length
                sample_rate = (
                    audio.info.sample_rate
                    if hasattr(audio.info, "sample_rate")
                    else None
                )

                # Check channels for non-WAV files (should be stereo = 2)
                if channels is not None and channels != 2:
                    warnings.append(f"Channels: {channels} (recommended: 2 for stereo)")
                elif channels is None and file_path.suffix.lower() in [".flac", ".m4a"]:
                    warnings.append("Could not determine channel count")

                # Check bit depth for FLAC (should be 16 or 24)
                if bit_depth is not None and bit_depth not in [16, 24]:
                    warnings.append(
                        f"Bit depth: {bit_depth}-bit (recommended: 16-bit or 24-bit)"
                    )
            else:
                warnings.append(
                    f"Could not read audio properties for {file_path.suffix}"
                )
        else:
            warnings.append(
                "Could not read audio properties (install mutagen for MP3/FLAC/M4A)"
            )

        # Duration check (1 second to 2 hours)
        if duration is not None:
            if duration < MIN_DURATION_SECONDS:
                errors.append(
                    f"Duration too short: {duration:.2f}s (min {MIN_DURATION_SECONDS}s)"
                )
            elif duration > MAX_DURATION_SECONDS:
                errors.append(
                    f"Duration too long: {duration/60:.2f}min (max {MAX_DURATION_SECONDS/3600}h)"
                )

        # Sample rate check
        if sample_rate and sample_rate not in RECOMMENDED_SAMPLE_RATES:
            warnings.append(
                f"Sample rate {sample_rate}Hz (recommended: {RECOMMENDED_SAMPLE_RATES[0]/1000}kHz or {RECOMMENDED_SAMPLE_RATES[1]/1000}kHz)"
            )
    except Exception as e:
        errors.append(f"Error reading audio file: {e}")

    # Check for clipping (requires librosa)
    clipping_detected = False
    if LIBROSA_AVAILABLE and duration and duration > 0:
        try:
            # Load audio file (librosa handles WAV, MP3, FLAC, M4A)
            y, sr = librosa.load(str(audio_path), sr=None, mono=False)

            # Check for clipping: any sample at or above 0 dBFS (1.0 or -1.0)
            if y.ndim == 1:  # Mono
                max_amplitude = abs(y).max()
            else:  # Stereo or multi-channel
                max_amplitude = abs(y).max()

            # Clipping threshold: samples at or very close to 1.0 (0 dBFS)
            # Using 0.99 as threshold to catch hard clipping
            if max_amplitude >= 0.99:
                clipping_detected = True
                errors.append(
                    f"Audio clipping detected (max amplitude: {max_amplitude:.4f}, threshold: 0.99)"
                )
            elif max_amplitude >= 0.95:
                warnings.append(
                    f"Audio near clipping (max amplitude: {max_amplitude:.4f}, recommended: <0.95)"
                )
        except Exception as e:
            # If librosa fails, don't fail the entire validation
            warnings.append(f"Could not check for clipping: {e}")
    elif not LIBROSA_AVAILABLE:
        warnings.append(
            "Clipping check skipped (install librosa and soundfile: pip install librosa soundfile)"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "file_size_mb": file_size_mb,
        "duration": duration,
        "clipping_detected": clipping_detected,
    }


def validate_cover_art(cover_path):
    """Validate cover art meets DistroKid requirements."""
    if not PIL_AVAILABLE:
        raise ImportError(
            "Pillow library required for cover art validation. "
            "Install with: pip install Pillow"
        )

    errors = []
    warnings = []

    cover_file = Path(cover_path)

    if not cover_file.exists():
        return {
            "valid": False,
            "errors": [f"Cover art file not found: {cover_path}"],
            "warnings": [],
        }

    try:
        img = Image.open(cover_file)
        width, height = img.size
        file_size_mb = os.path.getsize(cover_path) / (1024 * 1024)

        # Format check
        if not cover_path.lower().endswith((".jpg", ".jpeg", ".png")):
            errors.append("Format must be JPG or PNG")

        # Size check (3000×3000)
        if width != REQUIRED_DIMENSIONS[0] or height != REQUIRED_DIMENSIONS[1]:
            errors.append(
                f"Dimensions must be {REQUIRED_DIMENSIONS[0]}×{REQUIRED_DIMENSIONS[1]}, got {width}×{height}"
            )

        # Aspect ratio check
        aspect_ratio = width / height
        if abs(aspect_ratio - 1.0) > 0.01:
            errors.append(f"Must be square (1:1), got {aspect_ratio:.3f}")

        # File size check (5MB limit)
        if file_size_mb > MAX_COVER_SIZE_MB:
            errors.append(
                f"File too large: {file_size_mb:.2f}MB (max {MAX_COVER_SIZE_MB}MB)"
            )
        elif file_size_mb > 3:
            warnings.append(
                f"File size {file_size_mb:.2f}MB (close to {MAX_COVER_SIZE_MB}MB limit)"
            )

    except Exception as e:
        errors.append(f"Error reading image: {e}")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def validate_metadata(metadata):
    """Validate metadata fields meet DistroKid requirements."""
    errors = []
    warnings = []

    # Title check (1-200 characters)
    title = metadata.get("title", "")
    if len(title) < 1:
        errors.append("Title is required")
    elif len(title) > 200:
        errors.append(f"Title too long: {len(title)} chars (max 200)")

    # Artist check (1-200 characters)
    artist = metadata.get("artist", "")
    if len(artist) < 1:
        errors.append("Artist is required")
    elif len(artist) > 200:
        errors.append(f"Artist too long: {len(artist)} chars (max 200)")

    # Genre check (should be valid)
    genre = metadata.get("genre", "")
    if not genre:
        warnings.append("Genre recommended but not required")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def full_compliance_check(audio_path, cover_path, metadata):
    """Run all compliance checks and return summary."""
    from rich_utils import console, print_success, print_error, print_warning, print_info, create_table
    
    console.print()
    console.print("[bold cyan]Running DistroKid Compliance Checks[/bold cyan]")
    console.print()

    audio_result = validate_audio_file(audio_path)

    # Cover art is optional - only validate if provided
    cover_result = {"valid": True, "errors": [], "warnings": []}
    if cover_path:
        cover_result = validate_cover_art(cover_path)

    metadata_result = validate_metadata(metadata)

    all_valid = (
        audio_result["valid"] and cover_result["valid"] and metadata_result["valid"]
    )

    # Create compliance results table
    table = create_table("Compliance Check Results", ["Category", "Status", "Details"])
    
    # Audio File
    audio_status = "[bold green]PASSED[/bold green]" if audio_result["valid"] else "[bold red]FAILED[/bold red]"
    audio_details = "\n".join([f"[red]- {e}[/red]" for e in audio_result["errors"]] + 
                              [f"[yellow][WARN] {w}[/yellow]" for w in audio_result.get("warnings", [])])
    if not audio_details:
        audio_details = "[dim]No issues[/dim]"
    table.add_row("[cyan]Audio File[/cyan]", audio_status, audio_details)
    
    # Cover Art
    cover_status = "[bold green]PASSED[/bold green]" if cover_result["valid"] else "[bold red]FAILED[/bold red]"
    cover_details = "\n".join([f"[red]- {e}[/red]" for e in cover_result["errors"]] + 
                              [f"[yellow][WARN] {w}[/yellow]" for w in cover_result.get("warnings", [])])
    if not cover_details:
        cover_details = "[dim]No issues[/dim]"
    table.add_row("[cyan]Cover Art[/cyan]", cover_status, cover_details)
    
    # Metadata
    metadata_status = "[bold green]PASSED[/bold green]" if metadata_result["valid"] else "[bold red]FAILED[/bold red]"
    metadata_details = "\n".join([f"[red]- {e}[/red]" for e in metadata_result["errors"]] + 
                                  [f"[yellow][WARN] {w}[/yellow]" for w in metadata_result.get("warnings", [])])
    if not metadata_details:
        metadata_details = "[dim]No issues[/dim]"
    table.add_row("[cyan]Metadata[/cyan]", metadata_status, metadata_details)
    
    console.print(table)
    console.print()
    
    if all_valid:
        print_success("All checks passed - Ready for upload")
    else:
        print_error("Fix errors before upload")

    return all_valid


if __name__ == "__main__":
    # Usage
    metadata = {"title": "Deep Dive", "artist": "YourArtistName", "genre": "Deep House"}

    full_compliance_check("YourArtistName - Deep Dive.mp3", "cover.jpg", metadata)
