# Usage Guide - How to Use This Tool

## What Is This?

This is a **Command-Line Tool (CLI)** - you run it from your terminal/command prompt. It's **NOT** a GUI app with buttons.

## Main Entry Point

**The main file is:** `pack.py` (Python) or `pack.js` (JavaScript)

This is the **simplest way** to use the tool.

## How to Use It

### Step 1: Install

```bash
pip install -r requirements.txt
```

### Step 2: Create Config File

```bash
# Copy the example
cp release.example.json release.json

# Edit release.json with your track details
# (Use any text editor)
```

### Step 3: Run

```bash
python pack.py release.json
```

**That's it!** The tool does everything automatically.

## What It Does

When you run `python pack.py release.json`, it:

1. ✅ Validates your configuration (required fields, types, values)
2. ✅ Checks dependencies (mutagen, Pillow) - fails fast if missing
3. ✅ Acquires workflow lock (prevents concurrent execution)
4. ✅ Checks disk space (requires minimum 500MB)
5. ✅ Sanitizes filenames (removes invalid filesystem characters)
6. ✅ Extracts Suno version info
7. ✅ Renames your audio files properly (with overwrite protection)
8. ✅ Organizes stems (if you have them, with multiple match warnings)
9. ✅ Tags files with ID3v2 metadata
10. ✅ Embeds cover art
11. ✅ Validates everything (cover art, audio formats: WAV, MP3, FLAC, M4A)
12. ✅ Creates metadata JSON files
13. ✅ Releases workflow lock

**Output:** Ready-to-upload files in `Releases/YourTrack/`

## Command Reference

```bash
# Main command - run the workflow
python pack.py release.json

# Show help
python pack.py --help

# Show example config
python pack.py --example
```

## Example Session

```bash
# 1. Install dependencies
$ pip install -r requirements.txt
Collecting mutagen...
Successfully installed mutagen-1.47.0 Pillow-10.0.0

# 2. Create config
$ cp release.example.json release.json
$ nano release.json  # Edit with your details

# 3. Run the tool
$ python pack.py release.json
📋 Loading config: release.json

🚀 Starting DistroKid Release Packer Workflow

📋 Step 1: Extracting Suno version info...
✓ Version: v3.5.2, Build: abc123xyz

📁 Step 2: Renaming and organizing audio files...
✓ Renamed: YourArtistName - Deep Dive .mp3

🏷️  Step 5: Tagging audio files with ID3v2...
✓ ID3v2 tags applied successfully: YourArtistName - Deep Dive .mp3

✅ Step 7: Running full compliance check...
✓ ALL CHECKS PASSED - Ready for upload!

🎉 Workflow completed successfully!
📦 Release files ready in: ./Releases/DeepDive

✅ Success! Your release is ready for DistroKid upload.
```

## File Structure After Running

```
Releases/
└── DeepDive/
    ├── Audio/
    │   └── YourArtistName - Deep Dive .mp3  ← Ready to upload
    ├── Cover/
    │   └── YourArtistName - Deep Dive - Cover.jpg   ← Validated
    ├── Stems/ (optional)
    │   ├── YourArtistName - Deep Dive - Vocals.wav
    │   └── YourArtistName - Deep Dive - Drums.wav
    └── Metadata/
        └── YourArtistName - Deep Dive - Metadata.json
```

## Alternative: Individual Scripts

You can also run scripts individually:

```bash
# Just rename files
python scripts/rename_audio_files.py

# Just tag files  
python scripts/tag_audio_id3.py

# Just validate
python scripts/validate_compliance.py
```

But `pack.py` is easier - it does everything at once.

## Troubleshooting

### "Config file not found"
- Make sure you created `release.json` from `release.example.json`
- Check the file path is correct

### "Module not found"
- Run: `pip install -r requirements.txt`

### "File not found" errors
- Check that your source directories exist
- Verify paths in release.json are correct

## More Information

- **How It Works:** [HOW_IT_WORKS.md](HOW_IT_WORKS.md) - Detailed explanation
- **Quick Start:** [QUICK_START.md](QUICK_START.md) - 5-minute guide
- **Scripts:** [scripts/README.md](scripts/README.md) - Individual script docs

