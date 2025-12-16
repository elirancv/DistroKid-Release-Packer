import shutil
from pathlib import Path

try:
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, APIC, TPUB, TPE2, TCOP, TBPM, TSRC, TSSE, TLAN, COMM
    from mutagen.mp3 import MP3

    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    from rich_utils import print_warning
    print_warning("mutagen not installed. Install with: pip install mutagen")


def tag_audio_file(audio_path, cover_path, metadata):
    """Apply ID3v2 tags and embed cover art to MP3 file."""
    from rich_utils import print_warning, print_success
    
    if not MUTAGEN_AVAILABLE:
        raise ImportError(
            "mutagen library required for tagging. " "Install with: pip install mutagen"
        )

    audio_file = Path(audio_path)

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if audio_file.suffix.lower() not in [".mp3"]:
        raise ValueError(f"Invalid format: {audio_file.suffix}. Only MP3 supported")

    # Load low-level ID3 FIRST to delete old COMM frames before any saves
    audio_mp3 = MP3(str(audio_file), ID3=ID3)
    if audio_mp3.tags is None:
        audio_mp3.add_tags()

    # Delete ALL existing comment frames FIRST (before EasyID3 saves)
    # This prevents old comments from persisting
    # COMM frames can have different descriptors/languages (e.g., COMM::eng)
    # TXXX frames can also store comments (e.g., TXXX:comment)
    if audio_mp3.tags:
        # Delete all COMM frames (regardless of descriptor/language)
        comm_keys = [key for key in audio_mp3.tags.keys() if key.startswith("COMM")]
        for key in comm_keys:
            del audio_mp3.tags[key]
        # Delete TXXX frames with description 'comment' (user-defined text frames)
        txxx_keys = [
            key
            for key in audio_mp3.tags.keys()
            if key.startswith("TXXX") and ":comment" in key.lower()
        ]
        for key in txxx_keys:
            del audio_mp3.tags[key]
    audio_mp3.save()  # Save immediately to remove old comments

    # Now use EasyID3 for simple string-based tagging
    try:
        audio = EasyID3(str(audio_file))
    except:
        # If file doesn't have ID3 tags, create them
        audio = MP3(str(audio_file))
        audio.add_tags()
        audio.save()
        audio = EasyID3(str(audio_file))

    # Add basic tags (EasyID3 handles strings directly)
    # REQUIRED TAGS (DistroKid 2025 Standard)
    if metadata.get("title"):
        audio["title"] = metadata.get("title")  # TIT2
    if metadata.get("artist"):
        audio["artist"] = metadata.get("artist")  # TPE1
    if metadata.get("album"):
        audio["album"] = metadata.get("album")  # TALB
    if metadata.get("genre"):
        audio["genre"] = metadata.get("genre")  # TCON
    if metadata.get("year"):
        audio["date"] = metadata.get("year")  # TYER/TDRC
    if metadata.get("tracknumber"):
        audio["tracknumber"] = metadata.get("tracknumber")  # TRCK
    if metadata.get("composer"):
        audio["composer"] = metadata.get("composer")  # TCOM (Strongly Recommended)

    # Save EasyID3 tags
    audio.save()

    # Reload low-level ID3 after EasyID3 save
    audio_mp3 = MP3(str(audio_file), ID3=ID3)
    if audio_mp3.tags is None:
        audio_mp3.add_tags()

    # STRONGLY RECOMMENDED TAGS (DistroKid 2025 Standard)
    # Album Artist (TPE2) - Prevents compilation issues
    if metadata.get("album_artist"):
        audio_mp3.tags.add(TPE2(encoding=3, text=metadata.get("album_artist")))
    elif metadata.get("artist"):
        # Default to same as artist if not specified
        audio_mp3.tags.add(TPE2(encoding=3, text=metadata.get("artist")))

    # Publisher (TPUB) - Even "Self-Released"
    if metadata.get("publisher"):
        audio_mp3.tags.add(
            TPUB(encoding=3, text=metadata.get("publisher", "Independent"))
        )

    # Copyright (TCOP) - Ownership clarity
    if metadata.get("copyright"):
        audio_mp3.tags.add(TCOP(encoding=3, text=metadata.get("copyright")))
    elif metadata.get("artist") and metadata.get("year"):
        # Auto-generate copyright: © YEAR ARTIST
        copyright_text = f"© {metadata.get('year')} {metadata.get('artist')}"
        audio_mp3.tags.add(TCOP(encoding=3, text=copyright_text))

    # BPM (TBPM) - DJ / catalog systems
    if metadata.get("bpm"):
        audio_mp3.tags.add(TBPM(encoding=3, text=str(metadata.get("bpm"))))

    # ISRC (TSRC) - DistroKid will generate, but archive it
    if metadata.get("isrc"):
        audio_mp3.tags.add(TSRC(encoding=3, text=metadata.get("isrc")))

    # Encoder (TSSE) - Optional metadata only (NOT a DistroKid requirement)
    # Remove existing TSSE frames if encoder is not provided
    if "TSSE" in audio_mp3.tags:
        if metadata.get("encoder"):
            # Update existing encoder
            del audio_mp3.tags["TSSE"]
            audio_mp3.tags.add(TSSE(encoding=3, text=metadata.get("encoder")))
        else:
            # Remove encoder if not provided
            del audio_mp3.tags["TSSE"]
    elif metadata.get("encoder"):
        # Add encoder only if explicitly provided
        audio_mp3.tags.add(TSSE(encoding=3, text=metadata.get("encoder")))

    # Language (TLAN) - Especially for non-English lyrics
    if metadata.get("language"):
        # Convert language name to ISO 639-2 code if needed
        lang_code = metadata.get(
            "language_code", metadata.get("language", "eng")[:3].lower()
        )
        audio_mp3.tags.add(TLAN(encoding=3, text=lang_code))

    # Comment (COMM) - Internal notes / AI usage info
    # COMM frames were already deleted at the start, so just add the new one
    if metadata.get("comment"):
        audio_mp3.tags.add(
            COMM(encoding=3, lang="eng", desc="", text=metadata.get("comment"))
        )

    # Embed cover art
    if cover_path:
        cover_file = Path(cover_path)
        if cover_file.exists():
            mime_type = (
                "image/jpeg"
                if cover_path.lower().endswith((".jpg", ".jpeg"))
                else "image/png"
            )
            with open(cover_file, "rb") as albumart:
                audio_mp3.tags.add(
                    APIC(
                        encoding=3,  # UTF-8
                        mime=mime_type,
                        type=3,  # Front cover
                        desc="Cover",
                        data=albumart.read(),
                    )
                )
        else:
            print_warning(f"Cover art file not found: {cover_path}")

    # Save all tags (EasyID3 + cover art + comment)
    audio_mp3.save()
    print_success(f"ID3v2 tags applied successfully: {audio_file.name}")
    return str(audio_file)


