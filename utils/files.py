"""
File utility functions for the marketing pipeline.
"""

import os
from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_directory(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists.
    
    Returns:
        The absolute path of the directory.
    """
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        os.makedirs(abs_path, exist_ok=True)
        logger.info(f"Created directory: {abs_path}")
    return abs_path


def ensure_file(filepath: str, default_content: str = "") -> str:
    """
    Ensure a file exists, creating it with default content if necessary.
    
    Args:
        filepath: Path to the file.
        default_content: Content to write if file doesn't exist.
    
    Returns:
        The absolute path of the file.
    """
    abs_path = os.path.abspath(filepath)
    directory = os.path.dirname(abs_path)
    ensure_directory(directory)
    
    if not os.path.exists(abs_path):
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(default_content)
        logger.info(f"Created file: {abs_path}")
    return abs_path
