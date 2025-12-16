# User Settings Guide

## Overview

The **User Settings** feature lets you set default values (like your artist name) in **one central place** instead of repeating them in every release config file.

## Quick Setup

### Step 1: Create Your User Settings File

```bash
# Copy the example file
cp user_settings.example.json user_settings.json
```

### Step 2: Edit `user_settings.json`

Open `user_settings.json` and set your defaults:

```json
{
  "default_artist": "YourArtistName",
  "default_publisher": "Independent",
  "default_composer_template": "{artist} + Suno AI",
  "default_track_number": "1",
  "default_total_tracks": "1"
}
```

**That's it!** Now all your releases will use your default artist name automatically.

## How It Works

### Priority Order

1. **User Settings** (`user_settings.json`) - Your defaults
2. **Release Config** (`config.json`) - Overrides defaults

### Example

**`user_settings.json`:**
```json
{
  "default_artist": "YourArtistName",
  "default_publisher": "Independent"
}
```

**`config.json` (Release 1):**
```json
{
  "title": "Deep Dive"
  // No "artist" specified → uses default from user_settings.json
}
```

**`config.json` (Release 2 - Different Artist):**
```json
{
  "title": "Collab Track",
  "artist": "YourArtistName & Friend"  // Overrides default
}
```

## Available Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `default_artist` | Default artist name for all releases | `"YourArtistName"` |
| `default_publisher` | Default publisher (used in ID3 tags) | `"Independent"` |
| `default_composer_template` | Template for composer field | `"{artist} + Suno AI"` |
| `default_track_number` | Default track number (for singles) | `"1"` |
| `default_total_tracks` | Default total tracks (for multi-track) | `"1"` (single) or `"5"` (EP) |

## Benefits

✅ **Set once, use everywhere** - No need to type your artist name in every config  
✅ **Easy to change** - Update one file to change all defaults  
✅ **Override when needed** - Still can specify different values per release  
✅ **Consistent** - Ensures all releases use the same defaults unless overridden  

## Override Per Release

You can always override defaults in your `config.json`:

```json
{
  "artist": "Different Artist Name",  // Overrides default_artist
  "title": "My Track",
  "id3_metadata": {
    "publisher": "Different Publisher",  // Overrides default_publisher
    "tracknumber": "2/5"  // Overrides default track number
  }
}
```

## Track Number Format

**For Singles:**
- Set `default_track_number: "1"` and `default_total_tracks: "1"`
- Result: `tracknumber: "1"`

**For Multi-Track Releases (EPs/Albums):**
- Set `default_track_number: "1"` and `default_total_tracks: "5"`
- Result: `tracknumber: "1/5"` (track 1 of 5)
- Override per track in `config.json`: `"tracknumber": "2/5"` (track 2 of 5)

## Troubleshooting

**Q: My artist name isn't being used**  
A: Make sure `user_settings.json` exists and has `default_artist` set correctly.

**Q: Can I have different artists for different releases?**  
A: Yes! Just specify `"artist"` in each `config.json` to override the default.

**Q: What if I don't create `user_settings.json`?**  
A: The tool will work fine, but you'll need to specify `artist` in every `config.json`.

## File Location

- **Template:** `user_settings.example.json` (tracked in git)
- **Your Settings:** `user_settings.json` (gitignored, personal to you)

