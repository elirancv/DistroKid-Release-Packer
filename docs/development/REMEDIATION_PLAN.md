# DistroKid Release Packer Production Readiness Remediation Plan

**Plan Version:** 1.0  
**Based On:** Production Review Report  
**Target State:** Production-ready with confidence  
**Estimated Effort:** 3-5 days (critical fixes) + 1-2 weeks (testing)

---

## Phase 0 — Safety & Ground Rules

### Preconditions

1. **Create feature branch:**
   ```bash
   git checkout -b fix/production-readiness
   ```

2. **Establish baseline:**
   - Document current behavior with manual test cases
   - Create `test_manual_baseline.md` listing:
     - Sample config files that currently work
     - Expected output file structure
     - Known working audio/cover art files

3. **Set up test infrastructure:**
   ```bash
   # Python
   pip install pytest pytest-cov
   
   # Create test directory structure
   mkdir -p tests/{unit,integration,fixtures}
   ```

4. **Guardrails:**
   - Never modify `config.example.json` without updating documentation
   - All fixes must maintain backward compatibility with existing valid configs
   - Each phase should be independently committable
   - Run manual smoke test after each phase

### Branching Strategy

- Work in `fix/production-readiness` branch
- Commit after each phase completion
- Tag commits: `fix/phase-1-complete`, `fix/phase-2-complete`, etc.
- Merge to main only after Phase 7 validation passes

### Test Baselines Required

Before starting, verify these scenarios work manually:
- [ ] Valid config with all required fields → successful workflow
- [ ] Missing `artist` field → currently fails silently (baseline for fix)
- [ ] Malformed JSON config → currently crashes (baseline for fix)
- [ ] Missing mutagen library → currently skips tagging (baseline for fix)

---

## Phase 1 — Must-Fix Structural & Correctness Issues

**Goal:** Eliminate critical bugs that cause invalid output or silent failures.

**Dependencies:** None. Can be done first.

**Risk Level:** Low (fixing bugs, not refactoring)

---

### Fix 1.1: Add Required Field Validation

**What to fix:** Orchestrator proceeds with `None` values for `artist`/`title`, creating invalid file paths.

**Why first:** Blocks all other fixes. Invalid paths break everything downstream.

**Files affected:**
- `scripts/orchestrator.py` (add validation function, call at start)
- `pack.py` (add validation before workflow execution)

**Implementation steps:**

1. **Add validation function to `scripts/orchestrator.py`:**

   Insert after `load_config()` function (around line 39):

   ```python
   def validate_config(config):
       """Validate required configuration fields and types."""
       errors = []
       warnings = []
       
       # Required fields
       required_fields = {
           "artist": str,
           "title": str
       }
       
       for field, expected_type in required_fields.items():
           if field not in config:
               errors.append(f"Missing required field: '{field}'")
           elif not isinstance(config[field], expected_type):
               errors.append(f"Field '{field}' must be {expected_type.__name__}, got {type(config[field]).__name__}")
           elif not config[field] or not str(config[field]).strip():
               errors.append(f"Field '{field}' cannot be empty")
       
       # Optional but recommended fields
       if "source_audio_dir" not in config:
           warnings.append("'source_audio_dir' not specified, using default: ./exports")
       
       # Validate paths if provided
       if "release_dir" in config and config["release_dir"]:
           release_path = Path(config["release_dir"])
           if release_path.is_absolute() and not release_path.parent.exists():
               warnings.append(f"Release directory parent does not exist: {release_path.parent}")
       
       if errors:
           raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
       
       if warnings:
           for warning in warnings:
               print(f"⚠️  {warning}")
       
       return True
   ```

2. **Call validation in `run_release_workflow()`:**

   Modify `run_release_workflow()` function, add as first line (after docstring, before line 65):

   ```python
   def run_release_workflow(config):
       """Run the complete release workflow."""
       validate_config(config)  # ADD THIS LINE
       
       print("🚀 Starting DistroKid Release Packer Workflow\n")
       # ... rest of function
   ```

3. **Update `pack.py` to catch validation errors:**

   In `main()` function, around line 107, modify exception handling:

   ```python
   except ValueError as e:
       print(f"\n✗ Configuration Error: {e}")
       print("\nTroubleshooting:")
       print("  - Check that config.json has 'artist' and 'title' fields")
       print("  - Verify fields are not empty")
       print("  - See config.example.json for reference")
       sys.exit(1)
   except Exception as e:
       # ... existing handling
   ```

4. **Update `scripts/orchestrator.js` similarly:**

   Add validation function and call it at start of `runReleaseWorkflow()`.

**Verification:**
```bash
# Test missing artist
python pack.py tests/fixtures/config_missing_artist.json
# Expected: Clear error message, exit code 1

# Test empty title
python pack.py tests/fixtures/config_empty_title.json
# Expected: Clear error message, exit code 1

# Test valid config
python pack.py tests/fixtures/config_valid.json
# Expected: Workflow proceeds normally
```

