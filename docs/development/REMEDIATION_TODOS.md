# DistroKid Release Packer - Production Readiness Todo List

**Based on:** [REMEDIATION_PLAN.md](./REMEDIATION_PLAN.md)  
**Status:** In Progress  
**Last Updated:** 2025-01-XX

---

## Progress Summary

- **Phase 0:** 0/4 tasks complete
- **Phase 1:** 0/25 tasks complete (5 critical fixes)
- **Phase 2:** 0/12 tasks complete
- **Phase 3:** 0/10 tasks complete
- **Phase 4:** 0/6 tasks complete
- **Phase 5:** 0/15 tasks complete
- **Phase 6:** 0/8 tasks complete
- **Phase 7:** 0/25 tasks complete

**Total:** 0/105 tasks complete

---

## Phase 0 — Safety & Ground Rules

### Preconditions

- [ ] Create feature branch: `git checkout -b fix/production-readiness`
- [ ] Document current behavior with manual test cases
- [ ] Create `test_manual_baseline.md` with:
  - [ ] Sample config files that currently work
  - [ ] Expected output file structure
  - [ ] Known working audio/cover art files
- [ ] Set up test infrastructure:
  - [ ] Install pytest: `pip install pytest pytest-cov`
  - [ ] Create test directory structure: `mkdir -p tests/{unit,integration,fixtures}`

### Guardrails

- [ ] Never modify `config.example.json` without updating documentation
- [ ] All fixes must maintain backward compatibility with existing valid configs
- [ ] Each phase should be independently committable
- [ ] Run manual smoke test after each phase

### Test Baselines Required

- [ ] Verify: Valid config with all required fields → successful workflow
- [ ] Verify: Missing `artist` field → currently fails silently (baseline for fix)
- [ ] Verify: Malformed JSON config → currently crashes (baseline for fix)
- [ ] Verify: Missing mutagen library → currently skips tagging (baseline for fix)

---

## Phase 1 — Must-Fix Structural & Correctness Issues

### Fix 1.1: Add Required Field Validation

**Files:** `scripts/orchestrator.py`, `pack.py`, `scripts/orchestrator.js`

- [ ] Add `validate_config()` function to `scripts/orchestrator.py` (after `load_config()`, around line 39)
- [ ] Implement required field checks (artist, title)
- [ ] Implement type validation (str type checks)
- [ ] Implement empty value checks
- [ ] Add optional field warnings (source_audio_dir)
- [ ] Add path validation warnings
- [ ] Call `validate_config(config)` at start of `run_release_workflow()` in `scripts/orchestrator.py`
- [ ] Update `pack.py` to catch `ValueError` exceptions with clear error messages
- [ ] Add validation function to `scripts/orchestrator.js`
- [ ] Call validation at start of `runReleaseWorkflow()` in `scripts/orchestrator.js`
- [ ] Create test fixture: `tests/fixtures/config_missing_artist.json`
- [ ] Create test fixture: `tests/fixtures/config_empty_title.json`
- [ ] Create test fixture: `tests/fixtures/config_valid.json`
- [ ] Verify: Missing artist → clear error message, exit code 1
- [ ] Verify: Empty title → clear error message, exit code 1
- [ ] Verify: Valid config → workflow proceeds normally

### Fix 1.2: Remove Duplicate Imports

**Files:** `scripts/orchestrator.py`

- [ ] Remove duplicate `import sys` (line 14)
- [ ] Remove duplicate `from pathlib import Path` (line 15)
- [ ] Verify: Script compiles without errors (`python -m py_compile scripts/orchestrator.py`)
- [ ] Verify: Script runs normally with valid config

### Fix 1.3: Handle JSON Parsing Errors

**Files:** `scripts/orchestrator.py`, `pack.py`, `scripts/orchestrator.js`

