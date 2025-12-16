# DistroKid Release Packer

[![Tests](https://github.com/elirancv/distrokid-release-packer/workflows/Tests/badge.svg)](https://github.com/elirancv/distrokid-release-packer/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 14+](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Command-line automation toolkit for preparing and packaging music tracks generated in Suno for distribution via DistroKid. Automates the complete workflow from audio file export to DistroKid-ready release packages with ID3v2 metadata tagging, compliance validation, and standardized file organization.

---

## Quick Start

**Prerequisites:**
- Python 3.8+
- Node.js 14+ (optional, for JavaScript variant)
- pip and npm

**Install and run:**
```bash
# Install dependencies
make setup

# Edit release.json with your track details
# Place audio files in exports/ directory

# Run workflow
make run
```

**Expected output:**
```
Releases/{TrackName}/
├── Audio/Artist - Title.mp3
├── Stems/ (if enabled)
├── Cover/Artist - Title - Cover.jpg
└── Metadata/Artist - Title - Metadata.json
```

For detailed setup, see [Installation & Setup](#installation--setup). For complete workflow documentation, see `docs/QUICK_START.md`.

---

## Technology Stack

**Runtime & Language:**
- Python 3.8+ (primary implementation)
- Node.js 14+ (alternative implementation)

**Core Dependencies:**
- `mutagen>=1.47.0` - ID3v2 metadata tagging for MP3 files
- `Pillow>=10.0.0` - Image processing for cover art validation
- `librosa>=0.10.0` - Audio analysis for clipping detection (optional)
- `soundfile>=0.12.0` - Audio file I/O for librosa
- `rich>=13.0.0` - Terminal output formatting and styling
- `node-id3@^0.2.1` - ID3v2 tag writing (JavaScript variant)
- `sharp@^0.32.6` - Image processing (JavaScript variant)

**Development Tools:**
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Test coverage reporting

**Build & Package:**
- Make (for automation via Makefile)
- pip (Python dependency management)
- npm (JavaScript dependency management)

**External Dependencies:**
- ffmpeg (optional, for audio clipping fix functionality)

---

## Architecture Overview

The project follows a modular script-based architecture where individual workflow steps are implemented as separate scripts, orchestrated by a central coordinator.

```mermaid
flowchart TD
    A[User: pack.py release.json] --> B[Orchestrator]
    B --> C[Extract Suno Version]
    B --> D[Rename Audio Files]
    B --> E[Organize Stems]
    B --> F[Tag Audio ID3v2]
    B --> G[Validate Cover Art]
    B --> H[Validate Compliance]
    B --> I[Generate Metadata JSON]
    C --> J[Release Directory]
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K[DistroKid Ready Files]
```

**Workflow sequence:**
1. Validate configuration and dependencies
2. Acquire workflow lock (prevent concurrent execution)
3. Check disk space (minimum 500MB)
4. Extract Suno version/build ID (if URL provided)
5. Rename audio files to convention: `Artist - Title.wav/mp3`
6. Organize stems (if enabled) into `Stems/` directory
7. Tag audio files with ID3v2 metadata and embed cover art
8. Validate cover art dimensions (3000×3000) and file size (<5MB)
9. Run full DistroKid compliance checks
10. Generate release metadata JSON file
11. Release workflow lock

**Configuration system:** Two-tier configuration with `artist-defaults.json` (defaults) merged with release-specific `release.json`.

---

## Project Structure

```
.
├── .github/                   # GitHub configuration
│   ├── workflows/             # CI/CD pipelines
│   │   └── test.yml
│   ├── ISSUE_TEMPLATE/       # Issue templates
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── .editorconfig             # Editor configuration
├── .gitattributes             # Git attributes (line endings)
├── .pre-commit-config.yaml    # Pre-commit hooks
├── LICENSE                    # MIT License
├── README.md                  # Main project README
├── SECURITY.md                # Security policy
├── CODE_OF_CONDUCT.md         # Code of conduct
├── AUTHORS.md                 # Contributors
├── pack.py                    # Python CLI entry point
├── pack.js                    # JavaScript CLI entry point
├── release.example.json       # Release configuration template
├── artist-defaults.example.json # Artist default settings template
├── requirements.txt           # Python dependencies
├── package.json               # JavaScript dependencies
├── pyproject.toml             # Python packaging config
├── pytest.ini                 # Test configuration
├── Makefile                   # Build automation
├── scripts/                   # Workflow automation scripts
│   ├── orchestrator.py/js     # Main workflow coordinator
│   ├── extract_suno_version.py/js
│   ├── rename_audio_files.py/js
│   ├── organize_stems.py/js
│   ├── tag_audio_id3.py/js
│   ├── validate_cover_art.py
│   ├── validate_compliance.py
│   ├── fix_clipping.py
│   └── rich_utils.py          # Terminal output utilities
├── docs/                      # Documentation
│   ├── README.md              # Documentation index
│   ├── QUICK_START.md
│   ├── WORKFLOW.md
│   ├── CONTRIBUTING.md        # Contribution guidelines
│   ├── CHANGELOG.md           # Version history
│   └── ...
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/              # Test data
├── exports/                   # Source audio files (gitignored)
└── Releases/                  # Generated releases (gitignored)
```

**Key directories:**
- `scripts/` - Modular workflow scripts (Python and JavaScript variants)
- `docs/` - Comprehensive documentation and guides
- `tests/` - Unit and integration test suite
- `Releases/` - Output directory for processed releases
- `exports/` - Input directory for source audio files

---

## Core API & Usage Examples

**Primary entry point:**
```bash
python pack.py release.json
```

**CLI commands:**
```bash
python pack.py --help      # Show help
python pack.py --example   # Show example config
```

**Programmatic usage (Python):**
```python
from scripts.orchestrator import run_release_workflow, load_config

# Load configuration
config = load_config("release.json")

# Run workflow
success = run_release_workflow(config)
```

**Programmatic usage (JavaScript):**
```javascript
const { runReleaseWorkflow, loadConfig } = require('./scripts/orchestrator');

// Load configuration
const config = loadConfig('release.json');

// Run workflow
runReleaseWorkflow(config).then(success => {
    console.log('Workflow completed:', success);
});
```

**Individual script usage:**
```python
from scripts.tag_audio_id3 import tag_audio_file
from scripts.validate_cover_art import validate_cover_art

# Tag audio file
tag_audio_file("track.mp3", "cover.jpg", {
    "title": "Track Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "year": "2025"
})

# Validate cover art
result = validate_cover_art("cover.jpg")
```

For complete API documentation, see `scripts/README.md`.

---

## Installation & Setup

### Prerequisites

- Python 3.8+ (required)
- Node.js 14+ (optional, for JavaScript variant)
- pip (Python package manager)
- npm (optional, for JavaScript dependencies)
- Make (optional, for Makefile commands)
- ffmpeg (optional, for audio clipping fix)

### Install

**Option 1: Using Makefile (Recommended)**
```bash
make setup
```

This installs Python dependencies and creates `release.json` from `release.example.json` if missing.

**Option 2: Manual Installation**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install JavaScript dependencies (optional)
npm install

# Create configuration files
cp release.example.json release.json
cp artist-defaults.example.json artist-defaults.json
```

### Verify Installation

```bash
# Check Python dependencies
make check-python

# Check Node.js dependencies
make check-node

# Or manually
python -c "import mutagen, PIL, librosa; print('Dependencies OK')"
```

### Common Issues

- **ImportError for mutagen/Pillow:** Run `pip install -r requirements.txt`
- **ffmpeg not found:** Install ffmpeg and ensure it's in PATH (only needed for clipping fix)
- **Node.js errors:** Ensure Node.js 14+ is installed (only needed for JavaScript variant)

### Optional Features

- **Audio clipping detection:** Requires `librosa` (installed via requirements.txt)
- **Audio clipping fix:** Requires `ffmpeg` installed separately
- **JavaScript variant:** Requires Node.js and npm

---

## Environment & Configuration

**Configuration files:**
- `artist-defaults.json` - Default values (artist name, publisher, composer template)
- `release.json` - Release-specific configuration

**Configuration precedence:**
1. `release.json` (release-specific, overrides defaults)
2. `artist-defaults.json` (defaults, used if not in release.json)

**Required fields:**
- `title` - Track title
- `source_audio_dir` - Source audio files directory
- `release_dir` - Output directory path

**Optional fields:**
- `artist` - Artist name (uses `artist-defaults.json` default if not specified)
- `suno_url` - Suno track URL (for version extraction)
- `source_stems_dir` - Source stems directory
- `genre`, `bpm`, `key`, `explicit`, `language`, `mood`, `target_regions`
- `isrc`, `upc` - Pre-assigned identifiers
- `id3_metadata` - Album, year, track number, composer, publisher, etc.

**Feature flags:**
- `rename_audio` - Enable audio file renaming (default: true)
- `organize_stems` - Enable stem organization (default: false)
- `tag_audio` - Enable ID3v2 tagging (default: true)
- `validate_cover` - Enable cover art validation (default: true)
- `validate_compliance` - Enable compliance checks (default: true)
- `strict_mode` - Fail workflow on any error (default: false)
- `overwrite_existing` - Allow overwriting existing files (default: false)
- `auto_fix_clipping` - Automatically fix audio clipping (default: false)
- `debug` - Enable debug mode with full tracebacks (default: false)

**Environment variables:**
Not detected - No environment variable usage in codebase.

---

## Scripts & Commands

**Makefile commands:**

**Setup:**
- `make setup` - Install dependencies and create release.json
- `make install` - Install Python dependencies
- `make install-js` - Install JavaScript dependencies
- `make install-all` - Install all dependencies

**Execution:**
- `make run` - Run the release packer (requires release.json)
- `make run-js` - Run using JavaScript orchestrator

**Utilities:**
- `make help` - Show all available commands
- `make example` - Show example configuration
- `make validate` - Validate release.json syntax
- `make check` - Check if dependencies are installed
- `make clean` - Clean temporary files (keeps Releases/)
- `make clean-all` - Clean everything including Releases/

**Testing:**
- `make test` - Run all tests
- `make test-cov` - Run tests with coverage report
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only

**Development:**
- `make docs` - Show documentation links
- `make info` - Show project information
- `make version` - Show version info

**npm scripts:**
- `npm run orchestrate` - Run full workflow
- `npm run extract-version` - Extract Suno version
- `npm run rename-audio` - Rename audio files
- `npm run tag-audio` - Tag audio files

---

## Development Workflow

**Setting up development environment:**
```bash
# Clone repository
git clone <repository-url>
cd distrokid-release-packer

# Install development dependencies
make install-all

# Run tests
make test
```

**Code style:**
- Python: Use `pathlib.Path` for file operations, `snake_case` for functions
- JavaScript: Use `path.join()` for paths, `camelCase` for functions
- JSON: Use `snake_case` for keys, ISO 8601 for dates

**Testing:**
- Framework: pytest
- Run tests: `make test` or `pytest tests/`
- Run with coverage: `make test-cov` or `pytest --cov=scripts tests/`
- Test organization: `tests/unit/` for unit tests, `tests/integration/` for integration tests

**Code quality:**
- Type hints: Recommended for Python functions
- Error handling: Validation functions return structured dicts, operation functions raise exceptions
- File naming: Follow strict conventions (see `.cursor/rules/distrokid.cursorrules`)

**PR workflow:**
- Branch naming: `feature/description` or `bugfix/description`
- Requires: Tests passing, code follows style guidelines
- See `docs/CONTRIBUTING.md` for detailed guidelines

---

## Testing & Quality

**Testing:**
- Framework: pytest
- Coverage: Tracked via Codecov in CI (`.github/workflows/test.yml`)
- Test organization:
  - `tests/unit/` - Unit tests for validation functions
  - `tests/integration/` - Integration tests for full workflow
  - `tests/fixtures/` - Test configuration files and sample data
- CI/CD: Automated testing on push/PR across multiple OS (Ubuntu, Windows, macOS) and Python versions (3.8, 3.9, 3.10, 3.11)

**Code quality:**
- Error handling: Structured validation results, exception-based operations
- Type safety: Python type hints recommended
- File operations: `pathlib.Path` (Python), `path.join()` (JavaScript)

**Known gaps:**
- No automated linting/formatting configuration detected (`.pre-commit-config.yaml` exists but linting tools commented out; no `.flake8`, `.pylintrc`, or `.ruff.toml` found)

---

## Dependencies & Compatibility

**Key dependencies:**
- `mutagen` - ID3v2 metadata tagging; required for audio file tagging
- `Pillow` - Image processing; required for cover art validation
- `librosa` - Audio analysis; optional, for clipping detection
- `rich` - Terminal output; required for formatted CLI output
- `node-id3` - ID3v2 tagging (JavaScript); required for JS variant
- `sharp` - Image processing (JavaScript); required for JS variant

**Compatibility:**
- Python: 3.8, 3.9, 3.10, 3.11, 3.12
- Node.js: 14.0+, 16.0+, 18.0+, 20.0+
- OS: Linux, macOS, Windows (with Windows-specific handling in Makefile)
- Audio formats: MP3 (tagging), WAV (stems, analysis)

**Version constraints:**
- See `requirements.txt` for Python dependencies
- See `package.json` for JavaScript dependencies

---

## Limitations, Assumptions & TODOs

**Known limitations:**
- JavaScript stem tagging uses companion JSON files (WAV ID3 support limitations)
- Node.js disk space check is limited (no built-in API)
- ffmpeg required for clipping fix but not automatically installed
- librosa optional for clipping detection (validation continues if missing)
- No batch processing of multiple releases
- No DistroKid API integration (workflow stops at file preparation)

**Assumptions:**
- Source audio files exported from Suno and placed in `source_audio_dir` before workflow
- Cover art files follow naming convention in `release_dir/Cover/`
- Python 3.8+ or Node.js 14+ installed and accessible in PATH
- File system permissions allow read/write access
- ffmpeg installed and in PATH if `auto_fix_clipping` enabled

**TODOs & Improvements:**

| Item | Priority | Details |
|------|----------|---------|
| Implement structured logging | High | Replace print statements with logging module |
| Add JSON schema validation | Medium | Validate release.json structure with jsonschema |
| Add batch processing | Medium | Process multiple releases from directory |
| Add Docker containerization | Low | Consistent execution environment |
| Add error recovery | Medium | Retry mechanisms for transient failures |
| Add DistroKid API integration | Low | Automated upload after file preparation |

---

## Deployment

**Not applicable:** This is a local development tool intended for use on developer machines, not a deployed service.

**CI/CD:** Automated testing configured via GitHub Actions (`.github/workflows/test.yml`) - runs on push/PR across multiple OS and Python versions. No deployment infrastructure (Docker, containerization) as tool is executed locally via CLI.

---

## Troubleshooting & FAQ

**Q: ImportError for mutagen/Pillow**
A: Install dependencies: `pip install -r requirements.txt`

**Q: Config file not found**
A: Create from example: `cp release.example.json release.json`

**Q: Audio file not found**
A: Ensure audio files are in `source_audio_dir` (default: `./exports`)

**Q: Cover art validation fails**
A: Ensure cover art is 3000×3000 pixels, <5MB, JPG or PNG format

**Q: Workflow lock error**
A: Another workflow is running or stale lock file exists. Remove `.workflow.lock` if safe.

**Q: ffmpeg not found (clipping fix)**
A: Install ffmpeg and ensure it's in PATH, or disable `auto_fix_clipping`

**Q: Tests fail on Windows**
A: Some path handling may differ. Use WSL2 or report issue with details.

---

## Contributing & Community

**How to contribute:**
1. Fork repository
2. Create feature branch (`feature/description`)
3. Make changes following code style guidelines
4. Add tests for new functionality
5. Run test suite: `make test`
6. Submit pull request

**Code standards:**
- Follow `.cursor/rules/distrokid.cursorrules`
- Use structured error handling patterns
- Add tests for validation functions
- Update documentation for new features

**Reporting issues:**
- Use GitHub Issues
- Include error messages, config (sanitized), and steps to reproduce

**Documentation:**
- See `docs/CONTRIBUTING.md` for detailed guidelines
- Update relevant documentation when adding features

---

## License & Attribution

**License:** [MIT License](LICENSE)

**Copyright:** Copyright (c) 2025 Eliran Cohen

---

## References & Further Reading

**Documentation:**
- `docs/README.md` - Documentation index
- `docs/QUICK_START.md` - Getting started guide
- `docs/WORKFLOW.md` - Complete workflow checklist
- `docs/HOW_IT_WORKS.md` - Tool architecture explanation
- `docs/USAGE_GUIDE.md` - Detailed usage instructions
- `docs/CONTRIBUTING.md` - Contribution guidelines
- `docs/CHANGELOG.md` - Version history
- `scripts/README.md` - Scripts documentation

**External resources:**
- [DistroKid Upload Requirements](https://distrokid.com/help/) - Official DistroKid documentation
- [ID3v2 Specification](https://id3.org/id3v2.3.0) - ID3 tag standard
- [Suno AI](https://suno.ai) - Music generation platform

**Related projects:**
- `mutagen` - Python ID3v2 library
- `node-id3` - JavaScript ID3v2 library