**Test files to create:**
- `tests/fixtures/config_missing_artist.json`
- `tests/fixtures/config_empty_title.json`
- `tests/fixtures/config_valid.json`

---

### Fix 1.2: Remove Duplicate Imports

**What to fix:** Duplicate `import sys` and `from pathlib import Path` in orchestrator.

**Why now:** Code quality issue, easy fix, prevents confusion.

**Files affected:**
- `scripts/orchestrator.py` (lines 13-15)

**Implementation steps:**

1. **Remove duplicate imports:**

   In `scripts/orchestrator.py`, delete lines 14-15:
   ```python
   # DELETE THESE LINES:
   import sys
   from pathlib import Path
   ```

   Keep only the imports at the top (lines 8-11).

**Verification:**
```bash
python -m py_compile scripts/orchestrator.py
# Should compile without errors

python scripts/orchestrator.py config.example.json
# Should run normally (if config is valid)
```

---

### Fix 1.3: Handle JSON Parsing Errors

**What to fix:** Malformed JSON configs cause unhandled `JSONDecodeError`.

**Why now:** Common user error, poor UX without proper handling.

**Files affected:**
- `scripts/orchestrator.py` (`load_config()` function)
- `pack.py` (error handling in `main()`)
- `scripts/orchestrator.js` (`loadConfig()` function)

**Implementation steps:**

1. **Update `load_config()` in `scripts/orchestrator.py`:**

   Replace function (lines 30-38) with:

   ```python
   def load_config(config_path):
       """Load configuration from JSON file."""
       config_file = Path(config_path)
       
       if not config_file.exists():
           raise FileNotFoundError(f"Config file not found: {config_path}")
       
       try:
           with open(config_file, 'r', encoding='utf-8') as f:
               return json.load(f)
       except json.JSONDecodeError as e:
           raise ValueError(
               f"Invalid JSON in config file '{config_path}':\n"
               f"  Error: {e.msg}\n"
               f"  Line {e.lineno}, column {e.colno}\n"
               f"  Fix the JSON syntax and try again."
           )
       except UnicodeDecodeError as e:
           raise ValueError(
               f"Config file '{config_path}' is not valid UTF-8 text.\n"
               f"  Error: {e}\n"
               f"  Ensure the file is saved as UTF-8."
           )
   ```

2. **Update `pack.py` error handling:**

   In `main()` function, add specific handler (around line 117):

   ```python
   except ValueError as e:
       # Handles both validation and JSON errors
       print(f"\n✗ Configuration Error: {e}")
       print("\nTroubleshooting:")
       print("  - Validate JSON syntax (use jsonlint.com or similar)")
       print("  - Check that all required fields are present")
       print("  - See config.example.json for reference")
       sys.exit(1)
   ```

3. **Update `scripts/orchestrator.js` similarly:**

   Wrap `JSON.parse()` in try-catch with clear error messages.

**Verification:**
```bash
# Test malformed JSON
echo '{"artist": "Test", "title": }' > tests/fixtures/config_malformed.json
python pack.py tests/fixtures/config_malformed.json
# Expected: Clear JSON error message with line/column, exit code 1

# Test invalid UTF-8 (if possible on system)
# Expected: Clear encoding error message
```

---

### Fix 1.4: Fail Fast on Missing Dependencies

**What to fix:** Missing `mutagen` or `Pillow` causes silent step skipping.

**Why now:** Critical workflow steps fail silently, user may upload invalid files.

**Files affected:**
- `scripts/orchestrator.py` (add dependency check at start)
- `scripts/tag_audio_id3.py` (change return None to raise exception)
- `scripts/validate_compliance.py` (check dependencies before use)
- `scripts/validate_cover_art.py` (check dependencies before use)

**Implementation steps:**

1. **Add dependency validation function to `scripts/orchestrator.py`:**

   Add after `validate_config()`:

   ```python
   def validate_dependencies():
       """Check that required dependencies are installed."""
       missing = []
       
       try:
           import mutagen
       except ImportError:
           missing.append("mutagen (required for ID3 tagging)")
       
       try:
           from PIL import Image
       except ImportError:
           missing.append("Pillow (required for cover art validation)")
       
       if missing:
           raise ImportError(
               "Missing required dependencies:\n" +
               "\n".join(f"  - {dep}" for dep in missing) +
               "\n\nInstall with: pip install -r requirements.txt"
           )
       
       return True
   ```

2. **Call at start of workflow:**

   In `run_release_workflow()`, after `validate_config(config)`:

   ```python
   validate_config(config)
   validate_dependencies()  # ADD THIS
   ```

3. **Update `tag_audio_file()` to raise instead of return None:**

   In `scripts/tag_audio_id3.py`, replace lines 16-18:

   ```python
   if not MUTAGEN_AVAILABLE:
       raise ImportError(
           "mutagen library required for tagging. "
           "Install with: pip install mutagen"
       )
   ```