- [ ] Update `load_config()` in `scripts/orchestrator.py` to catch `json.JSONDecodeError`
- [ ] Add UTF-8 encoding specification in `load_config()`
- [ ] Add `UnicodeDecodeError` handling in `load_config()`
- [ ] Update error messages to include line/column numbers
- [ ] Update `pack.py` error handling to catch `ValueError` for JSON errors
- [ ] Add troubleshooting guidance in `pack.py` error messages
- [ ] Update `loadConfig()` in `scripts/orchestrator.js` with try-catch for JSON.parse
- [ ] Create test fixture: `tests/fixtures/config_malformed.json`
- [ ] Verify: Malformed JSON → clear error with line/column, exit code 1
- [ ] Verify: Invalid UTF-8 → clear encoding error message

### Fix 1.4: Fail Fast on Missing Dependencies

**Files:** `scripts/orchestrator.py`, `scripts/tag_audio_id3.py`, `scripts/validate_compliance.py`, `scripts/validate_cover_art.py`

- [ ] Add `validate_dependencies()` function to `scripts/orchestrator.py` (after `validate_config()`)
- [ ] Check for mutagen import in `validate_dependencies()`
- [ ] Check for Pillow import in `validate_dependencies()`
- [ ] Call `validate_dependencies()` at start of `run_release_workflow()` (after `validate_config()`)
- [ ] Update `tag_audio_file()` in `scripts/tag_audio_id3.py` to raise `ImportError` instead of returning None
- [ ] Update `validate_compliance.py` to raise `ImportError` when dependencies missing
- [ ] Update `validate_cover_art.py` to raise `ImportError` when dependencies missing
- [ ] Verify: With dependencies installed → normal execution
- [ ] Verify: With mutagen uninstalled → clear error before workflow starts
- [ ] Verify: With Pillow uninstalled → clear error before workflow starts

### Fix 1.5: Prevent Accidental File Overwrites

**Files:** `scripts/rename_audio_files.py`, `scripts/organize_stems.py`, `scripts/orchestrator.py`, `config.example.json`

- [ ] Add file existence check in `rename_audio_files()` before copying (around line 22)
- [ ] Add `overwrite` parameter to `rename_audio_files()` function signature
- [ ] Update overwrite check logic in `rename_audio_files()` to use parameter
- [ ] Update orchestrator call to `rename_audio_files()` to pass `overwrite_existing` flag (around line 85)
- [ ] Add file existence check in `organize_stems()` before copying
- [ ] Add `overwrite` parameter to `organize_stems()` function signature
- [ ] Update orchestrator call to `organize_stems()` to pass `overwrite_existing` flag
- [ ] Add `overwrite_existing` field to `config.example.json` with comment
- [ ] Create test: Existing file without overwrite flag → FileExistsError
- [ ] Create test: Existing file with overwrite flag → file replaced with warning

**Phase 1 Completion:**
- [ ] All 5 critical fixes implemented
- [ ] Manual verification tests pass
- [ ] No regressions in existing functionality
- [ ] Error messages are clear and actionable
- [ ] Commit: "fix: address critical production issues (phase 1)"

---

## Phase 2 — Architectural Consistency & Contract Alignment

### Fix 2.1: Complete Audio Format Validation

**Files:** `scripts/validate_compliance.py`, `requirements.txt`

- [ ] Add FLAC support to `validate_audio_file()` using `mutagen.flac.FLAC`
- [ ] Add M4A support to `validate_audio_file()` using `mutagen.mp4.MP4`
- [ ] Update validation logic to handle FLAC/M4A duration and sample rate
- [ ] Add ImportError handling for FLAC/MP4 support
- [ ] Verify mutagen version supports FLAC/MP4 in `requirements.txt` (mutagen>=1.47.0)
- [ ] Create test with FLAC file (if available) → duration and sample rate validated
- [ ] Create test with M4A file (if available) → duration validated
- [ ] **Alternative:** If FLAC/M4A not needed, remove from `valid_formats` and update documentation

### Fix 2.2: Add Configuration Schema Validation

**Files:** `scripts/orchestrator.py`

