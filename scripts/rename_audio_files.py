import shutil
from pathlib import Path
from rich_utils import print_warning, print_success


def rename_audio_files(artist, title, source_dir, dest_dir, overwrite=False):
    """Rename and organize audio files with validation."""
    source = Path(source_dir)
    dest = Path(dest_dir)

    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    dest.mkdir(parents=True, exist_ok=True)

    # Find audio files
    audio_files = list(source.glob("*.wav")) + list(source.glob("*.mp3"))

    if not audio_files:
        print_warning(f"No audio files found in {source_dir}")
        return

    for file in audio_files:
        new_name = f"{artist} - {title}{file.suffix}"

        dest_file = dest / new_name

        # Check for existing file
        if dest_file.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {dest_file}\n"
                f"  To overwrite, set 'overwrite_existing: true' in release.json"
            )

        shutil.copy2(file, dest_file)
        print_success(f"Renamed: {new_name}")


if __name__ == "__main__":
    # Usage
    rename_audio_files(
        "Your Artist", "Your Title", "./exports", "./Releases/TrackName/Audio"
    )