4. **Update validation functions similarly:**

   In `scripts/validate_compliance.py` and `scripts/validate_cover_art.py`, 
   raise `ImportError` instead of returning error dict when dependencies missing.

**Verification:**
```bash
# Test with dependencies installed
python pack.py tests/fixtures/config_valid.json
# Expected: Normal execution

# Test with mutagen uninstalled (if possible)
pip uninstall mutagen -y
python pack.py tests/fixtures/config_valid.json
# Expected: Clear error about missing mutagen, exit before workflow starts
pip install mutagen  # Restore
```

---

### Fix 1.5: Prevent Accidental File Overwrites

**What to fix:** Files copied without checking if destination exists.

**Why now:** Data loss risk, user may lose previous releases.

**Files affected:**
- `scripts/rename_audio_files.py` (`rename_audio_files()` function)
- `scripts/organize_stems.py` (`organize_stems()` function)
- `scripts/orchestrator.py` (add `overwrite_existing` config option)

**Implementation steps:**

1. **Add overwrite protection to `rename_audio_files()`:**

   In `scripts/rename_audio_files.py`, modify the copy loop (around line 22):

   ```python
   for file in audio_files:
       if "final" in file.name.lower() or "master" in file.name.lower():
           new_name = f"{artist} - {title}{file.suffix}"
       else:
           new_name = f"{artist} - {title}{file.suffix}"
       
       dest_file = dest / new_name
       
       # Check for existing file
       if dest_file.exists():
           raise FileExistsError(
               f"File already exists: {dest_file}\n"
               f"  To overwrite, set 'overwrite_existing: true' in config.json"
           )
       
       shutil.copy2(file, dest_file)
       print(f"✓ Renamed: {new_name}")
   ```

2. **Add overwrite flag support:**

   Modify function signature:
   ```python
   def rename_audio_files(artist, title, source_dir, dest_dir, overwrite=False):
   ```

   Update check:
   ```python
   if dest_file.exists() and not overwrite:
       raise FileExistsError(...)
   ```

3. **Update orchestrator to pass flag:**

   In `scripts/orchestrator.py`, around line 85:

   ```python
   rename_audio_files(
       artist=artist,
       title=title,
       source_dir=config.get("source_audio_dir", "./exports"),
       dest_dir=release_dir / "Audio",
       overwrite=config.get("overwrite_existing", False)  # ADD THIS
   )
   ```

4. **Apply same pattern to `organize_stems()`:**

   Add overwrite parameter and check before copying.

5. **Update `config.example.json`:**

   Add comment:
   ```json
   "overwrite_existing": false,  // Set to true to overwrite existing files
   ```

**Verification:**
```bash
# Create existing file
mkdir -p Releases/Test/Audio
touch "Releases/Test/Audio/Artist - Title.mp3"

# Test without overwrite flag
python pack.py tests/fixtures/config_valid.json
# Expected: FileExistsError with clear message

# Test with overwrite flag
# Edit config to set overwrite_existing: true
python pack.py tests/fixtures/config_with_overwrite.json
# Expected: File overwritten with warning message
```

---

**Phase 1 Completion Checklist:**
- [ ] All 5 critical fixes implemented
- [ ] Manual verification tests pass
- [ ] No regressions in existing functionality
- [ ] Error messages are clear and actionable
- [ ] Commit with message: "fix: address critical production issues (phase 1)"

---

## Phase 2 — Architectural Consistency & Contract Alignment

**Goal:** Ensure code behavior matches documentation and enforces contracts.

**Dependencies:** Phase 1 complete (validation in place).

**Risk Level:** Low (adding validation, not changing behavior).

---

### Fix 2.1: Complete Audio Format Validation

**What to fix:** FLAC and M4A formats claimed but not fully validated.

**Why now:** Compliance validation gaps create false confidence.

**Files affected:**
- `scripts/validate_compliance.py` (`validate_audio_file()` function)

**Implementation steps:**

1. **Add FLAC/M4A support to validation:**

   In `scripts/validate_compliance.py`, update `validate_audio_file()` (around line 57):

   ```python
   try:
       if file_path.suffix.lower() == '.wav':
           with wave.open(str(audio_path), 'rb') as wav_file:
               frames = wav_file.getnframes()
               sample_rate = wav_file.getframerate()
               duration = frames / float(sample_rate)
       elif MUTAGEN_AVAILABLE:
           # Use mutagen for MP3, FLAC, M4A
           audio = MP3(audio_path) if file_path.suffix.lower() == '.mp3' else None
           if not audio:
               # Try as FLAC or M4A
               try:
                   from mutagen.flac import FLAC
                   from mutagen.mp4 import MP4
                   
                   if file_path.suffix.lower() == '.flac':
                       audio = FLAC(audio_path)
                   elif file_path.suffix.lower() == '.m4a':
                       audio = MP4(audio_path)
               except ImportError:
                   warnings.append("mutagen FLAC/MP4 support not available")
           
           if audio:
               duration = audio.info.length
               sample_rate = audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else None
           else:
               warnings.append(f"Could not read audio properties for {file_path.suffix}")
       else:
           warnings.append("Could not read audio properties (install mutagen)")
   ```