- [ ] Add type validation for optional fields (bpm, explicit, organize_stems, etc.) in `validate_config()`
- [ ] Add value range validation for BPM (1-300) in `validate_config()`
- [ ] Add path validation for source directories in `validate_config()`
- [ ] Add validation for nested `id3_metadata` structure in `validate_config()`
- [ ] Add track number format validation (X/Total) in `validate_config()`
- [ ] Create test fixture: `tests/fixtures/config_invalid_bpm.json`
- [ ] Create test fixture: `tests/fixtures/config_invalid_tracknum.json`
- [ ] Verify: Invalid BPM → validation error
- [ ] Verify: Invalid track number format → validation error

### Fix 2.3: Standardize Error Handling Pattern

**Files:** All scripts in `scripts/`, `scripts/README.md`

- [ ] Review all functions in `scripts/` for error handling consistency
- [ ] Ensure no functions return `None` on error
- [ ] Ensure orchestrator handles all exception types
- [ ] Document error handling standards in `scripts/README.md`:
  - [ ] Validation functions return structured dict
  - [ ] Operation functions raise exceptions
  - [ ] Never return None to indicate failure

**Phase 2 Completion:**
- [ ] Audio format validation complete or formats removed from docs
- [ ] Configuration schema validation implemented
- [ ] Error handling patterns documented and consistent
- [ ] Commit: "fix: improve validation and consistency (phase 2)"

---

## Phase 3 — Configuration, Feature Flags & Environment Safety

### Fix 3.1: Sanitize File Paths

**Files:** `scripts/orchestrator.py`

- [ ] Add `sanitize_filename()` function to `scripts/orchestrator.py` (after imports)
- [ ] Implement invalid character removal (`<>:"/\|?*`)
- [ ] Implement leading/trailing dot and space removal
- [ ] Implement length limiting (max 200 chars)
- [ ] Implement empty name handling (return "Unknown")
- [ ] Apply sanitization in `run_release_workflow()` after validation
- [ ] Update `validate_config()` to warn about invalid characters
- [ ] Create test fixture: `tests/fixtures/config_invalid_chars.json`
- [ ] Create test fixture: `tests/fixtures/config_long_names.json`
- [ ] Verify: Invalid characters → warning message, sanitized filenames created
- [ ] Verify: Very long names → names truncated, files created

### Fix 3.2: Warn on Multiple File Matches

**Files:** `scripts/organize_stems.py`

- [ ] Add check for multiple matching files in `organize_stems()` (around line 31)
- [ ] Add warning message listing all matching files
- [ ] Add message indicating which file will be used
- [ ] Create test with multiple matching files → warning message displayed

### Fix 3.3: Improve Error Context and Logging

**Files:** `scripts/orchestrator.py`

- [ ] Add `debug_mode` variable at start of `run_release_workflow()`
- [ ] Update exception handler for rename_audio step to include traceback in debug mode
- [ ] Update exception handler for organize_stems step to include traceback in debug mode
- [ ] Update exception handler for tag_stems step to include traceback in debug mode
- [ ] Update exception handler for tag_audio step to include traceback in debug mode
- [ ] Add helpful message when debug mode is off
- [ ] Create test fixture: `tests/fixtures/config_debug.json`
- [ ] Verify: Debug mode off → error message without traceback
- [ ] Verify: Debug mode on → full traceback printed

**Phase 3 Completion:**
- [ ] Filename sanitization implemented
- [ ] Multiple file match warnings added
- [ ] Error context improved with debug mode
- [ ] Commit: "fix: improve configuration safety and error handling (phase 3)"

---

## Phase 4 — Concurrency, Performance & Operational Hardening

### Fix 4.1: Add File Locking Protection

**Files:** `scripts/orchestrator.py`

- [ ] Add `acquire_workflow_lock()` function to `scripts/orchestrator.py`
- [ ] Implement stale lock detection (older than 1 hour)
- [ ] Implement lock file creation with PID and timestamp
- [ ] Add `release_workflow_lock()` function
- [ ] Wrap workflow execution in try/finally to ensure lock release
- [ ] Add `import time` and `import os` if not already present
- [ ] Verify: Concurrent execution → error about lock file
- [ ] Verify: Stale lock → automatically removed

