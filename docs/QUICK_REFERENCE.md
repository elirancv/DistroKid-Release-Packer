# Quick Reference Guide - DistroKid Release Packer

**Your go-to cheat sheet for preparing releases in seconds.**

---

## 🚀 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy example config
cp config.example.json config.json

# 3. Edit config.json with your track details
# 4. Run!
python pack.py config.json
```

**That's it!** Your release is ready in `Releases/YourTrack/`

---

## 📋 Pre-Flight Checklist

Before running the tool, ensure you have:

- [ ] **Audio file** in `exports/` directory (MP3 or WAV)
- [ ] **Cover art** (optional) - place any `.jpg` or `.png` in `Releases/YourTrack/Cover/`
- [ ] **Config file** (`config.json`) with track details
- [ ] **FFmpeg installed** (for auto-fix clipping) - check with `ffmpeg -version`

---

## ⚙️ Essential Config Fields

**Minimum required fields in `config.json`:**

```json
{
  "artist": "YourArtistName",
  "title": "Your Track Title",
  "genre": "Deep House",
  "id3_metadata": {
    "album": "Your Album Name",
    "year": "2025",
    "tracknumber": "1/1"
  }
}
```

**Pro tip:** Set defaults in `user_settings.json` to avoid repeating artist name, publisher, etc.

---

## 🎯 Common Workflows

### Single Track Release

```json
{
  "artist": "Playdexmusic",
  "title": "My New Track",
  "genre": "Deep House",
  "bpm": 122,
  "id3_metadata": {
    "album": "My New Track",
    "year": "2025",
    "tracknumber": "1/1"
  },
  "auto_fix_clipping": true,
  "overwrite_existing": true
}
```

### Multi-Track EP/Album

```json
{
  "artist": "Playdexmusic",
  "title": "Track 1",
  "genre": "Deep House",
  "id3_metadata": {
    "album": "Summer Vibes EP",
    "year": "2025",
    "tracknumber": "1/5"  // Track 1 of 5
  }
}
```

**Repeat for each track** (Track 2 = "2/5", Track 3 = "3/5", etc.)

### With Stems

```json
{
  "organize_stems": true,
  "tag_stems": false,  // Optional: tag stem files
  "source_stems_dir": "./exports/stems"
}
```

Place stems in `exports/stems/` with naming: `Artist - Title - Vocals.wav`

---

## 🔧 Key Features

### Auto-Fix Clipping
```json
{
  "auto_fix_clipping": true
}
```
Automatically normalizes audio to -1 dB if clipping detected.

### Overwrite Existing Files
```json
{
  "overwrite_existing": true
}
```
Overwrites existing files in release directory (useful for re-runs).

### Strict Mode
```json
{
  "strict_mode": false  // Default: false
}
```
If `true`, workflow stops on any error. If `false`, continues with warnings.

### Debug Mode
```json
{
  "debug": true
}
```
Shows full tracebacks for troubleshooting.

---

## 📁 File Structure

```
Your Project/
├── exports/                    # Source audio files go here
│   ├── YourTrack.mp3
│   └── stems/                  # Optional: stems go here
│       ├── Vocals.wav
│       └── Drums.wav
├── Releases/                   # Output directory
│   └── YourTrack/
│       ├── Audio/              # Tagged audio files
│       ├── Stems/              # Organized stems
│       ├── Cover/              # Cover art (auto-renamed)
│       └── Metadata/           # Release metadata JSON
├── config.json                  # Your release config
├── user_settings.json           # Default settings (optional)
└── pack.py                     # Main entry point
```

---

## 🎨 Cover Art Setup

**Option 1: Auto-rename (Recommended)**
- Place any `.jpg` or `.png` file in `Releases/YourTrack/Cover/`
- Tool automatically renames to: `Artist - Title - Cover.jpg/png`

**Option 2: Manual naming**
- Name file exactly: `Artist - Title - Cover.jpg` or `.png`
- Place in `Releases/YourTrack/Cover/`

**Requirements:**
- Format: JPG or PNG
- Size: 3000×3000 pixels (recommended)
- File size: < 10 MB
- No text/watermarks

---

## 🏷️ ID3 Tagging Standards

**Required Tags (Auto-filled):**
- Title (TIT2)
- Artist (TPE1)
- Album (TALB)
- Genre (TCON)
- Year (TYER)
- Track Number (TRCK)
- Cover Art (APIC)

**Strongly Recommended (Auto-filled if available):**
- Album Artist (TPE2)
- Composer (TCOM)
- Publisher (TPUB)
- Copyright (TCOP)
- BPM (TBPM)
- ISRC (TSRC)
- Language (TLAN)

**Optional:**
- Comment (COMM) - Auto-generated: "AI-generated with Suno v5"
- Encoder (TSSE) - Not added by default (optional metadata)

---

## ⚡ Quick Commands

```bash
# Run workflow
python pack.py config.json

