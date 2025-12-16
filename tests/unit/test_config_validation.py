"""
Unit tests for configuration validation functions.
"""

import pytest
from pathlib import Path
import sys

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from orchestrator import validate_config


def test_validate_config_missing_required():
    """Test validation fails when required fields are missing."""
    config = {"title": "Test"}
    with pytest.raises(ValueError, match="Missing required field: 'artist'"):
        validate_config(config)


def test_validate_config_empty_artist():
    """Test validation fails when artist is empty."""
    config = {"artist": "", "title": "Test"}
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_config(config)


def test_validate_config_empty_title():
    """Test validation fails when title is empty."""
    config = {"artist": "Test", "title": "   "}
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_config(config)


def test_validate_config_invalid_bpm_type():
    """Test validation fails when BPM is not an integer."""
    config = {"artist": "Test", "title": "Test", "bpm": "not a number"}
    with pytest.raises(ValueError, match="must be int"):
        validate_config(config)


def test_validate_config_invalid_bpm_range():
    """Test validation fails when BPM is out of range."""
    config = {"artist": "Test", "title": "Test", "bpm": 500}
    with pytest.raises(ValueError, match="must be integer between 1-300"):
        validate_config(config)


def test_validate_config_invalid_tracknumber_format():
    """Test validation fails when track number format is invalid."""
    config = {
        "artist": "Test",
        "title": "Test",
        "id3_metadata": {
            "tracknumber": "invalid"
        }
    }
    with pytest.raises(ValueError, match="must be.*format"):
        validate_config(config)


def test_validate_config_valid():
    """Test validation passes with valid config."""
    config = {"artist": "Test Artist", "title": "Test Title"}
    result = validate_config(config)
    assert result is True


def test_validate_config_with_warnings():
    """Test validation passes but shows warnings."""
    config = {"artist": "Test", "title": "Test"}
    # Should not raise, but may print warnings
    result = validate_config(config)
    assert result is True


def test_validate_config_invalid_boolean_type():
    """Test validation fails when boolean fields have wrong type."""
    config = {"artist": "Test", "title": "Test", "strict_mode": "true"}
    with pytest.raises(ValueError, match="must be bool"):
        validate_config(config)