### Fix 4.2: Add Disk Space Check

**Files:** `scripts/orchestrator.py`

- [ ] Add `check_disk_space()` function to `scripts/orchestrator.py`
- [ ] Implement disk space calculation using `shutil.disk_usage()`
- [ ] Add check for minimum required space (500MB)
- [ ] Call `check_disk_space()` before file operations in `run_release_workflow()`
- [ ] Verify: Insufficient disk space → clear error before workflow starts

**Phase 4 Completion:**
- [ ] File locking implemented
- [ ] Disk space check added
- [ ] Commit: "fix: add operational safeguards (phase 4)"

---

## Phase 5 — Test Coverage & Verification Gaps

### Test 5.1: Unit Tests for Validation Functions

**Files to create:** `tests/unit/test_config_validation.py`, `tests/unit/test_audio_validation.py`, `tests/unit/test_cover_validation.py`

- [ ] Create `tests/unit/test_config_validation.py` with tests for:
  - [ ] Missing required fields
  - [ ] Empty required fields
  - [ ] Invalid BPM type
  - [ ] Valid config
- [ ] Create `tests/unit/test_audio_validation.py` with tests for audio validation
- [ ] Create `tests/unit/test_cover_validation.py` with tests for cover validation
- [ ] Run tests: `pytest tests/unit/ -v`
- [ ] Verify coverage > 80% for validation functions

### Test 5.2: Integration Test for Full Workflow

**Files to create:** `tests/integration/test_full_workflow.py`, `tests/fixtures/sample_audio.mp3`, `tests/fixtures/sample_cover.jpg`

- [ ] Create `tests/integration/test_full_workflow.py`
- [ ] Add `temp_release_dir` fixture
- [ ] Add `test_full_workflow_success()` test
- [ ] Add `test_workflow_missing_source_files()` test
- [ ] Create test fixture: `tests/fixtures/sample_audio.mp3` (small test file)
- [ ] Create test fixture: `tests/fixtures/sample_cover.jpg` (3000x3000 test image)
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Verify: All happy paths and critical error paths tested

### Test 5.3: Test Error Handling Paths

**Files to create:** `tests/unit/test_error_handling.py`

- [ ] Create `tests/unit/test_error_handling.py`
- [ ] Add test for malformed JSON: `test_load_config_malformed_json()`
- [ ] Add test for missing dependencies (if possible)
- [ ] Run error handling tests: `pytest tests/unit/test_error_handling.py -v`

### Test 5.4: Add CI/CD Pipeline

**Files to create:** `.github/workflows/test.yml`

- [ ] Create `.github/workflows/test.yml` with GitHub Actions workflow
- [ ] Configure workflow to run on push and pull_request
- [ ] Add Python setup step
- [ ] Add dependency installation step
- [ ] Add pytest execution with coverage
- [ ] Add `test` target to Makefile: `pytest tests/ -v`
- [ ] Add `test-cov` target to Makefile: `pytest tests/ -v --cov=scripts --cov-report=html`
- [ ] Verify: CI runs on test commit
- [ ] Verify: Coverage reported in CI

**Phase 5 Completion:**
- [ ] Unit tests for all validation functions
- [ ] Integration test for full workflow
- [ ] Error handling tests
- [ ] CI/CD pipeline configured
- [ ] Test coverage > 70%
- [ ] Commit: "test: add comprehensive test coverage (phase 5)"

---

## Phase 6 — Cleanup, Polish & Professionalism

### Fix 6.1: Remove Dead Code and Comments

**Files:** All Python and JavaScript files in `scripts/`

- [ ] Install flake8: `pip install flake8`
- [ ] Run linter: `flake8 scripts/*.py`
- [ ] Fix all reported linting issues
- [ ] Remove unused imports from all files
- [ ] Remove commented-out code
- [ ] Update docstrings for all functions
- [ ] Ensure all functions have complete parameter descriptions