def batch_tag_files(source_dir, dest_dir, cover_path, metadata_template):
    """Tag multiple MP3 files in batch."""
    source = Path(source_dir)
    dest = Path(dest_dir)

    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    dest.mkdir(parents=True, exist_ok=True)

    mp3_files = list(source.glob("*.mp3"))

    from rich_utils import print_warning, print_success
    
    if not mp3_files:
        print_warning(f"No MP3 files found in {source_dir}")
        return

    for i, mp3_file in enumerate(mp3_files, 1):
        # Create metadata for this file
        metadata = metadata_template.copy()
        metadata["tracknumber"] = str(i)

        # Copy file to destination
        dest_file = dest / mp3_file.name
        shutil.copy2(mp3_file, dest_file)

        # Tag the copied file
        tag_audio_file(str(dest_file), cover_path, metadata)

    print_success(f"Tagged {len(mp3_files)} files")


if __name__ == "__main__":
    # Usage Example
    metadata = {
        "title": "Deep Dive",
        "artist": "YourArtistName",
        "album": "Summer Vibes EP",
        "genre": "Deep House",
        "year": "2025",
        "tracknumber": "1",
        "composer": "YourArtistName + Suno AI",
        "publisher": "Independent",
        "comment": "AI-generated with Suno, v3.5.2, Build abc123xyz",
    }

    tag_audio_file("YourArtistName - Deep Dive.mp3", "cover.jpg", metadata)
