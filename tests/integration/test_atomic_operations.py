"""
Integration tests for atomic file operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from rename_audio_files import rename_audio_files


@pytest.fixture
def temp_source_dir():
    """Create temporary source directory with test files."""
    temp_dir = tempfile.mkdtemp()
    source_dir = Path(temp_dir)
    
    # Create a small test audio file
    audio_file = source_dir / "test_audio.mp3"
    audio_file.write_bytes(b"fake mp3 content" * 100)  # Small test file
    
    yield source_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_dest_dir():
    """Create temporary destination directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_appears_atomically(temp_source_dir, temp_dest_dir):
    """Test that file appears atomically (not partially written)."""
    artist = "Test Artist"
    title = "Test Track"
    
    # Rename file
    rename_audio_files(artist, title, str(temp_source_dir), str(temp_dest_dir))
    
    # File should exist at final location
    expected_file = temp_dest_dir / f"{artist} - {title}.mp3"
    assert expected_file.exists(), "File should exist at final location"
    
    # Temp file should not exist
    temp_files = list(temp_dest_dir.glob("*.tmp"))
    assert len(temp_files) == 0, f"Temp files should be cleaned up: {temp_files}"


def test_temp_file_cleanup_on_failure(temp_source_dir, temp_dest_dir):
    """Test that temp files are cleaned up on failure."""
    artist = "Test Artist"
    title = "Test Track"
    
    # Make destination read-only to cause failure
    temp_dest_dir.chmod(0o444)
    
    try:
        with pytest.raises(Exception):
            rename_audio_files(artist, title, str(temp_source_dir), str(temp_dest_dir))
        
        # Temp files should be cleaned up even on failure
        temp_files = list(temp_dest_dir.glob("*.tmp"))
        assert len(temp_files) == 0, f"Temp files should be cleaned up on failure: {temp_files}"
    finally:
        # Restore permissions for cleanup
        temp_dest_dir.chmod(0o755)


def test_final_file_only_after_successful_write(temp_source_dir, temp_dest_dir):
    """Test that final file only exists after successful write."""
    artist = "Test Artist"
    title = "Test Track"
    
    expected_file = temp_dest_dir / f"{artist} - {title}.mp3"
    
    # File should not exist before operation
    assert not expected_file.exists()
    
    # Perform operation
    rename_audio_files(artist, title, str(temp_source_dir), str(temp_dest_dir))
    
    # File should exist after successful operation
    assert expected_file.exists()
    
    # Verify content is correct
    assert expected_file.read_bytes() == (temp_source_dir / "test_audio.mp3").read_bytes()


def test_no_partial_files_on_failure(temp_source_dir, temp_dest_dir):
    """Test that partial files don't remain on failure."""
    artist = "Test Artist"
    title = "Test Track"
    
    expected_file = temp_dest_dir / f"{artist} - {title}.mp3"
    
    # Create a file that will cause permission error
    temp_dest_dir.chmod(0o444)
    
    try:
        with pytest.raises(Exception):
            rename_audio_files(artist, title, str(temp_source_dir), str(temp_dest_dir))
        
        # Final file should not exist (operation failed)
        assert not expected_file.exists(), "Final file should not exist after failure"
        
        # No temp files should remain
        temp_files = list(temp_dest_dir.glob("*.tmp"))
        assert len(temp_files) == 0, f"No temp files should remain: {temp_files}"
    finally:
        temp_dest_dir.chmod(0o755)


def test_atomic_rename_preserves_file_content(temp_source_dir, temp_dest_dir):
    """Test that atomic rename preserves file content correctly."""
    artist = "Test Artist"
    title = "Test Track"
    
    source_file = temp_source_dir / "test_audio.mp3"
    original_content = source_file.read_bytes()
    
    # Perform rename
    rename_audio_files(artist, title, str(temp_source_dir), str(temp_dest_dir))
    
    # Verify content matches
    dest_file = temp_dest_dir / f"{artist} - {title}.mp3"
    assert dest_file.read_bytes() == original_content
