#!/usr/bin/env python3
"""
Structured logging configuration for DistroKid Release Packer.

Provides centralized logging setup with file and console handlers.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path = None,
    log_to_file: bool = True,
    log_to_console: bool = False,
) -> logging.Logger:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console (usually False, Rich handles console output)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("distrokid_release_packer")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler (rotating, detailed)
    if log_to_file:
        if log_dir is None:
            log_dir = Path("./runtime/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"release_packer_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Console handler (optional, simple format)
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional logger name (default: "distrokid_release_packer")
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"distrokid_release_packer.{name}")
    return logging.getLogger("distrokid_release_packer")


# Initialize default logger
_logger = setup_logging()

