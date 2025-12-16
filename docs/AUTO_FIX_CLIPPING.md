# Auto-Fix Clipping with FFmpeg

The tool can automatically fix audio clipping using FFmpeg.

## Quick Start

1. **Enable auto-fix in `release.json`:**
   ```json
   {
     "auto_fix_clipping": true
   }
   ```

2. **Run the workflow:**
   ```bash
   python pack.py release.json
   ```

   If clipping is detected, the tool will automatically:
   - Normalize the audio to -1 dB (safe level)
   - Overwrite the original file
   - Re-run compliance checks

## Manual Fix (Standalone Script)

You can also fix clipping manually:

```bash
# Fix in place (overwrites original)
python scripts/fix_clipping.py "exports/your-track.mp3"

# Fix to new file
python scripts/fix_clipping.py "exports/your-track.mp3" "exports/your-track-fixed.mp3"

# Custom target level (default: -1 dB)
python scripts/fix_clipping.py "exports/your-track.mp3" "exports/your-track-fixed.mp3" -2.0
```

## How It Works

- Uses FFmpeg's `volume` filter to normalize audio
- Default target: **-1 dB** (safe headroom for DistroKid)
- Preserves original format and quality
- Overwrites original file when auto-fix is enabled

## Requirements

- **FFmpeg** must be installed and in your PATH
- Check installation: `ffmpeg -version`

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `auto_fix_clipping` | `false` | Automatically fix clipping when detected |
| Target dB | `-1.0` | Safe level for DistroKid (hardcoded) |

## Notes

- Auto-fix only runs if clipping is detected (max amplitude ≥ 0.99)
- Original file is backed up during processing (temp file)
- If FFmpeg fails, the workflow continues with a warning
- Manual fix script can be used independently

