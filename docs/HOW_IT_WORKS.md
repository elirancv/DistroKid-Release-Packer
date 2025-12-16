# How This Tool Works

## Overview

This is a **Command-Line Interface (CLI) tool** - you run it from your terminal/command prompt. It's not a GUI app, but a powerful automation script that processes your music files.

## Main Entry Point

**The main file is:** `scripts/orchestrator.py` (Python) or `scripts/orchestrator.js` (JavaScript)

This is the **orchestrator** - it runs the complete workflow automatically.

## How It Works

### 1. **It's a CLI Tool (Command-Line Interface)**

You run it from your terminal like this:

```bash
python scripts/orchestrator.py config.json
```

### 2. **Workflow Process**

```
┌─────────────────────────────────────────────────┐
│  You: Create config.json with track details     │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  You: Run orchestrator.py config.json          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Orchestrator runs these steps automatically:  │
│                                                  │
│  1. Validate configuration (required fields)    │
│  2. Check dependencies (mutagen, Pillow)        │
│  3. Acquire workflow lock (prevent conflicts)  │
│  4. Check disk space (minimum 500MB)            │
│  5. Sanitize filenames (remove invalid chars)   │
│  6. Extract Suno version info                   │
│  7. Rename audio files → "Artist - Title.mp3" │
│  8. Organize stems (if enabled)                  │
│  9. Tag audio files with ID3v2 metadata         │
│  10. Embed cover art into MP3                    │
│  11. Validate cover art (3000×3000, <5MB)        │
│  12. Run compliance checks                       │
│  13. Generate metadata JSON                      │
│  14. Release workflow lock                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│  Output: Ready-to-upload files in Releases/    │
│          - Properly named                       │
│          - Tagged with metadata                 │
│          - Validated for DistroKid              │
└─────────────────────────────────────────────────┘
```

### 3. **Input: Configuration File**

You create a `config.json` file that tells the tool:
- Artist name
- Track title
- Suno URL (to extract version info)
- Where your source files are
- What metadata to use

**Example config.json:**
```json
{
  "artist": "YourArtistName",
  "title": "Deep Dive",
  "suno_url": "https://suno.com/song/abc123xyz",
  "source_audio_dir": "./exports",
  "genre": "Deep House"
}
```

### 4. **Output: Organized Release Folder**

After running, you get:
```
Releases/DeepDive/
├── Audio/
│   └── YourArtistName - Deep Dive .mp3  ← Tagged, ready
├── Cover/
│   └── YourArtistName - Deep Dive - Cover.jpg  ← Validated
├── Stems/ (if enabled)
│   └── YourArtistName - Deep Dive - Vocals.wav
└── Metadata/
    └── YourArtistName - Deep Dive - Metadata.json
```

## Usage Examples

### Basic Usage (One Command)

```bash
# 1. Create config.json (copy from example)
cp config.example.json config.json
# Edit config.json with your details

# 2. Run the tool
python scripts/orchestrator.py config.json
```

### What Happens When You Run It

```
🚀 Starting DistroKid Release Packer Workflow

📋 Step 1: Extracting Suno version info...
✓ Version: v3.5.2, Build: abc123xyz

📁 Step 2: Renaming and organizing audio files...
✓ Renamed: YourArtistName - Deep Dive .mp3

🎵 Step 3: Organizing stems...
✓ Organized: YourArtistName - Deep Dive - Vocals.wav
✓ Organized: YourArtistName - Deep Dive - Drums.wav

🏷️  Step 5: Tagging audio files with ID3v2...
✓ ID3v2 tags applied successfully: YourArtistName - Deep Dive .mp3

🖼️  Step 6: Validating cover art...
✓ Cover art validation passed: cover.jpg

✅ Step 7: Running full compliance check...
✓ ALL CHECKS PASSED - Ready for upload!

💾 Step 8: Saving release metadata...
✓ Generated release metadata: Metadata/YourArtistName - Deep Dive - Metadata.json

🎉 Workflow completed successfully!
📦 Release files ready in: ./Releases/DeepDive
```

**Note:** The workflow now includes automatic validation, dependency checking, file locking, and disk space checks before processing begins. If any validation fails, you'll get clear error messages explaining what's wrong.

## Individual Scripts (Alternative)

You can also run scripts individually instead of using the orchestrator:

```bash
# Just rename files
python scripts/rename_audio_files.py

# Just tag files
python scripts/tag_audio_id3.py

# Just validate
python scripts/validate_compliance.py
```

But the orchestrator is easier - it does everything in one command.

## It's Not a GUI App

- ❌ No graphical interface
- ❌ No buttons to click
- ✅ Command-line only (terminal/command prompt)
- ✅ Fast and automated
- ✅ Can be scripted/batched

## Think of It Like...

- **Like a recipe** - You provide ingredients (config.json), it follows steps automatically
- **Like a factory** - Input raw files → Output organized, tagged, validated files
- **Like a checklist** - But automated, so you don't have to do each step manually

## Quick Start

1. **Install:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure:**
   ```bash
   cp config.example.json config.json
   # Edit config.json
   ```

3. **Run:**
   ```bash
   python scripts/orchestrator.py config.json
   ```

That's it! Your files are ready for DistroKid upload.

