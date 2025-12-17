"""
Windows-specific path handling tests.

Tests for path operations that may behave differently on Windows vs Unix.
"""

import pytest
from pathlib import Path
import sys

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from orchestrator import sanitize_filename, validate_path_safety

# Skip these tests on non-Windows platforms
pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows-specific tests"
)


class TestWindowsPaths:
    """Test Windows path handling."""
    
    def test_long_paths(self):
        """Test handling of long Windows paths (>260 chars)."""
        # Windows has a 260 character path limit by default
        # This test verifies we handle it gracefully
        long_path = Path("C:\\" + "a" * 250 + "\\file.txt")
        
        # Should not raise on path creation
        assert long_path.parts[0] == "C:\\"
        assert len(str(long_path)) > 260
    
    def test_path_separators(self):
        """Test that path operations work with Windows separators."""
        # Test forward slashes (should work on Windows too)
        path1 = Path("C:/Users/Test/file.txt")
        assert path1.parts[-1] == "file.txt"
        
        # Test backslashes
        path2 = Path("C:\\Users\\Test\\file.txt")
        assert path2.parts[-1] == "file.txt"
        
        # Test mixed (should normalize)
        path3 = Path("C:/Users\\Test/file.txt")
        assert path3.parts[-1] == "file.txt"
    
    def test_unc_paths(self):
        """Test UNC (network) path handling."""
        # UNC paths: \\server\share\path
        # On Windows, Path normalizes UNC paths differently
        unc_path = Path("\\\\server\\share\\file.txt")
        # The first part contains the server and share
        assert len(unc_path.parts) > 0
        # Check that it's a UNC path (starts with \\)
        assert str(unc_path).startswith("\\\\") or unc_path.parts[0].startswith("\\\\")
    
    def test_drive_letters(self):
        """Test drive letter handling."""
        path = Path("C:\\Users\\file.txt")
        assert path.drive == "C:"
        
        # Relative paths have no drive
        rel_path = Path("Users\\file.txt")
        assert rel_path.drive == ""
    
    def test_case_insensitive_comparison(self):
        """Test case-insensitive path comparison on Windows."""
        path1 = Path("C:\\Users\\FILE.TXT")
        path2 = Path("C:\\Users\\file.txt")
        
        # On Windows, these should be considered equal
        # Note: Path comparison is case-sensitive in Python, but filesystem is not
        assert str(path1).lower() == str(path2).lower()


class TestWindowsFileOperations:
    """Test Windows-specific file operations."""
    
    def test_reserved_names_sanitized(self):
        """Test that Windows reserved filenames are sanitized correctly."""
        # Windows reserves: CON, PRN, AUX, NUL, COM1-9, LPT1-9
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM9", "LPT1", "LPT9"]
        
        for name in reserved_names:
            # Should be prefixed with underscore
            sanitized = sanitize_filename(name)
            assert sanitized.startswith("_"), f"Reserved name '{name}' should be prefixed with underscore, got '{sanitized}'"
            assert sanitized == f"_{name}", f"Expected '_{name}', got '{sanitized}'"
    
    def test_reserved_names_with_extension(self):
        """Test reserved names with extensions are handled correctly."""
        test_cases = [
            ("CON.mp3", "_CON.mp3"),
            ("PRN.wav", "_PRN.wav"),
            ("COM1.txt", "_COM1.txt"),
        ]
        
        for input_name, expected in test_cases:
            sanitized = sanitize_filename(input_name)
            # Should preserve extension but prefix base name
            assert sanitized == expected, f"Expected '{expected}', got '{sanitized}'"
    
    def test_non_reserved_names_unchanged(self):
        """Test that non-reserved names are not modified."""
        normal_names = ["MyTrack", "Artist - Title", "Song123"]
        
        for name in normal_names:
            sanitized = sanitize_filename(name)
            # Should not be prefixed (unless it happens to match reserved after sanitization)
            # But normal names should not be prefixed
            assert not sanitized.startswith("_") or name.upper() in ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    
    def test_invalid_chars_sanitized(self):
        """Test that invalid Windows filename characters are sanitized."""
        # Windows invalid chars: < > : " | ? * \
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\']
        
        for char in invalid_chars:
            test_name = f"file{char}name"
            sanitized = sanitize_filename(test_name)
            # Should not contain invalid character
            assert char not in sanitized, f"Invalid char '{char}' should be removed from '{test_name}', got '{sanitized}'"
            # Should be replaced with underscore
            assert "_" in sanitized or sanitized == "filenamename", f"Expected sanitization of '{test_name}'"
    
    def test_path_traversal_prevented(self):
        """Test that path traversal is prevented."""
        # Paths with .. should raise error
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            validate_path_safety("../../etc/passwd")
        
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            validate_path_safety("./../other/dir")
        
        # Valid paths should pass
        valid_path = validate_path_safety("./runtime/output")
        assert isinstance(valid_path, Path)
    
    def test_path_outside_base_dir_rejected(self):
        """Test that paths outside base directory are rejected."""
        base_dir = "C:\\Users\\Test\\runtime"
        
        # Path outside base should fail
        with pytest.raises(ValueError, match="outside allowed directory"):
            validate_path_safety("C:\\Users\\Other", base_dir=base_dir)
        
        # Path inside base should pass
        valid_path = validate_path_safety("C:\\Users\\Test\\runtime\\output", base_dir=base_dir)
        assert isinstance(valid_path, Path)