2. **Update requirements.txt:**

   Ensure mutagen version supports FLAC/MP4 (mutagen>=1.47.0 should work).

**Verification:**
```bash
# Test with FLAC file (if available)
python scripts/validate_compliance.py tests/fixtures/test.flac
# Expected: Duration and sample rate validated

# Test with M4A file (if available)
python scripts/validate_compliance.py tests/fixtures/test.m4a
# Expected: Duration validated
```

**Alternative:** If FLAC/M4A support is not needed, remove from `valid_formats` list and update documentation.

---

### Fix 2.2: Add Configuration Schema Validation

**What to fix:** No validation of config field types, enums, or constraints.

**Why now:** Prevents runtime type errors and invalid values.

**Files affected:**
- `scripts/orchestrator.py` (extend `validate_config()` function)

**Implementation steps:**

1. **Extend `validate_config()` with type and value validation:**

   Add after required field checks:

   ```python
   # Type validation for optional fields
   type_checks = {
       "bpm": int,
       "explicit": bool,
       "organize_stems": bool,
       "tag_stems": bool,
       "tag_audio": bool,
       "validate_cover": bool,
       "validate_compliance": bool,
       "strict_mode": bool,
       "overwrite_existing": bool
   }
   
   for field, expected_type in type_checks.items():
       if field in config and not isinstance(config[field], expected_type):
           errors.append(
               f"Field '{field}' must be {expected_type.__name__}, "
               f"got {type(config[field]).__name__}"
           )
   
   # Value range validation
   if "bpm" in config:
       bpm = config["bpm"]
       if not isinstance(bpm, int) or bpm < 1 or bpm > 300:
           errors.append(f"Field 'bpm' must be integer between 1-300, got {bpm}")
   
   # Path validation
   path_fields = ["source_audio_dir", "source_stems_dir", "release_dir"]
   for field in path_fields:
       if field in config and config[field]:
           path_val = Path(config[field])
           if field.startswith("source_") and not path_val.exists():
               warnings.append(f"Source directory does not exist: {config[field]}")
   ```

2. **Validate nested `id3_metadata` structure:**

   ```python
   if "id3_metadata" in config:
       if not isinstance(config["id3_metadata"], dict):
           errors.append("Field 'id3_metadata' must be an object")
       else:
           # Validate track number format if present
           if "tracknumber" in config["id3_metadata"]:
               tracknum = config["id3_metadata"]["tracknumber"]
               if isinstance(tracknum, str) and "/" in tracknum:
                   parts = tracknum.split("/")
                   if len(parts) != 2 or not all(p.isdigit() for p in parts):
                       errors.append(
                           f"Field 'id3_metadata.tracknumber' must be format 'X/Total', "
                           f"got '{tracknum}'"
                       )
   ```

**Verification:**
```bash
# Test invalid BPM
python pack.py tests/fixtures/config_invalid_bpm.json
# Expected: Validation error

# Test invalid track number format
python pack.py tests/fixtures/config_invalid_tracknum.json
# Expected: Validation error
```

---

### Fix 2.3: Standardize Error Handling Pattern

**What to fix:** Inconsistent patterns (return None vs raise exceptions).

**Why now:** Makes code predictable and easier to maintain.

**Files affected:**
- All scripts in `scripts/` directory

**Implementation steps:**

1. **Define error handling standard:**

   - **Functions that perform operations:** Raise exceptions on failure
   - **Functions that validate:** Return structured dict with `{"valid": bool, "errors": [], "warnings": []}`
   - **Never return `None` to indicate failure** (use exceptions)

2. **Update `tag_audio_file()`:**

   Already raises exceptions (good). Verify all call sites handle exceptions.

3. **Update `organize_stems()` duration reading:**

   In `scripts/organize_stems.py`, the duration reading already handles exceptions gracefully (line 49). This is acceptable.

4. **Document pattern in `scripts/README.md`:**

   Add section:
   ```markdown
   ## Error Handling Standards
   
   - Validation functions return: `{"valid": bool, "errors": [], "warnings": []}`
   - Operation functions raise exceptions on failure
   - Never return `None` to indicate failure
   ```

**Verification:**
- Review all functions in `scripts/` for consistency
- Ensure no functions return `None` on error
- Ensure orchestrator handles all exception types

---

**Phase 2 Completion Checklist:**
- [ ] Audio format validation complete or formats removed from docs
- [ ] Configuration schema validation implemented
- [ ] Error handling patterns documented and consistent
- [ ] Commit: "fix: improve validation and consistency (phase 2)"

---

## Phase 3 — Configuration, Feature Flags & Environment Safety

**Goal:** Make configuration safe, predictable, and environment-agnostic.

