"""
Validation utilities for the Spotify Downloader application.
Provides secure input validation and sanitization functions.
"""

import re
from urllib.parse import urlparse
import os


def validate_spotify_url(url: str) -> bool:
    """
    Validates if the provided URL is a valid Spotify URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if the URL is a valid Spotify URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Parse the URL to check its structure
    parsed = urlparse(url.strip())
    
    # Check if it's a valid Spotify URL
    if parsed.netloc not in ['open.spotify.com', 'spotify.link']:
        return False
    
    # Check for valid Spotify entity types in the path
    valid_paths = ['/track/', '/playlist/', '/album/', '/artist/']
    path = parsed.path.lower()
    
    return any(path.startswith(valid_path) for valid_path in valid_paths)


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to prevent directory traversal and other security issues.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: A sanitized filename safe for use
    """
    if not filename:
        return ""
    
    # Remove potentially dangerous characters/sequences
    filename = filename.replace('../', '').replace('..\\', '')  # Prevent directory traversal
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)  # Replace invalid Windows chars
    filename = filename.strip()  # Remove leading/trailing whitespace
    
    # Limit length to prevent issues
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length-len(ext)] + ext
    
    return filename


def validate_download_path(base_path: str, sub_path: str = "") -> str:
    """
    Validates and constructs a safe download path.
    
    Args:
        base_path: The base download directory
        sub_path: Optional subdirectory path
        
    Returns:
        str: A validated and safe path
    """
    # Sanitize the sub_path to prevent directory traversal
    if sub_path:
        safe_sub_path = sanitize_filename(sub_path)
        full_path = os.path.join(base_path, safe_sub_path)
    else:
        full_path = base_path
    
    # Resolve the path to get the absolute path
    resolved_path = os.path.abspath(full_path)
    base_abs = os.path.abspath(base_path)
    
    # Ensure the resolved path is within the base path (prevent directory traversal)
    if not resolved_path.startswith(base_abs):
        raise ValueError("Invalid path: Path traversal detected")
    
    return resolved_path


def is_safe_url(url: str) -> bool:
    """
    Checks if a URL is safe to use in the application.
    
    Args:
        url: The URL to check
        
    Returns:
        bool: True if the URL is safe, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL format check
    if not re.match(r'^https?://', url.lower()):
        return False
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Check for potentially dangerous schemes
    if parsed.scheme not in ['http', 'https']:
        return False
    
    # Check for IP addresses that might be internal
    hostname = parsed.hostname
    if hostname:
        # Block localhost and private IPs for security
        if hostname in ['localhost', '127.0.0.1', '::1']:
            return False
        
        # Block private IP ranges (basic check)
        if re.match(r'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)', hostname):
            return False
    
    return True