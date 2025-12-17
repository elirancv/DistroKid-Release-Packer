"""
Unit tests for configuration validation functions.
"""

import pytest
from pathlib import Path
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from orchestrator import validate_config
from validate_config import validate_release_config


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


def test_basic_validation_when_jsonschema_missing():
    """Test basic validation works when jsonschema is not installed."""
    config_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            # Create invalid config (missing required field)
            json.dump({"title": "Test"}, f)
            f.flush()
        
        # Close file before patching
        # Mock jsonschema as unavailable
        with patch('validate_config.JSONSCHEMA_AVAILABLE', False):
            is_valid, errors = validate_release_config(config_path, strict=False)
            
            # Should catch missing required field via basic validation
            assert not is_valid
            assert any("source_audio_dir" in str(e).lower() or "required" in str(e).lower() for e in errors)
    finally:
        if config_path and config_path.exists():
            # Retry on Windows if file is locked
            import time
            for _ in range(3):
                try:
                    config_path.unlink()
                    break
                except (PermissionError, OSError):
                    time.sleep(0.1)


def test_basic_validation_catches_type_errors():
    """Test basic validation catches type errors when jsonschema missing."""
    config_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            # Create config with wrong type
            json.dump({
                "title": "Test",
                "source_audio_dir": "./input",
                "release_dir": "./output",
                "bpm": "not a number"  # Should be int/float
            }, f)
            f.flush()
        
        with patch('validate_config.JSONSCHEMA_AVAILABLE', False):
            is_valid, errors = validate_release_config(config_path, strict=False)
            
            # Should catch type error
            assert not is_valid
            assert any("bpm" in str(e).lower() and "int" in str(e).lower() for e in errors)
    finally:
        if config_path and config_path.exists():
            import time
            for _ in range(3):
                try:
                    config_path.unlink()
                    break
                except (PermissionError, OSError):
                    time.sleep(0.1)


def test_basic_validation_catches_empty_required_fields():
    """Test basic validation catches empty required fields."""
    config_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            # Create config with empty required field
            json.dump({
                "title": "",  # Empty
                "source_audio_dir": "./input",
                "release_dir": "./output"
            }, f)
            f.flush()
        
        with patch('validate_config.JSONSCHEMA_AVAILABLE', False):
            is_valid, errors = validate_release_config(config_path, strict=False)
            
            assert not is_valid
            assert any("title" in str(e).lower() and "empty" in str(e).lower() for e in errors)
    finally:
        if config_path and config_path.exists():
            import time
            for _ in range(3):
                try:
                    config_path.unlink()
                    break
                except (PermissionError, OSError):
                    time.sleep(0.1)


def test_strict_mode_raises_when_jsonschema_missing():
    """Test strict mode raises error when jsonschema is missing."""
    config_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            json.dump({"title": "Test", "source_audio_dir": "./input", "release_dir": "./output"}, f)
            f.flush()
        
        with patch('validate_config.JSONSCHEMA_AVAILABLE', False):
            with pytest.raises(ValueError, match="jsonschema not installed"):
                validate_release_config(config_path, strict=True)
    finally:
        if config_path and config_path.exists():
            import time
            for _ in range(3):
                try:
                    config_path.unlink()
                    break
                except (PermissionError, OSError):
                    time.sleep(0.1)


def test_basic_validation_warning_logged():
    """Test that warning is logged when jsonschema is missing."""
    import logging
    config_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
            json.dump({"title": "Test", "source_audio_dir": "./input", "release_dir": "./output"}, f)
            f.flush()
        
        with patch('validate_config.JSONSCHEMA_AVAILABLE', False):
            with patch('validate_config.logger') as mock_logger:
                validate_release_config(config_path, strict=False)
                # Should log warning
                mock_logger.warning.assert_called()
                assert "jsonschema" in str(mock_logger.warning.call_args).lower()
    finally:
        if config_path and config_path.exists():
            import time
            for _ in range(3):
                try:
                    config_path.unlink()
                    break
                except (PermissionError, OSError):
                    time.sleep(0.1)

