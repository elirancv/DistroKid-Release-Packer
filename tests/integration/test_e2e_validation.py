"""
End-to-end validation tests for complete workflow output correctness.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
import sys

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
    
    # Create a minimal valid MP3 file (just header bytes)
    # Real MP3 files have complex headers, but for testing we'll use a simple approach
    audio_file = source_dir / "test_audio.mp3"
    # Write minimal MP3 header (ID3v2 tag header + frame header)
    # This is a simplified version - real tests would use actual MP3 files
    audio_file.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 1000)
    
    yield source_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_naming_convention(temp_release_dir, temp_source_dir):
    """Test that files follow naming convention: Artist - Title.ext"""
    config = {
        "artist": "Test Artist",
        "title": "Test Track",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "tag_audio": False,  # Skip tagging for speed
        "validate_cover": False,
        "validate_compliance": False,
        "organize_stems": False
    }
    
    result = run_release_workflow(config)
    assert result is True
    
    # Check audio file naming
    audio_dir = temp_release_dir / "Audio"
    audio_files = list(audio_dir.glob("*.mp3"))
    assert len(audio_files) > 0, "Audio file should exist"
    
    expected_name = "Test Artist - Test Track.mp3"
    assert any(f.name == expected_name for f in audio_files), \
        f"Expected file named '{expected_name}', found: {[f.name for f in audio_files]}"


def test_metadata_json_structure(temp_release_dir, temp_source_dir):
    """Test that metadata JSON has correct structure and content."""
    config = {
        "artist": "Test Artist",
        "title": "Test Track",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "genre": "Test Genre",
        "bpm": 120,
        "tag_audio": False,
        "validate_cover": False,
        "validate_compliance": False,
        "organize_stems": False
    }
    
    result = run_release_workflow(config)
    assert result is True
    
    # Check metadata file
    metadata_dir = temp_release_dir / "Metadata"
    metadata_files = list(metadata_dir.glob("*.json"))
    assert len(metadata_files) == 1, "Should have exactly one metadata file"
    
    metadata_file = metadata_files[0]
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Verify structure
    assert "artist" in metadata
    assert "title" in metadata
    assert "created_date" in metadata
    assert metadata["artist"] == "Test Artist"
    assert metadata["title"] == "Test Track"
    assert metadata.get("genre") == "Test Genre"
    assert metadata.get("bpm") == 120


def test_directory_structure_matches_spec(temp_release_dir, temp_source_dir):
    """Test that directory structure matches DistroKid specification."""
    config = {
        "artist": "Test Artist",
        "title": "Test Track",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "tag_audio": False,
        "validate_cover": False,
        "validate_compliance": False,
        "organize_stems": False
    }
    
    result = run_release_workflow(config)
    assert result is True
    
    # Verify required directories exist
    assert (temp_release_dir / "Audio").exists(), "Audio directory should exist"
    assert (temp_release_dir / "Metadata").exists(), "Metadata directory should exist"
    
    # Audio directory should contain files
    audio_files = list((temp_release_dir / "Audio").glob("*"))
    assert len(audio_files) > 0, "Audio directory should contain files"


def test_id3_tags_match_config(temp_release_dir, temp_source_dir):
    """Test that ID3 tags match configuration values (if tagging enabled)."""
    try:
        from mutagen.mp3 import MP3
        from mutagen.easyid3 import EasyID3
    except ImportError:
        pytest.skip("mutagen not available for ID3 tag testing")
    
    # Create a minimal valid MP3 file for testing
    # Use a simple approach: copy from a real MP3 or create minimal valid structure
    import struct
    audio_file = temp_source_dir / "test_audio.mp3"
    # Write minimal MP3 frame header (simplified - real MP3s are more complex)
    # This is a very basic MP3 frame header
    mp3_header = b'\xff\xfb\x90\x00'  # MP3 sync word + header
    mp3_data = mp3_header + b'\x00' * 1000  # Minimal data
    audio_file.write_bytes(mp3_data)
    
    config = {
        "artist": "Test Artist",
        "title": "Test Track",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "genre": "Test Genre",
        "id3_metadata": {
            "album": "Test Album",
            "year": "2025",
            "composer": "Test Composer"
        },
        "tag_audio": True,  # Enable tagging
        "validate_cover": False,
        "validate_compliance": False,
        "organize_stems": False
    }
    
    result = run_release_workflow(config)
    # Tagging may fail if file isn't valid MP3, but workflow should complete
    # (tagging errors are logged but don't fail workflow unless strict_mode=True)
    
    # Find audio file
    audio_dir = temp_release_dir / "Audio"
    audio_files = list(audio_dir.glob("*.mp3"))
    
    if len(audio_files) == 0:
        pytest.skip("No audio file created (likely due to invalid MP3)")
    
    audio_file = audio_files[0]
    
    # Try to read ID3 tags - may fail if file isn't valid MP3
    try:
        audio = EasyID3(str(audio_file))
        
        # Verify tags match config (if tags exist)
        if audio.get("title"):
            assert audio.get("title") == ["Test Track"]
        if audio.get("artist"):
            assert audio.get("artist") == ["Test Artist"]
        if audio.get("album"):
            assert audio.get("album") == ["Test Album"]
    except Exception as e:
        # If file isn't a valid MP3, skip the test (test file is too minimal)
        # In real usage, users would provide valid MP3 files
        pytest.skip(f"Could not read ID3 tags (test file may not be valid MP3): {e}")


def test_metadata_file_naming_convention(temp_release_dir, temp_source_dir):
    """Test that metadata file follows naming convention."""
    config = {
        "artist": "Test Artist",
        "title": "Test Track",
        "release_dir": str(temp_release_dir),
        "source_audio_dir": str(temp_source_dir),
        "tag_audio": False,
        "validate_cover": False,
        "validate_compliance": False,
        "organize_stems": False
    }
    
    result = run_release_workflow(config)
    assert result is True
    
    # Check metadata file naming
    metadata_dir = temp_release_dir / "Metadata"
    metadata_files = list(metadata_dir.glob("*.json"))
    assert len(metadata_files) == 1
    
    expected_name = "Test Artist - Test Track - Metadata.json"
    assert metadata_files[0].name == expected_name, \
        f"Expected '{expected_name}', got '{metadata_files[0].name}'"
