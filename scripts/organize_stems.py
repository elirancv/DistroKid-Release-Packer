import json
import shutil
import wave
from datetime import datetime
from pathlib import Path
from rich_utils import print_warning, print_success, console


def organize_stems(artist, title, source_dir, stems_dir, overwrite=False):
    """Organize and validate stems with metadata generation."""
    source = Path(source_dir)
    stems_path = Path(stems_dir)

    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    stems_path.mkdir(parents=True, exist_ok=True)

    # Expected stem names
    expected_stems = ["Vocals", "Drums", "Bass", "Harmony", "Lead", "FX"]

    stems_data = {
        "track": title,
        "artist": artist,
        "export_date": datetime.now().isoformat() + "Z",
        "stems": [],
    }

    # Find and organize stem files
    for stem_name in expected_stems:
        # Look for files containing stem name
        pattern = f"*{stem_name}*"
        matching_files = list(source.glob(pattern))

        if matching_files:
            if len(matching_files) > 1:
                print_warning(f"Multiple files match '{stem_name}':")
                for f in matching_files:
                    console.print(f"     [dim]-[/dim] {f.name}")
                console.print(f"   [dim]Using:[/dim] {matching_files[0].name}")

            file = matching_files[0]
            new_name = f"{artist} - {title} - {stem_name}.wav"
            dest_file = stems_path / new_name

            # Check for existing file
            if dest_file.exists() and not overwrite:
                raise FileExistsError(
                    f"File already exists: {dest_file}\n"
                    f"  To overwrite, set 'overwrite_existing: true' in release.json"
                )

            # Copy file
            shutil.copy2(file, dest_file)

            # Get file info
            try:
                with wave.open(str(dest_file), "rb") as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    duration = frames / float(sample_rate)
                    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
            except Exception as e:
                print_warning(f"Could not read duration for {new_name}: {e}")
                duration_str = "N/A"

            stems_data["stems"].append(
                {"name": stem_name, "file": new_name, "duration": duration_str}
            )
            print_success(f"Organized: {new_name}")

    # Save metadata
    metadata_file = stems_path / f"{artist} - {title} - Stems_Metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(stems_data, f, indent=2)

    print_success(f"Generated metadata: {metadata_file}")
    return stems_data


if __name__ == "__main__":
    # Usage
    organize_stems(
        "YourArtistName", "Deep Dive", "./exports/stems", "./Releases/DeepDive/Stems"
    )
