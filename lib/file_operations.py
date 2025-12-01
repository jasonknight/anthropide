"""
Safe file operations with locking, atomic writes, and backup management.

This module provides thread-safe and process-safe file operations for JSON files,
including atomic writes, file locking, and backup management.
"""

import json
import logging
import platform
import shutil
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Determine platform-specific locking
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import msvcrt
else:
    import fcntl


class FileOperationError(Exception):
    """Base exception for file operation errors."""
    pass


class FileLockError(FileOperationError):
    """Exception raised when file locking fails."""
    pass


class FileReadError(FileOperationError):
    """Exception raised when file reading fails."""
    pass


class FileWriteError(FileOperationError):
    """Exception raised when file writing fails."""
    pass


class BackupError(FileOperationError):
    """Exception raised when backup operations fail."""
    pass


class FileDeleteError(FileOperationError):
    """Exception raised when file deletion fails."""
    pass


@contextmanager
def _file_lock(
    lock_file_path: Path,
    timeout: float = 10.0,
) -> Generator[None, None, None]:
    """
    Cross-platform file locking context manager with timeout.

    Args:
        lock_file_path: Path to the lock file
        timeout: Maximum time to wait for lock (seconds)

    Yields:
        None

    Raises:
        FileLockError: If lock cannot be acquired within timeout
    """
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = None
    try:
        lock_fd = open(lock_file_path, 'w')

        if IS_WINDOWS:
            # Windows-specific locking with retry
            start_time = time.time()
            while True:
                try:
                    msvcrt.locking(
                        lock_fd.fileno(),
                        msvcrt.LK_NBLCK,
                        1,
                    )
                    break  # Lock acquired
                except (OSError, IOError) as e:
                    if time.time() - start_time > timeout:
                        lock_fd.close()
                        raise FileLockError(
                            f"Failed to acquire lock on {lock_file_path} "
                            f"within {timeout}s: {e}",
                        ) from e
                    time.sleep(0.01)  # Wait before retry
        else:
            # Unix-specific locking with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(
                        lock_fd.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB,
                    )
                    break  # Lock acquired
                except BlockingIOError:
                    if time.time() - start_time > timeout:
                        lock_fd.close()
                        raise FileLockError(
                            f"Failed to acquire lock on {lock_file_path} "
                            f"within {timeout}s",
                        )
                    time.sleep(0.01)  # Wait before retry
                except (OSError, IOError) as e:
                    lock_fd.close()
                    raise FileLockError(
                        f"Failed to acquire lock on {lock_file_path}: {e}",
                    ) from e

        try:
            yield
        finally:
            # Release lock
            if IS_WINDOWS:
                try:
                    msvcrt.locking(
                        lock_fd.fileno(),
                        msvcrt.LK_UNLCK,
                        1,
                    )
                except (OSError, IOError):
                    pass
            else:
                try:
                    fcntl.flock(
                        lock_fd.fileno(),
                        fcntl.LOCK_UN,
                    )
                except (OSError, IOError):
                    pass

            if lock_fd:
                lock_fd.close()

    finally:
        # Clean up lock file
        try:
            lock_file_path.unlink(missing_ok=True)
        except (OSError, IOError) as e:
            logger.warning(f"Failed to remove lock file {lock_file_path}: {e}")


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Raises:
        FileOperationError: If directory cannot be created
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path}")
    except (OSError, IOError) as e:
        raise FileOperationError(
            f"Failed to create directory {path}: {e}",
        ) from e


def safe_read_json(
    path: Path,
    default: Optional[Any] = None,
) -> Any:
    """
    Safely read JSON file with error handling.

    Args:
        path: Path to JSON file
        default: Default value to return if file doesn't exist or is empty

    Returns:
        Parsed JSON data, or default value if file doesn't exist

    Raises:
        FileReadError: If file exists but cannot be read or parsed
    """
    path = Path(path)

    # If file doesn't exist, return default
    if not path.exists():
        logger.debug(f"File does not exist, returning default: {path}")
        return default

    # If file is empty, return default
    if path.stat().st_size == 0:
        logger.warning(f"File is empty, returning default: {path}")
        return default

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Successfully read JSON from: {path}")
            return data
    except json.JSONDecodeError as e:
        raise FileReadError(
            f"Failed to parse JSON from {path}: {e}",
        ) from e
    except (OSError, IOError) as e:
        raise FileReadError(
            f"Failed to read file {path}: {e}",
        ) from e