**Dependencies:** Phase 1 complete (validation framework in place).

**Risk Level:** Low (adding safety checks).

---

### Fix 3.1: Sanitize File Paths

**What to fix:** User input used directly in file paths without sanitization.

**Why now:** Security and filesystem compatibility risk.

**Files affected:**
- `scripts/orchestrator.py` (add sanitization function)
- All file path construction sites

**Implementation steps:**

1. **Add filename sanitization function:**

   In `scripts/orchestrator.py`, add after imports:

   ```python
   def sanitize_filename(name):
       """Remove invalid filesystem characters from filename."""
       if not name:
           return "Unknown"
       
       # Remove invalid characters for Windows/Unix
       invalid_chars = '<>:"/\\|?*'
       sanitized = name
       for char in invalid_chars:
           sanitized = sanitized.replace(char, '_')
       
       # Remove leading/trailing dots and spaces (Windows issue)
       sanitized = sanitized.strip('. ')
       
       # Limit length (filesystem limits + safety margin)
       max_length = 200
       if len(sanitized) > max_length:
           sanitized = sanitized[:max_length]
       
       # Ensure not empty after sanitization
       if not sanitized:
           sanitized = "Unknown"
       
       return sanitized
   ```

2. **Apply sanitization in workflow:**

   In `run_release_workflow()`, after validation:

   ```python
   validate_config(config)
   validate_dependencies()
   
   # Sanitize user input
   artist = sanitize_filename(config["artist"])
   title = sanitize_filename(config["title"])
   ```

3. **Update validation to warn about sanitization:**

   In `validate_config()`, add check:

   ```python
   # Check for invalid characters
   invalid_chars = '<>:"/\\|?*'
   for field in ["artist", "title"]:
       if field in config:
           value = str(config[field])
           found_invalid = [c for c in invalid_chars if c in value]
           if found_invalid:
               warnings.append(
                   f"Field '{field}' contains invalid characters: {found_invalid}. "
                   f"They will be replaced with '_'."
               )
   ```

**Verification:**
```bash
# Test with invalid characters
python pack.py tests/fixtures/config_invalid_chars.json
# Expected: Warning message, sanitized filenames created

# Test with very long names
python pack.py tests/fixtures/config_long_names.json
# Expected: Names truncated, files created
```

---

### Fix 3.2: Warn on Multiple File Matches

**What to fix:** `organize_stems()` silently uses first match when multiple files match pattern.

**Why now:** Data loss risk, confusing behavior.

**Files affected:**
- `scripts/organize_stems.py` (`organize_stems()` function)

**Implementation steps:**

1. **Add warning for multiple matches:**

   In `scripts/organize_stems.py`, modify matching logic (around line 31):

   ```python
   matching_files = list(source.glob(pattern))
   
   if matching_files:
       if len(matching_files) > 1:
           print(f"⚠️  Multiple files match '{stem_name}':")
           for f in matching_files:
               print(f"     - {f.name}")
           print(f"   Using: {matching_files[0].name}")
       
       file = matching_files[0]
       # ... rest of logic
   ```

**Verification:**
```bash
# Create multiple matching files
mkdir -p tests/fixtures/stems
touch tests/fixtures/stems/vocals1.wav
touch tests/fixtures/stems/vocals2.wav

# Test organization
python scripts/organize_stems.py
# Expected: Warning message listing both files
```

---

### Fix 3.3: Improve Error Context and Logging

**What to fix:** Exceptions caught with bare `except` lose stack traces.

**Why now:** Debugging difficulty in production.

**Files affected:**
- `scripts/orchestrator.py` (all exception handlers)

**Implementation steps:**

1. **Add debug mode support:**

   In `scripts/orchestrator.py`, add at start of `run_release_workflow()`:

   ```python
   debug_mode = config.get("debug", False)
   ```

2. **Update exception handlers:**

   Replace bare exception handlers (around line 92):

   ```python
   except Exception as e:
       error_msg = f"✗ Error renaming audio files: {e}"
       print(error_msg)
       
       if debug_mode:
           import traceback
           print("\nDebug traceback:")
           traceback.print_exc()
       else:
           print("   (Run with 'debug: true' in config for full traceback)")
       
       if config.get("strict_mode", False):
           return False
   ```

3. **Add structured error collection:**

   Optionally, collect errors and print summary at end:

   ```python
   workflow_errors = []
   
   # In each exception handler:
   workflow_errors.append({
       "step": "rename_audio",
       "error": str(e),
       "type": type(e).__name__
   })
   
   # At end of workflow:
   if workflow_errors:
       print(f"\n⚠️  Workflow completed with {len(workflow_errors)} error(s)")
   ```

**Verification:**
```bash
# Test with debug mode off
python pack.py tests/fixtures/config_valid.json
# Expected: Error message without traceback

# Test with debug mode on
# Edit config to set debug: true
python pack.py tests/fixtures/config_debug.json
# Expected: Full traceback printed
```

