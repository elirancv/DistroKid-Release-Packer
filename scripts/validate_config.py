#!/usr/bin/env python3
"""
JSON schema validation for release.json and artist-defaults.json configuration files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Get logger for validation warnings
logger = logging.getLogger("distrokid_release_packer.validate_config")


def _basic_validation_release(config: Dict) -> Tuple[bool, List[str]]:
    """
    Perform basic validation of release config when jsonschema is unavailable.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields (from release_schema.json)
    required_fields = ["title", "source_audio_dir", "release_dir"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: '{field}'")
        elif not config[field] or (isinstance(config[field], str) and not config[field].strip()):
            errors.append(f"Required field '{field}' cannot be empty")
    
    # Type checks for common fields
    type_checks = {
        "title": str,
        "artist": str,
        "source_audio_dir": str,
        "release_dir": str,
        "bpm": (int, float),
        "explicit": bool,
        "rename_audio": bool,
        "organize_stems": bool,
        "tag_audio": bool,
        "validate_cover": bool,
        "validate_compliance": bool,
        "strict_mode": bool,
        "overwrite_existing": bool,
        "auto_fix_clipping": bool,
    }
    
    for field, expected_type in type_checks.items():
        if field in config:
            if not isinstance(config[field], expected_type):
                errors.append(f"Field '{field}' must be {expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)}")
    
    # BPM range check
    if "bpm" in config and isinstance(config["bpm"], (int, float)):
        if not (1 <= config["bpm"] <= 300):
            errors.append("Field 'bpm' must be integer between 1-300")
    
    # Track number format check
    if "id3_metadata" in config and isinstance(config["id3_metadata"], dict):
        tracknum = config["id3_metadata"].get("tracknumber")
        if tracknum and isinstance(tracknum, str):
            import re
            if not re.match(r'^(\d+|\d+/\d+)$', tracknum):
                errors.append("Field 'id3_metadata.tracknumber' must be format 'X' or 'X/Total'")
    
    return len(errors) == 0, errors


def _basic_validation_artist_defaults(config: Dict) -> Tuple[bool, List[str]]:
    """
    Perform basic validation of artist-defaults config when jsonschema is unavailable.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # All fields in artist-defaults are optional, but if present should be correct type
    type_checks = {
        "default_artist": str,
        "default_publisher": str,
        "default_composer_template": str,
        "default_track_number": str,
        "default_total_tracks": str,
        "default_copyright_template": str,
    }
    
    for field, expected_type in type_checks.items():
        if field in config:
            if not isinstance(config[field], expected_type):
                errors.append(f"Field '{field}' must be {expected_type.__name__}")
    
    return len(errors) == 0, errors


def load_schema(schema_name: str) -> Optional[Dict]:
    """
    Load a JSON schema file.
    
    Args:
        schema_name: Name of schema file (e.g., 'release_schema.json')
    
    Returns:
        Schema dictionary or None if not found
    """
    schema_path = Path(__file__).parent.parent / "schemas" / schema_name
    if not schema_path.exists():
        return None
    
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return None


def validate_release_config(config_path: Path, strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate a release.json configuration file against the schema.
    
    Args:
        config_path: Path to release.json file
        strict: If True, raise ValueError on validation errors instead of returning False
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Raises:
        ValueError: If strict=True and validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        if strict:
            raise ValueError("jsonschema not installed - cannot validate in strict mode")
        # In non-strict mode, perform basic validation and warn
        logger.warning(
            "jsonschema not installed - using basic validation. "
            "Install with: pip install jsonschema for full schema validation"
        )
        # Load config for basic validation
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        except IOError as e:
            return False, [f"Cannot read file: {e}"]
        
        # Perform basic validation
        is_valid, errors = _basic_validation_release(config)
        return is_valid, errors
    
    errors = []
    
    # Load schema
    schema = load_schema("release_schema.json")
    if not schema:
        if strict:
            raise ValueError("Schema file not found - cannot validate in strict mode")
        return True, []  # Skip if schema not found
    
    # Load config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON: {e}"
        if strict:
            raise ValueError(error_msg) from e
        return False, [error_msg]
    except IOError as e:
        error_msg = f"Cannot read file: {e}"
        if strict:
            raise ValueError(error_msg) from e
        return False, [error_msg]
    
    # Validate
    try:
        validator = Draft7Validator(schema)
        errors_list = list(validator.iter_errors(config))
        
        if errors_list:
            for error in errors_list:
                path = ".".join(str(p) for p in error.path)
                if path:
                    errors.append(f"{path}: {error.message}")
                else:
                    errors.append(error.message)
            
            if strict:
                error_msg = "\n".join(f"  - {e}" for e in errors)
                raise ValueError(f"Schema validation failed:\n{error_msg}")
            
            return False, errors
        return True, []
    
    except ValueError:
        raise  # Re-raise ValueError from strict mode
    except Exception as e:
        error_msg = f"Validation error: {e}"
        if strict:
            raise ValueError(error_msg) from e
        return False, [error_msg]


def validate_artist_defaults(config_path: Path, strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate an artist-defaults.json configuration file against the schema.
    
    Args:
        config_path: Path to artist-defaults.json file
        strict: If True, raise ValueError on validation errors instead of returning False
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Raises:
        ValueError: If strict=True and validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        if strict:
            raise ValueError("jsonschema not installed - cannot validate in strict mode")
        # In non-strict mode, perform basic validation and warn
        logger.warning(
            "jsonschema not installed - using basic validation. "
            "Install with: pip install jsonschema for full schema validation"
        )
        # Load config for basic validation
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        except IOError as e:
            return False, [f"Cannot read file: {e}"]
        
        # Perform basic validation
        is_valid, errors = _basic_validation_artist_defaults(config)
        return is_valid, errors
    
    errors = []
    
    # Load schema
    schema = load_schema("artist_defaults_schema.json")
    if not schema:
        if strict:
            raise ValueError("Schema file not found - cannot validate in strict mode")
        return True, []  # Skip if schema not found
    
    # Load config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON: {e}"
        if strict:
            raise ValueError(error_msg) from e
        return False, [error_msg]
    except IOError as e:
        error_msg = f"Cannot read file: {e}"
        if strict:
            raise ValueError(error_msg) from e
        return False, [error_msg]
    
    # Validate
    try:
        validator = Draft7Validator(schema)
        errors_list = list(validator.iter_errors(config))
        
        if errors_list:
            for error in errors_list:
                path = ".".join(str(p) for p in error.path)
                if path:
                    errors.append(f"{path}: {error.message}")
                else:
                    errors.append(error.message)
            
            if strict:
                error_msg = "\n".join(f"  - {e}" for e in errors)
                raise ValueError(f"Schema validation failed:\n{error_msg}")
            
            return False, errors
        return True, []
    
    except ValueError:
        raise  # Re-raise ValueError from strict mode
    except Exception as e:
        error_msg = f"Validation error: {e}"
        if strict:
            raise ValueError(error_msg) from e
        return False, [error_msg]


def validate_config_file(config_path: Path, config_type: str = "release") -> Tuple[bool, List[str]]:
    """
    Validate a configuration file.
    
    Args:
        config_path: Path to configuration file
        config_type: Type of config ('release' or 'artist-defaults')
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    """
    Validate a configuration file.
    
    Args:
        config_path: Path to configuration file
        config_type: Type of config ('release' or 'artist-defaults')
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if config_type == "release":
        return validate_release_config(config_path)
    elif config_type == "artist-defaults":
        return validate_artist_defaults(config_path)
    else:
        return False, [f"Unknown config type: {config_type}"]

