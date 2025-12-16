# Cover Art Guide

## How Cover Art Works

The tool automatically finds and renames cover art files to match the release naming convention.

**Location:** `Releases/YourTrack/Cover/`

**Automatic Renaming:**
- Place **any** `.jpg`, `.jpeg`, or `.png` file in the `Cover/` directory
- The tool will automatically rename it to: `Artist - Title - Cover.jpg` (or `.png`)
- No need to manually rename files!

## How to Add Cover Art

### Simple Method (Recommended)

1. Create the Cover directory:
   ```bash
   mkdir Releases\YourTrack\Cover
   ```

2. Place **any** cover art file (any name, any format):
   ```
   Releases/YourTrack/Cover/cover.png
   Releases/YourTrack/Cover/my-artwork.jpg
   Releases/YourTrack/Cover/art.png
   ```

3. Run the tool:
   ```bash
   python pack.py release.json
   ```

4. The tool will automatically:
   - Find the image file
   - Rename it to: `YourArtistName - Your Title - Cover.jpg` (or `.png`)
   - Validate it meets DistroKid requirements

## Cover Art Requirements

- **Format**: JPG, JPEG, or PNG (any filename - tool renames automatically)
- **Size**: Exactly 3000×3000 pixels
- **File size**: Less than 5MB
- **Filename**: Automatically renamed to `Artist - Title - Cover.jpg` (or `.png`)

## How It Works

1. **Tool searches** `Releases/YourTrack/Cover/` for any image file
2. **Finds first** `.jpg`, `.jpeg`, or `.png` file (in that order)
3. **Renames** it to match release naming: `Artist - Title - Cover.{ext}`
4. **Validates** it meets DistroKid requirements

## Notes

- ✅ **Any filename works** - Just drop your cover art in `Cover/` directory
- ✅ **Auto-renaming** - Tool handles the naming automatically
- ✅ **Format detection** - Tool preserves original format (JPG/PNG)
- ⚠️ **Cover art is optional** - Tool works without it (just shows a warning)
- ⚠️ **Multiple images** - If multiple images found, first one is used
- 💡 **Skip validation** - Set `"validate_cover": false` in release.json to skip