### Fix 6.2: Standardize Code Formatting

**Files:** All Python files

- [ ] Install black: `pip install black`
- [ ] Format all Python files: `black scripts/*.py pack.py`
- [ ] Add `format` target to Makefile: `black scripts/*.py pack.py`
- [ ] Verify: All files formatted consistently

### Fix 6.3: Update Documentation

**Files:** `README.md`, `scripts/README.md`

- [ ] Update `README.md`:
  - [ ] Add section on error handling
  - [ ] Document new config options (`overwrite_existing`, `debug`)
  - [ ] Update troubleshooting section
- [ ] Update `scripts/README.md`:
  - [ ] Document error handling standards
  - [ ] Add examples of common errors

**Phase 6 Completion:**
- [ ] Code formatted consistently
- [ ] Dead code removed
- [ ] Documentation updated
- [ ] Commit: "chore: code cleanup and documentation (phase 6)"

---

## Phase 7 — Final Validation Checklist

### Critical Issues Resolution

- [ ] **Fix 1.1:** Required field validation implemented and tested
  - [ ] Test: Missing artist → clear error
  - [ ] Test: Missing title → clear error
  - [ ] Test: Valid config → workflow proceeds

- [ ] **Fix 1.2:** Duplicate imports removed
  - [ ] Verify: `scripts/orchestrator.py` has no duplicate imports
  - [ ] Verify: Script runs without errors

- [ ] **Fix 1.3:** JSON parsing errors handled
  - [ ] Test: Malformed JSON → clear error with line/column
  - [ ] Test: Invalid UTF-8 → clear encoding error

- [ ] **Fix 1.4:** Missing dependencies fail fast
  - [ ] Test: Uninstall mutagen → clear error before workflow starts
  - [ ] Test: Uninstall Pillow → clear error before workflow starts

- [ ] **Fix 1.5:** File overwrite protection
  - [ ] Test: Existing file → error unless overwrite flag set
  - [ ] Test: Overwrite flag → file replaced with warning

### Architectural Consistency

- [ ] **Fix 2.1:** Audio format validation complete
  - [ ] FLAC/M4A validated OR removed from supported formats
  - [ ] Documentation matches implementation

- [ ] **Fix 2.2:** Configuration schema validation
  - [ ] Type validation working
  - [ ] Value range validation working
  - [ ] Nested structure validation working

- [ ] **Fix 2.3:** Error handling standardized
  - [ ] All functions follow documented pattern
  - [ ] No functions return `None` on error

### Configuration Safety

- [ ] **Fix 3.1:** Filename sanitization
  - [ ] Invalid characters removed
  - [ ] Long names truncated
  - [ ] Empty names handled

- [ ] **Fix 3.2:** Multiple file match warnings
  - [ ] Warning displayed when multiple matches found

- [ ] **Fix 3.3:** Error context improved
  - [ ] Debug mode shows tracebacks
  - [ ] Error messages are actionable

### Operational Hardening

- [ ] **Fix 4.1:** File locking implemented
  - [ ] Concurrent execution prevented
  - [ ] Stale locks cleaned up

- [ ] **Fix 4.2:** Disk space check
  - [ ] Insufficient space detected before workflow starts

### Test Coverage

- [ ] **Test 5.1:** Unit tests for validation
  - [ ] Coverage > 80% for validation functions
  - [ ] All edge cases tested

- [ ] **Test 5.2:** Integration test
  - [ ] Full workflow test passes
  - [ ] Error path tests pass

- [ ] **Test 5.3:** Error handling tests
  - [ ] All exception paths tested

- [ ] **Test 5.4:** CI/CD configured
  - [ ] Tests run on every commit
  - [ ] Coverage reported

### Code Quality

- [ ] **Fix 6.1:** Dead code removed
- [ ] **Fix 6.2:** Code formatted
- [ ] **Fix 6.3:** Documentation updated

### Final Questions

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

**For detailed implementation instructions, see:** [REMEDIATION_PLAN.md](./REMEDIATION_PLAN.md)