# Show help
python pack.py --help

# Show example config
python pack.py --example

# Fix clipping manually
python scripts/fix_clipping.py "exports/track.mp3"

# Check tags
python scripts/check_tags.py
```

---

## 🐛 Troubleshooting

### "File already exists"
**Solution:** Set `"overwrite_existing": true` in `config.json`

### "Audio clipping detected"
**Solution:** Set `"auto_fix_clipping": true` in `config.json` (requires FFmpeg)

### "Cover art not found"
**Solution:** Place any `.jpg` or `.png` in `Releases/YourTrack/Cover/` - it will be auto-renamed

### "Config file not found"
**Solution:** Copy `config.example.json` to `config.json` and edit it

### "mutagen not installed"
**Solution:** Run `pip install -r requirements.txt`

### "ffmpeg not found"
**Solution:** Install FFmpeg:
- Windows: Download from https://ffmpeg.org/download.html
- Or: `choco install ffmpeg`
- Or: `winget install ffmpeg`

### Duplicate comments in metadata
**Solution:** Re-run workflow with `"overwrite_existing": true` - the tool now properly removes old comments

---

## 💡 Pro Tips

1. **Use `user_settings.json`** for default artist, publisher, composer template
2. **Enable `auto_fix_clipping`** to automatically fix audio issues
3. **Set `overwrite_existing: true`** when re-running for the same track
4. **Check compliance** before uploading - the tool validates everything
5. **Keep stems organized** - use consistent naming: `Artist - Title - StemName.wav`

---

## 📊 Workflow Steps

The tool runs these steps automatically:

1. **Extract Suno version** (if URL provided)
2. **Rename audio files** (standardized naming)
3. **Organize stems** (if enabled)
4. **Tag stems** (if enabled)
5. **Tag audio files** (ID3v2 + cover art)
6. **Validate cover art** (dimensions, size)
7. **Compliance check** (audio format, clipping, metadata)
8. **Save metadata** (JSON file for records)

**Progress:** Shows "Step X/Y" for each operation.

---

## ✅ Pre-Upload Checklist

Before uploading to DistroKid, verify:

- [ ] Audio file exists in `Releases/YourTrack/Audio/`
- [ ] Cover art validated (if provided)
- [ ] Compliance check passed (✅ ALL CHECKS PASSED)
- [ ] Metadata JSON generated
- [ ] No errors in final summary

**If compliance check fails:**
- Review error messages
- Fix issues (clipping, file format, etc.)
- Re-run workflow
- Or set `"strict_mode": false` to continue anyway (not recommended)

---

## 🎵 Example: Complete Workflow

```bash
# 1. Place your audio file
cp "MyTrack.mp3" exports/

# 2. Create/update config.json
{
  "artist": "Playdexmusic",
  "title": "My New Track",
  "genre": "Deep House",
  "bpm": 122,
  "suno_url": "https://suno.com/song/abc123?v=5",
  "id3_metadata": {
    "album": "My New Track",
    "year": "2025",
    "tracknumber": "1/1",
    "composer": "Playdexmusic + Suno AI"
  },
  "auto_fix_clipping": true,
  "overwrite_existing": true
}

# 3. Place cover art (optional)
cp "cover.jpg" "Releases/MyNewTrack/Cover/"

# 4. Run workflow
python pack.py config.json

# 5. Upload to DistroKid
# Files ready in: Releases/MyNewTrack/Audio/
```

---

## 📚 Additional Resources

- **Full Documentation:** `docs/HOW_IT_WORKS.md`
- **Setup Guide:** `docs/QUICK_START.md`
- **ID3 Standards:** `docs/ID3_TAGGING_STANDARDS.md`
- **Cover Art Guide:** `docs/COVER_ART_GUIDE.md`
- **Clipping Guide:** `docs/AUDIO_CLIPPING_GUIDE.md`
- **User Settings:** `docs/USER_SETTINGS_GUIDE.md`

---

## 🆘 Need Help?

1. **Check error messages** - they're usually self-explanatory
2. **Enable debug mode** - add `"debug": true` to config.json
3. **Review logs** - workflow shows detailed progress
4. **Check documentation** - see `docs/` directory

---

**Last Updated:** 2025  
**Version:** 1.0  
**Status:** Production Ready ✅

