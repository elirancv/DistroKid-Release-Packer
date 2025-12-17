# Script Refactoring Summary

All scripts have been extracted from `DistroKid Release Packer.md` and refactored to comply with the project's coding standards.

## Key Changes Applied

### 1. File Structure & Imports

**Before:**
```python
import os
import shutil
from pathlib import Path
```

**After:**
```python
import shutil
from pathlib import Path
```
- Standard library imports first, then third-party
- Removed unused `os` import where `pathlib` is sufficient

### 2. Error Handling

**Before:**
```python
def extract_from_metadata_file(metadata_path):
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            return {...}
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return None
```

**After:**
```python
def extract_from_metadata_file(metadata_path):
    metadata_file = Path(metadata_path)
    
    if not metadata_file.exists():
        print(f"✗ Metadata file not found: {metadata_path}")
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            return {...}
    except Exception as e:
        print(f"✗ Error reading metadata: {e}")
        return None
```
- Added file existence checks before processing
- Used descriptive status messages with ✓/✗ symbols
- Used `pathlib.Path` instead of string paths

### 3. Input Validation

**Before:**
```python
def rename_audio_files(artist, title, source_dir, dest_dir):
    source = Path(source_dir)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
```

**After:**
```python
def rename_audio_files(artist, title, source_dir, dest_dir):
    source = Path(source_dir)
    dest = Path(dest_dir)
    
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    dest.mkdir(parents=True, exist_ok=True)
```
- Added validation for source directories
- Fail fast with descriptive error messages

### 4. JSON Writing

**Before:**
```python
with open(metadata_file, 'w') as f:
    json.dump(stems_data, f, indent=2)
```

**After:**
```python
metadata_file = stems_path / f"{artist} - {title} - Stems_Metadata.json"
with open(metadata_file, 'w') as f:
    json.dump(stems_data, f, indent=2)
print(f"✓ Generated metadata: {metadata_file}")
```
- Always use `indent=2` for JSON (already compliant)
- Added success messages with file names

### 5. Date/Time Format

**Before:**
```python
"export_date": datetime.now().isoformat()
```

**After:**
```python
"export_date": datetime.now().isoformat() + "Z"
```
- ISO format with Z suffix for UTC

### 6. Constants for Limits

**Before:**
```python
if file_size_mb > 500:
    errors.append(f"File too large: {file_size_mb:.2f}MB (max 500MB)")
```

**After:**
```python
MAX_AUDIO_SIZE_MB = 500
MAX_COVER_SIZE_MB = 5

if file_size_mb > MAX_AUDIO_SIZE_MB:
    errors.append(f"File too large: {file_size_mb:.2f}MB (max {MAX_AUDIO_SIZE_MB}MB)")
```
- Defined constants instead of hardcoded values

### 7. JavaScript Error Handling

**Before:**
```javascript
const data = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
```

**After:**
```javascript
if (!fs.existsSync(metadataPath)) {
  console.error(`✗ Metadata file not found: ${metadataPath}`);
  return null;
}

try {
  const data = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
  // ...
} catch (e) {
  console.error(`✗ Error reading metadata: ${e.message}`);
  return null;
}
```
- Added file existence checks
- Proper error handling with descriptive messages

### 8. Status Messages

**Before:**
```python
print("Done")
print("Error occurred")
```

**After:**
```python
print(f"✓ Tagged: {file_path.name}")
print(f"✗ Error tagging {file_path}: {e}")
print(f"⚠️  File size close to limit: {file_size_mb:.2f}MB")
```
- Used ✓ for success, ✗ for errors, ⚠️ for warnings
- Included file names in messages

### 9. Empty Directory Handling

**Before:**
```python
audio_files = list(source.glob("*.wav"))
for file in audio_files:
    # process
```

**After:**
```python
audio_files = list(source.glob("*.wav"))

if not audio_files:
    print(f"⚠️  No audio files found in {source_dir}")
    return

for file in audio_files:
    # process
```
- Handle empty directories gracefully

### 10. Module Exports (JavaScript)

**Before:**
```javascript
// No exports
```

**After:**
```javascript
module.exports = { functionName };
```
- Added proper module exports for reusability

## Files Created

1. `scripts/extract_suno_version.py` - Extract Suno version from URL/metadata
2. `scripts/extract_suno_version.js` - JavaScript version
3. `scripts/rename_audio_files.py` - Rename and organize audio files
4. `scripts/rename_audio_files.js` - JavaScript version
5. `scripts/organize_stems.py` - Organize stem files with metadata
6. `scripts/organize_stems.js` - JavaScript version
7. `scripts/tag_stems.py` - Tag stem files with ID3v2
8. `scripts/tag_stems.js` - JavaScript version
9. `scripts/tag_audio_id3.py` - Tag MP3 files with ID3v2 and cover art
10. `scripts/tag_audio_id3.js` - JavaScript version
11. `scripts/validate_cover_art.py` - Validate cover art compliance
12. `scripts/validate_compliance.py` - Full DistroKid compliance validator

## Compliance Checklist

✅ All scripts use `pathlib.Path` for file operations  
✅ All functions have descriptive docstrings  
✅ Input validation before processing  
✅ Structured error returns with `valid`, `errors`, `warnings`  
✅ Descriptive status messages with ✓/✗/⚠️  
✅ Constants defined for limits and requirements  
✅ ISO date format with Z suffix  
✅ JSON writing with `indent=2`  
✅ File existence checks before operations  
✅ Proper error handling with try/except  
✅ Module exports for JavaScript files  
✅ Empty directory handling  