---

**Phase 3 Completion Checklist:**
- [ ] Filename sanitization implemented
- [ ] Multiple file match warnings added
- [ ] Error context improved with debug mode
- [ ] Commit: "fix: improve configuration safety and error handling (phase 3)"

---

## Phase 4 — Concurrency, Performance & Operational Hardening

**Goal:** Ensure system behaves correctly under real-world conditions.

**Dependencies:** Phases 1-3 complete.

**Risk Level:** Low (CLI tool, minimal concurrency concerns).

---

### Fix 4.1: Add File Locking Protection

**What to fix:** No protection against concurrent execution modifying same files.

**Why now:** Prevents corruption if user runs multiple instances.

**Files affected:**
- `scripts/orchestrator.py` (add lock file check)

**Implementation steps:**

1. **Add simple lock file mechanism:**

   In `scripts/orchestrator.py`, at start of `run_release_workflow()`:

   ```python
   def acquire_workflow_lock(release_dir):
       """Prevent concurrent workflow execution."""
       lock_file = Path(release_dir) / ".workflow.lock"
       
       if lock_file.exists():
           # Check if lock is stale (older than 1 hour)
           lock_age = time.time() - lock_file.stat().st_mtime
           if lock_age > 3600:
               print(f"⚠️  Removing stale lock file (age: {lock_age/60:.1f} minutes)")
               lock_file.unlink()
           else:
               raise RuntimeError(
                   f"Workflow already in progress for {release_dir}.\n"
                   f"  Lock file: {lock_file}\n"
                   f"  If no workflow is running, delete the lock file manually."
               )
       
       # Create lock file
       lock_file.parent.mkdir(parents=True, exist_ok=True)
       lock_file.write_text(f"PID: {os.getpid()}\nTime: {datetime.now().isoformat()}\n")
       return lock_file
   
   def release_workflow_lock(lock_file):
       """Release workflow lock."""
       if lock_file and lock_file.exists():
           lock_file.unlink()
   ```

2. **Use in workflow:**

   ```python
   lock_file = None
   try:
       lock_file = acquire_workflow_lock(release_dir)
       # ... workflow execution
   finally:
       release_workflow_lock(lock_file)
   ```

**Verification:**
```bash
# Start workflow in background
python pack.py config.json &

# Try to start another
python pack.py config.json
# Expected: Error about lock file

# Wait for first to complete, try again
# Expected: Normal execution
```

---

### Fix 4.2: Add Disk Space Check

**What to fix:** No check for available disk space before file operations.

**Why now:** Prevents partial failures and unclear errors.

**Files affected:**
- `scripts/orchestrator.py` (add space check)

**Implementation steps:**

1. **Add disk space check function:**

   ```python
   def check_disk_space(path, required_mb=100):
       """Check if sufficient disk space is available."""
       import shutil
       
       stat = shutil.disk_usage(path)
       free_mb = stat.free / (1024 * 1024)
       
       if free_mb < required_mb:
           raise RuntimeError(
               f"Insufficient disk space: {free_mb:.1f}MB free, "
               f"need at least {required_mb}MB"
           )
       
       return True
   ```

2. **Call before file operations:**

   In `run_release_workflow()`, after validation:

   ```python
   check_disk_space(release_dir, required_mb=500)  # Conservative estimate
   ```

**Verification:**
- Test on system with low disk space (if possible)
- Expected: Clear error before workflow starts

---

**Phase 4 Completion Checklist:**
- [ ] File locking implemented
- [ ] Disk space check added
- [ ] Commit: "fix: add operational safeguards (phase 4)"

---

## Phase 5 — Test Coverage & Verification Gaps

**Goal:** Transform confidence from assumed to proven.

**Dependencies:** Phases 1-4 complete (code is stable).

**Risk Level:** Medium (adding tests, must not break existing behavior).

---

### Test 5.1: Unit Tests for Validation Functions

**What to test:** All validation logic.

**Files to create:**
- `tests/unit/test_config_validation.py`
- `tests/unit/test_audio_validation.py`
- `tests/unit/test_cover_validation.py`

**Implementation steps:**

1. **Create `tests/unit/test_config_validation.py`:**

   ```python
   import pytest
   from scripts.orchestrator import validate_config
   
   def test_validate_config_missing_required():
       config = {"title": "Test"}
       with pytest.raises(ValueError, match="Missing required field: 'artist'"):
           validate_config(config)
   
   def test_validate_config_empty_artist():
       config = {"artist": "", "title": "Test"}
       with pytest.raises(ValueError, match="cannot be empty"):
           validate_config(config)
   
   def test_validate_config_invalid_bpm():
       config = {"artist": "Test", "title": "Test", "bpm": "not a number"}
       with pytest.raises(ValueError, match="must be int"):
           validate_config(config)
   
   def test_validate_config_valid():
       config = {"artist": "Test", "title": "Test"}
       assert validate_config(config) is True
   ```

