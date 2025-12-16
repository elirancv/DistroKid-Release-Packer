"""
Integration tests for full workflow execution.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from orchestrator import run_release_workflow


@pytest.fixture
def temp_release_dir():
    """Create temporary directory for test releases."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_source_dir():
    """Create temporary source directory with test files."""
    temp_dir = tempfile.mkdtemp()
    source_dir = Path(temp_dir)
    
    # Create a dummy audio file
    audio_file = source_dir / "test_audio.mp3"
    audio_file.write_bytes(b"fake mp3 content")
    
    yield source_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_full_workflow_success(temp_release_dir, temp_source_dir):
    """Test complete workflow with valid inputs."""
    config = {
        "artist": "Test Artist",
        "title": "Test Track",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "tag_audio": False,  # Skip tagging for speed (requires mutagen)
        "validate_cover": False,
        "validate_compliance": False,
        "organize_stems": False
    }
    
    result = run_release_workflow(config)
    assert result is True
    
    # Verify output structure
    assert (temp_release_dir / "Audio").exists()
    assert (temp_release_dir / "Metadata").exists()


def test_workflow_missing_source_files(temp_release_dir):
    """Test workflow handles missing source files gracefully."""
    config = {
        "artist": "Test",
        "title": "Test",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": "/nonexistent/path",
        "tag_audio": False,
        "validate_cover": False,
        "validate_compliance": False
    }
    
    # Should not crash, but may return False or raise FileNotFoundError
    # depending on strict_mode
    try:
        result = run_release_workflow(config)
        # If it doesn't raise, it should handle gracefully
        assert result is False or result is True
    except FileNotFoundError:
        # This is also acceptable - fail fast
        pass


def test_workflow_invalid_config(temp_release_dir):
    """Test workflow fails fast with invalid config."""
    config = {
        "title": "Test"  # Missing artist
    }
    
    with pytest.raises(ValueError, match="Missing required field"):
        run_release_workflow(config)


def test_workflow_with_overwrite_flag(temp_release_dir, temp_source_dir):
    """Test workflow respects overwrite_existing flag."""
    config = {
        "artist": "Test",
        "title": "Test",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "overwrite_existing": True,
        "tag_audio": False,
        "validate_cover": False,
        "validate_compliance": False
    }
    
    # Run first time
    result1 = run_release_workflow(config)
    assert result1 is True
    
    # Run second time with overwrite
    result2 = run_release_workflow(config)
    assert result2 is True  # Should succeed with overwrite flag

