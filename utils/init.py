"""
Utility modules for the marketing pipeline.
"""

from utils.logger import get_logger
from utils.files import ensure_directory, ensure_file
from utils.api import safe_request
from utils.markdown import parse_markdown
from utils.slug import generate_slug
from utils.seo import optimize_seo

__all__ = [
    'get_logger',
    'ensure_directory',
    'ensure_file',
    'safe_request',
    'parse_markdown',
    'generate_slug',
    'optimize_seo'
]