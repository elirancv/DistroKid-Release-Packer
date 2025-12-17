# Project Structure

Complete overview of the DistroKid Release Packer project organization.

## Directory Tree

```
DistroKid Release Packer/
│
├── .github/                    # GitHub configuration
│   ├── workflows/
│   │   └── test.yml           # CI/CD pipeline
│   ├── ISSUE_TEMPLATE/        # Issue templates
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md # PR template
│
├── docs/                       # All documentation
│   ├── README.md              # Documentation index
│   ├── QUICK_START.md         # Quick start guide
│   ├── USAGE_GUIDE.md         # Usage instructions
│   ├── HOW_IT_WORKS.md        # Architecture explanation
│   ├── WORKFLOW.md            # Complete workflow
│   ├── PROJECT_STRUCTURE.md   # This file
│   ├── SETUP_COMPLETE.md      # Setup summary
│   ├── CHANGELOG.md           # Version history
│   ├── CONTRIBUTING.md        # Contribution guidelines
│   ├── development/           # Development documentation
│   │   ├── REMEDIATION_PLAN.md
│   │   ├── REMEDIATION_TODOS.md
│   │   └── REFACTORING_SUMMARY.md
│   └── reports/               # Review reports
│       ├── PRODUCTION_REVIEW.md
│       └── PHASE_7_VALIDATION_REPORT.md
│
├── scripts/                    # Automation scripts
│   ├── README.md              # Scripts documentation
│   ├── orchestrator.py/js     # Main workflow coordinator
│   ├── extract_suno_version.py/js
│   ├── rename_audio_files.py/js
│   ├── organize_stems.py/js
│   ├── tag_stems.py/js
│   ├── tag_audio_id3.py/js
│   ├── validate_cover_art.py
│   └── validate_compliance.py
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration
│   ├── fixtures/              # Test data
│   │   ├── config_valid.json
│   │   ├── config_missing_artist.json
│   │   ├── config_empty_title.json
│   │   ├── config_invalid_bpm.json
│   │   ├── config_invalid_tracknum.json
│   │   └── config_malformed.json
│   ├── unit/                  # Unit tests
│   │   ├── test_config_validation.py
│   │   └── test_error_handling.py
│   └── integration/           # Integration tests
│       └── test_full_workflow.py
│
├── .gitignore                 # Git ignore rules
├── .editorconfig              # Editor configuration
├── .gitattributes             # Git attributes (line endings)
├── .pre-commit-config.yaml    # Pre-commit hooks config
├── LICENSE                    # MIT License
├── README.md                  # Main project README
├── SECURITY.md                # Security policy
├── CODE_OF_CONDUCT.md         # Code of conduct
├── AUTHORS.md                 # Contributors list
├── Makefile                   # Build automation
├── requirements.txt           # Python dependencies
├── package.json               # JavaScript dependencies
├── pyproject.toml             # Python packaging config
├── pytest.ini                 # Test configuration
├── release.example.json       # Example configuration
├── artist-defaults.example.json # Example artist defaults
├── pack.py                    # Main CLI entry point (Python)
└── pack.js                    # Main CLI entry point (JavaScript)
```

## File Descriptions

### Root Level (Essential Files Only)

- **`README.md`** - Main project documentation and overview
- **`LICENSE`** - MIT License
- **`.gitignore`** - Git ignore patterns
- **`Makefile`** - Build and automation commands
- **`requirements.txt`** - Python package dependencies
- **`package.json`** - JavaScript dependencies and npm scripts
- **`pytest.ini`** - Pytest configuration
- **`release.example.json`** - Example configuration template
- **`pack.py`** - Primary CLI entry point (Python)
- **`pack.js`** - Alternative CLI entry point (JavaScript)

### Documentation (`docs/`)

**User Guides:**
- **`README.md`** - Documentation index
- **`QUICK_START.md`** - 5-minute getting started guide
- **`USAGE_GUIDE.md`** - Step-by-step usage instructions
- **`HOW_IT_WORKS.md`** - Detailed explanation of tool architecture
- **`WORKFLOW.md`** - Complete workflow checklist

**Project Information:**
- **`PROJECT_STRUCTURE.md`** - This file - project organization
- **`SETUP_COMPLETE.md`** - Setup completion summary

**Project Management:**
- **`CHANGELOG.md`** - Version history and changes
- **`CONTRIBUTING.md`** - Guidelines for contributors

**Development Documentation (`docs/development/`):**
- **`REMEDIATION_PLAN.md`** - Production readiness remediation plan
- **`REMEDIATION_TODOS.md`** - Remediation task checklist
- **`REFACTORING_SUMMARY.md`** - Code refactoring summary

**Reports (`docs/reports/`):**
- **`PRODUCTION_REVIEW.md`** - Pre-deployment quality review
- **`PHASE_7_VALIDATION_REPORT.md`** - Final validation report

### Scripts (`scripts/`)

All automation scripts are available in both Python and JavaScript:

- **`orchestrator.py/js`** - Main workflow coordinator
- **`extract_suno_version.py/js`** - Extract Suno version from URLs/metadata
- **`rename_audio_files.py/js`** - Rename audio files to naming convention
- **`organize_stems.py/js`** - Organize stem files with metadata
- **`tag_stems.py/js`** - Apply ID3v2 tags to stem files
- **`tag_audio_id3.py/js`** - Apply ID3v2 tags and embed cover art
- **`validate_cover_art.py`** - Validate cover art compliance
- **`validate_compliance.py`** - Full DistroKid compliance validator
- **`README.md`** - Scripts documentation

### Tests (`tests/`)

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`fixtures/`** - Test configuration files and sample data
- **`unit/`** - Unit tests for individual functions
- **`integration/`** - Integration tests for full workflow

### Configuration Files

- **`.cursor/rules/`** - Cursor IDE coding standards
- **`.github/workflows/`** - CI/CD pipeline configuration
- **`release.example.json`** - Example configuration (copy to `release.json`)

## Output Directories (Gitignored)

These directories are created during workflow execution:

- **`Releases/`** - Generated release packages
- **`exports/`** - Source files (audio, stems, cover art)

## Best Practices

1. **Keep root clean** - Only essential files in root directory
2. **Documentation in `docs/`** - All documentation organized by category
3. **Scripts in `scripts/`** - All automation scripts in dedicated directory
4. **Tests in `tests/`** - All tests organized by type (unit/integration)
5. **Configuration examples** - Use `.example` suffix for templates

## Navigation

- **New to the project?** Start with [QUICK_START.md](QUICK_START.md)
- **Want to understand how it works?** Read [HOW_IT_WORKS.md](HOW_IT_WORKS.md)
- **Ready to use it?** Follow [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Looking for documentation?** See [docs/README.md](README.md)