def safe_write_json(
    path: Path,
    data: Any,
    indent: int = 2,
    create_backup: bool = False,
    backup_dir: Optional[Path] = None,
    max_backups: int = 10,
) -> None:
    """
    Safely write JSON file with atomic operations and file locking.

    Uses atomic write (write to temp file, then rename) and file locking
    to prevent data corruption from concurrent writes.

    Args:
        path: Path to JSON file
        data: Data to write (must be JSON-serializable)
        indent: JSON indentation level
        create_backup: Whether to create a backup before writing
        backup_dir: Directory for backups (defaults to path.parent / 'backups')
        max_backups: Maximum number of backups to keep

    Raises:
        FileWriteError: If file cannot be written
    """
    path = Path(path)

    # Ensure parent directory exists
    ensure_directory(path.parent)

    # Create backup if requested and file exists
    if create_backup and path.exists():
        if backup_dir is None:
            backup_dir = path.parent / 'backups'
        try:
            create_backup_file(
                path=path,
                backup_dir=backup_dir,
                max_backups=max_backups,
            )
        except BackupError as e:
            logger.warning(f"Backup creation failed: {e}")

    # Use lock file to prevent concurrent writes
    lock_file = path.with_suffix(path.suffix + '.lock')

    with _file_lock(lock_file):
        # Create temp file in same directory for atomic rename
        temp_fd, temp_path_str = tempfile.mkstemp(
            dir=path.parent,
            prefix=f'.{path.name}.',
            suffix='.tmp',
        )
        temp_path = Path(temp_path_str)

        try:
            # Write to temp file
            with open(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(
                    data,
                    f,
                    indent=indent,
                    ensure_ascii=False,
                )
                f.write('\n')  # Add trailing newline

            # Atomic rename (replaces existing file)
            temp_path.replace(path)
            logger.debug(f"Successfully wrote JSON to: {path}")

        except (OSError, IOError) as e:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            raise FileWriteError(
                f"Failed to write file {path}: {e}",
            ) from e
        except (TypeError, ValueError) as e:
            # Clean up temp file on serialization error
            temp_path.unlink(missing_ok=True)
            raise FileWriteError(
                f"Failed to serialize data to JSON: {e}",
            ) from e


def safe_read_file(
    path: Path,
    encoding: str = 'utf-8',
) -> str:
    """
    Safely read text file with error handling.

    Args:
        path: Path to text file
        encoding: File encoding (default: utf-8)

    Returns:
        File contents as string

    Raises:
        FileReadError: If file cannot be read
    """
    path = Path(path)

    if not path.exists():
        raise FileReadError(f"File does not exist: {path}")

    try:
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
            logger.debug(f"Successfully read file: {path}")
            return content
    except (OSError, IOError) as e:
        raise FileReadError(
            f"Failed to read file {path}: {e}",
        ) from e
    except UnicodeDecodeError as e:
        raise FileReadError(
            f"Failed to decode file {path} with encoding {encoding}: {e}",
        ) from e


def safe_write_file(
    path: Path,
    content: str,
    encoding: str = 'utf-8',
    create_backup: bool = False,
    backup_dir: Optional[Path] = None,
    max_backups: int = 10,
) -> None:
    """
    Safely write text file with atomic operations and file locking.

    Uses atomic write (write to temp file, then rename) and file locking
    to prevent data corruption from concurrent writes.

    Args:
        path: Path to text file
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_backup: Whether to create a backup before writing
        backup_dir: Directory for backups (defaults to path.parent / 'backups')
        max_backups: Maximum number of backups to keep

    Raises:
        FileWriteError: If file cannot be written
    """
    path = Path(path)

    # Ensure parent directory exists
    ensure_directory(path.parent)

    # Create backup if requested and file exists
    if create_backup and path.exists():
        if backup_dir is None:
            backup_dir = path.parent / 'backups'
        try:
            create_backup_file(
                path=path,
                backup_dir=backup_dir,
                max_backups=max_backups,
            )
        except BackupError as e:
            logger.warning(f"Backup creation failed: {e}")

    # Use lock file to prevent concurrent writes
    lock_file = path.with_suffix(path.suffix + '.lock')

    with _file_lock(lock_file):
        # Create temp file in same directory for atomic rename
        temp_fd, temp_path_str = tempfile.mkstemp(
            dir=path.parent,
            prefix=f'.{path.name}.',
            suffix='.tmp',
        )
        temp_path = Path(temp_path_str)

        try:
            # Write to temp file
            with open(temp_fd, 'w', encoding=encoding) as f:
                f.write(content)

            # Atomic rename (replaces existing file)
            temp_path.replace(path)
            logger.debug(f"Successfully wrote file: {path}")

        except (OSError, IOError) as e:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            raise FileWriteError(
                f"Failed to write file {path}: {e}",
            ) from e
        except UnicodeEncodeError as e:
            # Clean up temp file on encoding error
            temp_path.unlink(missing_ok=True)
            raise FileWriteError(
                f"Failed to encode content with {encoding}: {e}",
            ) from e


def safe_delete_file(path: Path) -> None:
    """
    Safely delete a file with error handling.

    Args:
        path: Path to file to delete

    Raises:
        FileDeleteError: If file cannot be deleted
    """
    path = Path(path)

    if not path.exists():
        raise FileDeleteError(f"File does not exist: {path}")

    try:
        path.unlink()
        logger.debug(f"Successfully deleted file: {path}")
    except (OSError, IOError) as e:
        raise FileDeleteError(
            f"Failed to delete file {path}: {e}",
        ) from e


def create_backup_file(
    path: Path,
    backup_dir: Path,
    max_backups: int = 10,
) -> Path:
    """
    Create timestamped backup of a file.

    Args:
        path: Path to file to backup
        backup_dir: Directory to store backups
        max_backups: Maximum number of backups to keep (0 = unlimited)

    Returns:
        Path to created backup file

    Raises:
        BackupError: If backup cannot be created
    """
    path = Path(path)
    backup_dir = Path(backup_dir)

    if not path.exists():
        raise BackupError(f"Cannot backup non-existent file: {path}")

    # Ensure backup directory exists
    ensure_directory(backup_dir)

    # Create timestamped backup filename with microseconds for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_name = f"{path.stem}_{timestamp}{path.suffix}"
    backup_path = backup_dir / backup_name

    try:
        # Copy file to backup location
        shutil.copy2(path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        # Clean up old backups if max_backups is set
        if max_backups > 0:
            _cleanup_old_backups(
                backup_dir=backup_dir,
                file_stem=path.stem,
                file_suffix=path.suffix,
                max_backups=max_backups,
            )

        return backup_path

    except (OSError, IOError) as e:
        raise BackupError(
            f"Failed to create backup of {path}: {e}",
        ) from e


def _cleanup_old_backups(
    backup_dir: Path,
    file_stem: str,
    file_suffix: str,
    max_backups: int,
) -> None:
    """
    Remove old backup files, keeping only the most recent max_backups.

    Args:
        backup_dir: Directory containing backups
        file_stem: Original file stem (name without extension)
        file_suffix: Original file suffix (extension)
        max_backups: Maximum number of backups to keep
    """
    # Find all backup files for this file
    pattern = f"{file_stem}_*{file_suffix}"
    backup_files = sorted(
        backup_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Remove old backups beyond max_backups
    for old_backup in backup_files[max_backups:]:
        try:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup}")
        except (OSError, IOError) as e:
            logger.warning(f"Failed to remove old backup {old_backup}: {e}")


def restore_from_backup(
    target_path: Path,
    backup_path: Path,
) -> None:
    """
    Restore a file from a backup.

    Args:
        target_path: Path where file should be restored
        backup_path: Path to backup file

    Raises:
        BackupError: If restore fails
    """
    target_path = Path(target_path)
    backup_path = Path(backup_path)

    if not backup_path.exists():
        raise BackupError(f"Backup file does not exist: {backup_path}")

    # Ensure target directory exists
    ensure_directory(target_path.parent)

    try:
        # Copy backup to target location
        shutil.copy2(backup_path, target_path)
        logger.info(f"Restored {target_path} from {backup_path}")
    except (OSError, IOError) as e:
        raise BackupError(
            f"Failed to restore {target_path} from {backup_path}: {e}",
        ) from e


def list_backups(
    backup_dir: Path,
    file_stem: str,
    file_suffix: str,
) -> list[Path]:
    """
    List all backup files for a given file, sorted by modification time (newest first).

    Args:
        backup_dir: Directory containing backups
        file_stem: Original file stem (name without extension)
        file_suffix: Original file suffix (extension)

    Returns:
        List of backup file paths, sorted newest to oldest
    """
    backup_dir = Path(backup_dir)

    if not backup_dir.exists():
        return []

    pattern = f"{file_stem}_*{file_suffix}"
    backup_files = sorted(
        backup_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    return backup_files


# Convenience aliases for backward compatibility
create_backup = create_backup_file
