from pathlib import Path

try:
    from mutagen.id3 import ID3
    from mutagen.wave import WAVE

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("⚠️  mutagen not installed. Install with: pip install mutagen")


def tag_stem_file(stem_path, artist, title, stem_type):
    """Tag a WAV stem file with ID3v2 metadata (WAV supports ID3 tags)."""
    if not MUTAGEN_AVAILABLE:
        print("✗ mutagen library required for tagging")
        return False

    stem_file = Path(stem_path)

    if not stem_file.exists():
        print(f"✗ Stem file not found: {stem_path}")
        return False

    try:
        # WAV files can have ID3 tags
        audio = WAVE(str(stem_file))

        # Create ID3 tag if it doesn't exist
        if audio.tags is None:
            audio.add_tags()

        # Add tags
        audio.tags["TIT2"] = f"{title} - {stem_type}"  # Title with stem type
        audio.tags["TPE1"] = artist  # Artist
        audio.tags["TALB"] = title  # Album (track title)
        audio.tags["TCON"] = "Stem"  # Genre/Type
        audio.tags["COMM"] = f"Stem type: {stem_type}"  # Comment

        audio.save()
        print(f"✓ Tagged stem: {stem_file.name}")
        return True
    except Exception as e:
        print(f"✗ Error tagging {stem_path}: {e}")
        return False


def batch_tag_stems(stems_dir, artist, title):
    """Tag all stems in a directory."""
    stems_path = Path(stems_dir)

    if not stems_path.exists():
        raise FileNotFoundError(f"Stems directory not found: {stems_dir}")

    stem_files = list(stems_path.glob("*.wav"))

    if not stem_files:
        print(f"⚠️  No WAV files found in {stems_dir}")
        return

    for stem_file in stem_files:
        # Extract stem type from filename (e.g., "Artist - Title - Vocals.wav")
        stem_name = stem_file.stem
        if " - " in stem_name:
            parts = stem_name.split(" - ")
            if len(parts) >= 3:
                stem_type = parts[-1]  # Last part is stem type
            else:
                stem_type = "Unknown"
        else:
            stem_type = "Unknown"

        tag_stem_file(str(stem_file), artist, title, stem_type)

    print(f"✓ Tagged {len(stem_files)} stem files")


if __name__ == "__main__":
    # Usage
    batch_tag_stems("./Releases/DeepDive/Stems", "YourArtistName", "Deep Dive")
