# Quick Start Guide

Get your Suno tracks ready for DistroKid in minutes.

## Installation

### Using Makefile (Easiest)

```bash
make setup
```

This will:
- Install Python dependencies
- Create release.json from example (if it doesn't exist)

### Manual Installation

**Python (Recommended):**
```bash
pip install -r requirements.txt
```

**JavaScript/Node.js (Optional):**
```bash
npm install
```

## Quick Workflow

### Option 1: Using the Orchestrator (Recommended)

1. **Create a config file:**

Copy `release.example.json` to `release.json` and edit:

```json
{
  "artist": "Your Artist Name",
  "title": "Your Track Title",
  "suno_url": "https://suno.com/song/your-track-id",
  "genre": "Deep House",
  "id3_metadata": {
    "album": "Your Album Name",
    "year": "2025"
  }
}
```

2. **Run the tool:**

**Using Makefile (Easiest):**
```bash
make run
```

**Or directly:**
```bash
# Python (Recommended)
python pack.py release.json

# JavaScript
node pack.js release.json
```

**See all commands:**
```bash
make help
```

The orchestrator will:
- Validate your configuration (required fields, types, values)
- Check dependencies (mutagen, Pillow)
- Acquire workflow lock (prevent concurrent execution)
- Check disk space (minimum 500MB)
- Sanitize filenames (remove invalid characters)
- Extract Suno version info
- Rename and organize audio files (with overwrite protection)
- Organize stems (if enabled, with multiple match warnings)
- Tag audio files with ID3v2
- Validate cover art
- Run compliance checks (WAV, MP3, FLAC, M4A support)
- Generate metadata JSON

### Option 2: Manual Step-by-Step

1. **Extract Suno version:**
```bash
python scripts/extract_suno_version.py
```

2. **Rename audio files:**
```bash
python scripts/rename_audio_files.py
```

3. **Tag audio files:**
```bash
python scripts/tag_audio_id3.py
```

4. **Validate compliance:**
```bash
python scripts/validate_compliance.py
```

## File Structure

After running, your files will be organized like this:

```
Releases/YourTrack/
├── Audio/
│   └── Artist - Title.mp3
├── Stems/
│   ├── Artist - Title - Vocals.wav
│   ├── Artist - Title - Drums.wav
│   └── ...
├── Cover/
│   └── Artist - Title - Cover.jpg
├── Metadata/
│   └── Artist - Title - Metadata.json
└── Screenshots/
```

## Common Tasks

### Rename a single track

```python
from scripts.rename_audio_files import rename_audio_files

rename_audio_files(
    artist="Your Artist",
    title="Your Title",
    source_dir="./exports",
    dest_dir="./Releases/YourTitle/Audio"
)
```

### Tag a track with metadata

```python
from scripts.tag_audio_id3 import tag_audio_file

tag_audio_file(
    audio_path="Artist - Title.mp3",
    cover_path="cover.jpg",
    metadata={
        "title": "Title",
        "artist": "Artist",
        "album": "Album",
        "genre": "Genre",
        "year": "2025"
    }
)
```

### Validate before upload

```python
from scripts.validate_compliance import full_compliance_check

is_valid = full_compliance_check(
    audio_path="track.mp3",
    cover_path="cover.jpg",
    metadata={"title": "Title", "artist": "Artist", "genre": "Genre"}
)
```

## Troubleshooting

### "Module not found" errors

**Python:**
```bash
pip install -r requirements.txt
```

**JavaScript:**
```bash
npm install
```

### Files not found

- Check that source directories exist
- Verify file paths in release.json
- Ensure audio files are in the source directory

### Validation failures

- Check file sizes (audio <500MB, cover <5MB)
- Verify cover art is exactly 3000×3000 pixels
- Ensure metadata fields are within character limits
- Check that required fields (artist, title) are present in release.json
- Verify BPM is between 1-300 if specified
- Ensure track number format is "X/Total" if using multi-track releases

### Configuration errors

If you get validation errors:
- Check that `artist` and `title` fields are present and not empty
- Verify field types (bpm must be number, boolean fields must be true/false)
- Check for invalid characters in artist/title (they'll be sanitized automatically)
- Use `debug: true` in release.json for detailed error messages

### File overwrite errors

If you get "File already exists" errors:
- Set `overwrite_existing: true` in release.json to allow overwriting
- Or manually delete existing files in the release directory

### Debug mode

For detailed error information, add to release.json:
```json
{
  "debug": true
}
```

This will show full tracebacks for any errors, making troubleshooting easier.

## Next Steps

1. Review generated files in `Releases/` directory
2. Verify metadata in JSON files
3. Upload to DistroKid
4. Track analytics (see Section 8 in main documentation)

## See Also

- [Scripts Documentation](scripts/README.md)
- [Full Documentation](DistroKid%20Release%20Packer.md)
- [Cursor Rules](.cursor/rules/distrokid.cursorrules)

