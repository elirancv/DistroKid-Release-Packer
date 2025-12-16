# Quick Setup Instructions

## ✅ Step 1: Dependencies Installed
- ✓ mutagen (for audio tagging)
- ✓ Pillow (for cover art validation)

## ✅ Step 2: Config File Created
- ✓ `config.json` created from `config.example.json`

## 📝 Step 3: Edit Your Config

Open `config.json` and update these **required** fields:

```json
{
  "artist": "YourArtistName",        ← Your artist name
  "title": "Your Track Title",     ← Your track title
  "source_audio_dir": "./exports", ← Where your MP3/WAV file is
  ...
}
```

**Minimum required fields:**
- `artist` - Your artist name
- `title` - Your track title
- `source_audio_dir` - Path to your audio file (default: `./exports`)

## 📁 Step 4: Place Your Audio File

Put your MP3 or WAV file in the `exports/` directory:

```
exports/
└── your_track.mp3  ← Put your file here
```

**File naming:** You can use any filename - the tool will rename it automatically.

## 🚀 Step 5: Run the Tool

```bash
python pack.py config.json
```

## 📋 What Gets Processed

The tool will:
1. ✅ Validate your configuration
2. ✅ Rename your audio file to: `Artist - Title.mp3`
3. ✅ Apply ID3v2 metadata tags
4. ✅ Validate cover art (if provided)
5. ✅ Run compliance checks
6. ✅ Generate metadata JSON

## 📦 Output Location

Processed files will be in:
```
Releases/YourTrack/
├── Audio/
│   └── YourArtistName - Your Track Title.mp3
├── Metadata/
│   └── YourArtistName - Your Track Title - Metadata.json
└── ...
```

## ⚠️ Common Issues

**"File not found" error:**
- Make sure your audio file is in `exports/` directory
- Check `source_audio_dir` path in config.json

**"Cover art not found" warning:**
- This is OK if you don't have cover art yet
- Place cover art in `Releases/YourTrack/Cover/` manually if needed

**"Missing required field" error:**
- Make sure `artist` and `title` are filled in config.json

## 🎯 Next Steps After Running

1. Check `Releases/YourTrack/` for processed files
2. Review the metadata JSON file
3. Upload to DistroKid!