2. **Create similar tests for audio and cover validation.**

3. **Run tests:**

   ```bash
   pytest tests/unit/ -v
   ```

**Coverage target:** 80%+ for validation functions.

---

### Test 5.2: Integration Test for Full Workflow

**What to test:** End-to-end workflow execution.

**Files to create:**
- `tests/integration/test_full_workflow.py`
- `tests/fixtures/sample_audio.mp3` (small test file)
- `tests/fixtures/sample_cover.jpg` (3000x3000 test image)

**Implementation steps:**

1. **Create integration test:**

   ```python
   import pytest
   import tempfile
   import shutil
   from pathlib import Path
   from scripts.orchestrator import run_release_workflow
   
   @pytest.fixture
   def temp_release_dir():
       """Create temporary directory for test releases."""
       temp_dir = tempfile.mkdtemp()
       yield Path(temp_dir)
       shutil.rmtree(temp_dir)
   
   def test_full_workflow_success(temp_release_dir):
       """Test complete workflow with valid inputs."""
       config = {
           "artist": "Test Artist",
           "title": "Test Track",
           "release_dir": str(temp_release_dir),
           "source_audio_dir": "tests/fixtures",
           "tag_audio": False,  # Skip tagging for speed
           "validate_cover": False,
           "validate_compliance": False
       }
       
       result = run_release_workflow(config)
       assert result is True
       
       # Verify output structure
       assert (temp_release_dir / "Audio").exists()
       assert (temp_release_dir / "Metadata").exists()
   ```

2. **Add test for error paths:**

   ```python
   def test_workflow_missing_source_files(temp_release_dir):
       """Test workflow handles missing source files gracefully."""
       config = {
           "artist": "Test",
           "title": "Test",
           "release_dir": str(temp_release_dir),
           "source_audio_dir": "/nonexistent/path"
       }
       
       # Should not crash, but return False or raise clear error
       with pytest.raises(FileNotFoundError):
           run_release_workflow(config)
   ```

**Coverage target:** All happy paths and critical error paths.

---

### Test 5.3: Test Error Handling Paths

**What to test:** All exception handlers and error recovery.

**Files to create:**
- `tests/unit/test_error_handling.py`

**Implementation steps:**

1. **Test JSON parsing errors:**
   ```python
   def test_load_config_malformed_json(tmp_path):
       config_file = tmp_path / "bad.json"
       config_file.write_text('{"invalid": json}')
       
       with pytest.raises(ValueError, match="Invalid JSON"):
           load_config(str(config_file))
   ```

2. **Test missing dependencies:**
   ```python
   @pytest.mark.skipif(has_mutagen, reason="mutagen installed")
   def test_workflow_missing_mutagen():
       # Test that workflow fails fast with clear error
   ```

---

### Test 5.4: Add CI/CD Pipeline

**What to add:** Automated test execution on commits.

**Files to create:**
- `.github/workflows/test.yml` (if using GitHub)

**Implementation steps:**

1. **Create GitHub Actions workflow:**

   ```yaml
   name: Tests
   
   on: [push, pull_request]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-python@v4
           with:
             python-version: '3.8'
         - run: pip install -r requirements.txt
         - run: pip install pytest pytest-cov
         - run: pytest tests/ -v --cov=scripts --cov-report=term
   ```

2. **Add to Makefile:**

   ```makefile
   test: ## Run tests
   	pytest tests/ -v
   
   test-cov: ## Run tests with coverage
   	pytest tests/ -v --cov=scripts --cov-report=html
   ```

---

**Phase 5 Completion Checklist:**
- [ ] Unit tests for all validation functions
- [ ] Integration test for full workflow
- [ ] Error handling tests
- [ ] CI/CD pipeline configured
- [ ] Test coverage > 70%
- [ ] Commit: "test: add comprehensive test coverage (phase 5)"

---

## Phase 6 — Cleanup, Polish & Professionalism

**Goal:** Improve code quality, remove cruft, enhance maintainability.

**Dependencies:** All previous phases complete.

**Risk Level:** Very Low (cleanup only).

---

### Fix 6.1: Remove Dead Code and Comments

**What to clean:** Unused imports, commented code, outdated comments.

**Files to review:**
- All Python files in `scripts/`
- All JavaScript files in `scripts/`

**Implementation steps:**

1. **Run linter:**

   ```bash
   # Python
   pip install flake8
   flake8 scripts/*.py
   
   # Fix reported issues
   ```

2. **Remove unused imports:**
   - Check each file for unused imports
   - Remove or use them

3. **Update docstrings:**
   - Ensure all functions have docstrings
   - Update outdated parameter descriptions

---

### Fix 6.2: Standardize Code Formatting

**What to format:** Inconsistent spacing, line lengths, etc.

**Implementation steps:**

1. **Install formatter:**

   ```bash
   pip install black
   ```

2. **Format all Python files:**

   ```bash
   black scripts/*.py pack.py
   ```

