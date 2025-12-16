# Quick Setup for Your File

## Your File
- **Filename**: `YourArtistName - Thank You Lord (Nicolas Jaar RMX).mp3`

## Steps to Process

### 1. Move Your File to exports/

Copy or move your MP3 file to the `exports/` directory:

```bash
# If your file is in Downloads or Desktop:
copy "YourArtistName - Thank You Lord (Nicolas Jaar RMX).mp3" exports\
```

Or manually:
- Copy the file
- Paste it into the `exports/` folder

### 2. Config is Already Updated ✅

I've updated your `config.json` with:
- **Title**: "Thank You Lord (Nicolas Jaar RMX)"
- **Release directory**: `./Releases/ThankYouLordNicolasJaarRMX`

### 3. Run the Tool

```bash
python pack.py config.json
```

## What Will Happen

1. ✅ Tool finds your MP3 in `exports/`
2. ✅ Copies it to: `Releases/ThankYouLordNicolasJaarRMX/Audio/YourArtistName - Thank You Lord (Nicolas Jaar RMX).mp3`
3. ✅ Applies ID3v2 metadata tags
4. ✅ Creates metadata JSON file
5. ⚠️ Cover art warning (optional - you can add it later)

## After Running

Your processed files will be in:
```
Releases/ThankYouLordNicolasJaarRMX/
├── Audio/
│   └── YourArtistName - Thank You Lord (Nicolas Jaar RMX).mp3
└── Metadata/
    └── YourArtistName - Thank You Lord (Nicolas Jaar RMX) - Metadata.json
```

## Optional: Add Cover Art Later

If you want to add cover art:
1. Create: `Releases/ThankYouLordNicolasJaarRMX/Cover/`
2. Place: `YourArtistName - Thank You Lord (Nicolas Jaar RMX) - Cover.jpg`
3. Run the tool again to validate it

