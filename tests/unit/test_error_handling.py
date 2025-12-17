"""
Unit tests for error handling paths.
"""

import pytest
from pathlib import Path
import sys
import tempfile
import json

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from orchestrator import load_config


def test_load_config_malformed_json(tmp_path):
    """Test load_config handles malformed JSON with clear error."""
    config_file = tmp_path / "bad.json"
    config_file.write_text('{"invalid": json}')
    
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(str(config_file))


def test_load_config_missing_file():
    """Test load_config handles missing file."""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config("/nonexistent/path/release.json")


def test_load_config_valid_json(tmp_path):
    """Test load_config loads valid JSON correctly."""
    config_file = tmp_path / "valid.json"
    config_data = {
        "artist": "Test",
        "title": "Test",
        "source_audio_dir": "./runtime/input",
        "release_dir": "./runtime/output"
    }
    config_file.write_text(json.dumps(config_data))
    
    result = load_config(str(config_file))
    assert result["artist"] == config_data["artist"]
    assert result["title"] == config_data["title"]


def test_load_config_unicode_error(tmp_path):
    """Test load_config handles invalid UTF-8 encoding."""
    config_file = tmp_path / "invalid_utf8.json"
    # Write binary data that's not valid UTF-8
    config_file.write_bytes(b'\xff\xfe\x00\x00')
    
    with pytest.raises(ValueError, match="not valid UTF-8"):
        load_config(str(config_file))