3. **Add to Makefile:**

   ```makefile
   format: ## Format code
   	black scripts/*.py pack.py
   ```

---

### Fix 6.3: Update Documentation

**What to update:** README, scripts/README.md to reflect fixes.

**Implementation steps:**

1. **Update README.md:**
   - Add section on error handling
   - Document new config options (`overwrite_existing`, `debug`)
   - Update troubleshooting section

2. **Update scripts/README.md:**
   - Document error handling standards
   - Add examples of common errors

---

**Phase 6 Completion Checklist:**
- [ ] Code formatted consistently
- [ ] Dead code removed
- [ ] Documentation updated
- [ ] Commit: "chore: code cleanup and documentation (phase 6)"

---

## Phase 7 — Final Validation Checklist

**Goal:** Verify all fixes are complete and system is production-ready.

**Execution:** Run through this checklist systematically.

---

### Critical Issues Resolution

- [ ] **Fix 1.1:** Required field validation implemented and tested
  - Test: Missing artist → clear error
  - Test: Missing title → clear error
  - Test: Valid config → workflow proceeds

- [ ] **Fix 1.2:** Duplicate imports removed
  - Verify: `scripts/orchestrator.py` has no duplicate imports
  - Verify: Script runs without errors

- [ ] **Fix 1.3:** JSON parsing errors handled
  - Test: Malformed JSON → clear error with line/column
  - Test: Invalid UTF-8 → clear encoding error

- [ ] **Fix 1.4:** Missing dependencies fail fast
  - Test: Uninstall mutagen → clear error before workflow starts
  - Test: Uninstall Pillow → clear error before workflow starts

- [ ] **Fix 1.5:** File overwrite protection
  - Test: Existing file → error unless overwrite flag set
  - Test: Overwrite flag → file replaced with warning

---

### Architectural Consistency

- [ ] **Fix 2.1:** Audio format validation complete
  - FLAC/M4A validated OR removed from supported formats
  - Documentation matches implementation

- [ ] **Fix 2.2:** Configuration schema validation
  - Type validation working
  - Value range validation working
  - Nested structure validation working

- [ ] **Fix 2.3:** Error handling standardized
  - All functions follow documented pattern
  - No functions return `None` on error

---

### Configuration Safety

- [ ] **Fix 3.1:** Filename sanitization
  - Invalid characters removed
  - Long names truncated
  - Empty names handled

- [ ] **Fix 3.2:** Multiple file match warnings
  - Warning displayed when multiple matches found

- [ ] **Fix 3.3:** Error context improved
  - Debug mode shows tracebacks
  - Error messages are actionable

---

### Operational Hardening

- [ ] **Fix 4.1:** File locking implemented
  - Concurrent execution prevented
  - Stale locks cleaned up

- [ ] **Fix 4.2:** Disk space check
  - Insufficient space detected before workflow starts

---

### Test Coverage

- [ ] **Test 5.1:** Unit tests for validation
  - Coverage > 80% for validation functions
  - All edge cases tested

- [ ] **Test 5.2:** Integration test
  - Full workflow test passes
  - Error path tests pass

- [ ] **Test 5.3:** Error handling tests
  - All exception paths tested

- [ ] **Test 5.4:** CI/CD configured
  - Tests run on every commit
  - Coverage reported

---

### Code Quality

- [ ] **Fix 6.1:** Dead code removed
- [ ] **Fix 6.2:** Code formatted
- [ ] **Fix 6.3:** Documentation updated

---

### Final Questions

**Answer these honestly:**

1. **Are all critical issues resolved?**
   - [ ] Yes, all 5 critical issues fixed and tested
   - [ ] No, list remaining: _______________

2. **Are defaults production-safe?**
   - [ ] Yes, all defaults are safe
   - [ ] No, unsafe defaults: _______________

3. **Are contracts enforced?**
   - [ ] Yes, validation enforces all contracts
   - [ ] No, unenforced contracts: _______________

4. **Can a new engineer reason about the system?**
   - [ ] Yes, code is clear and documented
   - [ ] No, unclear areas: _______________

5. **Would you personally approve deployment now?**
   - [ ] Yes, ready for production
   - [ ] No, blockers: _______________
   - [ ] Conditional: _______________

---

## Execution Summary

**Total Phases:** 7  
**Estimated Time:** 3-5 days (critical) + 1-2 weeks (testing)  
**Risk Level After Completion:** LOW (from HIGH)

**Recommended Deployment Approach:**
1. Complete Phases 1-3 (critical fixes)
2. Deploy to limited beta users
3. Complete Phases 4-6 (hardening and testing)
4. Full production deployment

**Sign-off Required:**
- [ ] All Phase 1-3 items complete
- [ ] Manual testing passes
- [ ] Code review completed
- [ ] Ready for beta deployment

---

**Plan Status:** Ready for execution  
**Last Updated:** [Date]  
**Next Review:** After Phase 3 completion

