"""Pure file utilities - stateless, reusable functions."""

import hashlib
import os
import uuid
from pathlib import Path
from typing import List, Tuple
from loguru import logger


# ==================== FILE VALIDATION ====================


def validate_file_extension(
    filename: str, allowed_extensions: List[str]
) -> Tuple[bool, str]:
    """
    Validate file extension.

    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        return (
            False,
            f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}",
        )

    return True, ""


def validate_file_size(file_size: int, max_size: int) -> Tuple[bool, str]:
    """
    Validate file size.

    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb}MB"

    if file_size == 0:
        return False, "Empty file not allowed"

    return True, ""


def validate_content_type(
    content_type: str, allowed_types: List[str]
) -> Tuple[bool, str]:
    """
    Validate file content type.

    Args:
        content_type: MIME type of the file
        allowed_types: List of allowed MIME types

    Returns:
        Tuple of (is_valid, error_message)
    """
    if content_type not in allowed_types:
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_types)}"

    return True, ""


# ==================== FILE NAMING ====================


def generate_unique_filename(
    original_filename: str, prefix: str = None, include_timestamp: bool = True
) -> str:
    """
    Generate unique filename with optional prefix.

    Args:
        original_filename: Original file name
        prefix: Optional prefix (e.g., user_id)
        include_timestamp: Include timestamp in filename

    Returns:
        Unique filename

    Example:
        >>> generate_unique_filename("photo.jpg", prefix="user123")
        "user123_20250421_153045_a1b2c3d4.jpg"
    """
    file_extension = Path(original_filename).suffix
    random_hex = uuid.uuid4().hex[:8]

    parts = []

    if prefix:
        parts.append(str(prefix))

    if include_timestamp:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parts.append(timestamp)

    parts.append(random_hex)

    filename = "_".join(parts) + file_extension
    return filename


# ==================== DIRECTORY OPERATIONS ====================


def ensure_directory(directory_path: str) -> str:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        directory_path: Path to directory

    Returns:
        Absolute path to directory

    Raises:
        OSError: If directory cannot be created
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.debug(f"Directory ensured: {directory_path}")
        return os.path.abspath(directory_path)
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {str(e)}")
        raise


def is_path_safe(file_path: str, base_directory: str) -> bool:
    """
    Check if file path is safe (prevents path traversal attacks).

    Args:
        file_path: File path to validate
        base_directory: Base directory that file should be within

    Returns:
        True if path is safe, False otherwise
    """
    try:
        base_dir = Path(base_directory).resolve()
        full_path = Path(file_path).resolve()

        # Check if full path starts with base directory
        return str(full_path).startswith(str(base_dir))
    except Exception:
        return False


# ==================== FILE OPERATIONS ====================


def get_file_hash(file_path: str) -> str:
    """
    Generate MD5 hash for file.

    Args:
        file_path: Path to file

    Returns:
        MD5 hash of file contents
    """
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating hash for {file_path}: {str(e)}")
        return ""


def get_relative_path(full_path: str, base_path: str) -> str:
    """
    Get relative path from base path.

    Args:
        full_path: Full file path
        base_path: Base path to calculate relative from

    Returns:
        Relative path

    Example:
        >>> get_relative_path("app/static/uploads/photo.jpg", "app/static")
        "uploads/photo.jpg"
    """
    return str(Path(full_path).relative_to(Path(base_path)))


# ==================== FILE SIZE FORMATTING ====================


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string

    Example:
        >>> format_file_size(1024)
        "1.00 KB"
        >>> format_file_size(1536000)
        "1.46 MB"
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


# ==================== DOCUMENT FINDING (For file_processing_service) ====================


def find_files_by_extension(
    folder_path: str, extensions: List[str] = None
) -> List[str]:
    """
    Find all files with specified extensions in folder.

    Args:
        folder_path: Path to folder
        extensions: List of extensions to search for (e.g., ['.docx', '.pdf'])

    Returns:
        List of file paths
    """
    if extensions is None:
        extensions = [".docx"]

    if not os.path.exists(folder_path):
        logger.error(f"Folder path '{folder_path}' does not exist!")
        return []

    import glob

    all_files = []
    for ext in extensions:
        pattern = os.path.join(folder_path, f"*{ext}")
        files = glob.glob(pattern)
        all_files.extend(files)

    logger.info(f"Found {len(all_files)} files in {folder_path}")
    return all_files
