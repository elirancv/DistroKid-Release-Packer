import os
from pathlib import Path

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    from rich_utils import print_warning
    print_warning("PIL/Pillow not installed. Install with: pip install Pillow")


MAX_COVER_SIZE_MB = 5
REQUIRED_DIMENSIONS = (3000, 3000)


def validate_cover_art(image_path):
    """Validate cover art meets DistroKid requirements."""
    if not PIL_AVAILABLE:
        raise ImportError(
            "Pillow library required for cover art validation. "
            "Install with: pip install Pillow"
        )

    image_file = Path(image_path)

    if not image_file.exists():
        return {
            "valid": False,
            "errors": [f"Cover art file not found: {image_path}"],
            "warnings": [],
        }

    errors = []
    warnings = []

    try:
        img = Image.open(image_file)
        width, height = img.size
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

        # Format check
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
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

        # Color mode check (should be RGB)
        if img.mode != "RGB":
            warnings.append(f"Color mode: {img.mode} (recommended: RGB)")

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

    valid = len(errors) == 0

    from rich_utils import print_success, print_error, print_warning, console
    
    if valid:
        print_success(f"Cover art validation passed: {image_file.name}")
    else:
        print_error(f"Cover art validation failed: {image_file.name}")
        for error in errors:
            console.print(f"  [red]-[/red] {error}")

    for warning in warnings:
        print_warning(warning)

    return {"valid": valid, "errors": errors, "warnings": warnings}


if __name__ == "__main__":
    # Usage
    from rich_utils import console
    result = validate_cover_art("./runtime/output/TrackName/Cover/cover.jpg")
    console.print()
    status = "[bold green]PASSED[/bold green]" if result['valid'] else "[bold red]FAILED[/bold red]"
    console.print(f"[bold]Validation result:[/bold] {status}")
