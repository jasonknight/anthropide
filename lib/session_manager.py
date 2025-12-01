"""
Session management for AnthropIDE projects.

This module provides the SessionManager class for loading, saving, and managing
session backups for individual projects. Sessions represent complete Anthropic API
request states including messages, tools, and system prompts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from lib.data_models import Session
from lib.file_operations import (
    safe_read_json,
    safe_write_json,
    FileReadError,
    FileWriteError,
)

# Set up logging
logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """Base exception for session manager errors."""
    pass


class SessionLoadError(SessionManagerError):
    """Exception raised when session loading fails."""
    pass


class SessionSaveError(SessionManagerError):
    """Exception raised when session saving fails."""
    pass


class BackupInfo:
    """
    Information about a session backup file.

    Attributes:
        filename: Name of the backup file
        path: Full path to the backup file
        timestamp: Parsed timestamp from filename
        size: File size in bytes
        created: File creation time
    """

    def __init__(
        self,
        filename: str,
        path: Path,
        timestamp: Optional[datetime],
        size: int,
        created: datetime,
    ):
        self.filename = filename
        self.path = path
        self.timestamp = timestamp
        self.size = size
        self.created = created

    def to_dict(self) -> Dict[str, Any]:
        """Convert BackupInfo to dictionary for JSON serialization."""
        return {
            'filename': self.filename,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'size': self.size,
            'created': self.created.isoformat(),
        }


class SessionManager:
    """
    Manages session loading, saving, and backup operations for a project.

    The SessionManager handles all operations related to the current_session.json
    file and its backups, including:
    - Loading and saving session data
    - Creating timestamped backups before overwrites
    - Listing, restoring, and deleting backups
    - Rotating old backups to maintain storage limits

    Attributes:
        project_path: Path to the project directory
        session_file: Path to current_session.json
    """

    def __init__(self, project_path: Path):
        """
        Initialize SessionManager for a project.

        Args:
            project_path: Path to the project directory

        Raises:
            SessionManagerError: If project path doesn't exist
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise SessionManagerError(
                f"Project directory does not exist: {self.project_path}",
            )

        self.session_file = self.project_path / 'current_session.json'
        logger.debug(f"SessionManager initialized for project: {self.project_path}")

    def load_session(self) -> Optional[Session]:
        """
        Load current session from current_session.json.

        Returns:
            Session object if file exists and is valid JSON, None otherwise.
            Returns None for invalid JSON to allow UI to show raw editor.

        Raises:
            SessionLoadError: If file exists but cannot be read (permission error, etc.)
        """
        if not self.session_file.exists():
            logger.info(f"Session file does not exist: {self.session_file}")
            return None

        try:
            data = safe_read_json(self.session_file, default=None)

            if data is None:
                logger.warning(
                    f"Session file is empty or missing: {self.session_file}",
                )
                return None

            # Try to parse as Session object
            try:
                session = Session(**data)
                logger.info(f"Successfully loaded session from: {self.session_file}")
                return session
            except Exception as e:
                # Invalid session structure - return None to show raw editor
                logger.warning(
                    f"Session data is not valid, returning None for raw editing: {e}",
                )
                return None

        except FileReadError as e:
            # Check if it's a JSONDecodeError specifically
            if 'parse JSON' in str(e):
                logger.warning(
                    f"Invalid JSON in session file, returning None for raw editing: {e}",
                )
                return None
            else:
                # Other read errors (permission, etc.) should raise
                raise SessionLoadError(
                    f"Failed to load session from {self.session_file}: {e}",
                ) from e

    def save_session(self, session: Session) -> None:
        """
        Save session to current_session.json.

        Automatically creates a backup of the existing session before overwriting.

        Args:
            session: Session object to save

        Raises:
            SessionSaveError: If session cannot be saved
        """
        try:
            # Create backup before overwriting if file exists
            if self.session_file.exists():
                try:
                    self.create_backup()
                except Exception as e:
                    # Log backup failure but don't block save
                    logger.warning(
                        f"Failed to create backup before save (continuing anyway): {e}",
                    )

            # Convert session to dict for JSON serialization
            session_dict = session.model_dump(mode='json')

            # Write session atomically
            safe_write_json(
                path=self.session_file,
                data=session_dict,
                indent=2,
            )

            logger.info(f"Successfully saved session to: {self.session_file}")

        except FileWriteError as e:
            raise SessionSaveError(
                f"Failed to save session to {self.session_file}: {e}",
            ) from e
        except Exception as e:
            raise SessionSaveError(
                f"Unexpected error saving session: {e}",
            ) from e

    def create_backup(self) -> Optional[Path]:
        """
        Create timestamped backup of current_session.json.

        Backup filename format: current_session.json.YYYYMMDDHHMMSSFFFFFFF
        where FFFFFFF is microseconds for uniqueness.

        Returns:
            Path to created backup file, or None if current session doesn't exist

        Raises:
            SessionManagerError: If backup creation fails
        """
        if not self.session_file.exists():
            logger.debug("No current session file to backup")
            return None

        try:
            # Create timestamp with microseconds for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            backup_filename = f"current_session.json.{timestamp}"
            backup_path = self.project_path / backup_filename

            # Use shutil.copy2 for atomic backup creation
            # This ensures complete backup or no backup, never partial
            import shutil
            shutil.copy2(self.session_file, backup_path)

            logger.info(f"Created session backup: {backup_path}")

            # Automatically rotate backups to enforce MAX_SESSION_BACKUPS limit
            # This ensures backups don't accumulate indefinitely
            from config import MAX_SESSION_BACKUPS
            try:
                self.rotate_backups(MAX_SESSION_BACKUPS)
            except Exception as e:
                logger.warning(
                    f"Failed to rotate backups after creation: {e}",
                )

            return backup_path

        except (OSError, IOError) as e:
            raise SessionManagerError(
                f"Failed to create backup: {e}",
            ) from e

    def list_backups(self) -> List[BackupInfo]:
        """
        List all session backup files with metadata.

        Returns:
            List of BackupInfo objects sorted by timestamp (newest first)
        """
        backups = []

        # Find all backup files matching pattern
        for backup_path in self.project_path.glob('current_session.json.*'):
            try:
                # Parse timestamp from filename
                timestamp = self._parse_timestamp(backup_path.name)

                # Get file metadata
                stat = backup_path.stat()

                backup_info = BackupInfo(
                    filename=backup_path.name,
                    path=backup_path,
                    timestamp=timestamp,
                    size=stat.st_size,
                    created=datetime.fromtimestamp(stat.st_mtime),
                )
                backups.append(backup_info)

            except Exception as e:
                logger.warning(
                    f"Failed to parse backup file {backup_path.name}: {e}",
                )
                continue

        # Sort by timestamp (newest first)
        backups.sort(
            key=lambda b: b.timestamp if b.timestamp else datetime.min,
            reverse=True,
        )

        logger.debug(f"Found {len(backups)} backup files")
        return backups

    def restore_backup(self, filename: str) -> None:
        """
        Restore a backup as the current session.

        Creates a backup of the current session before restoring.

        Args:
            filename: Name of the backup file to restore

        Raises:
            SessionManagerError: If backup file doesn't exist or restore fails
        """
        backup_path = self.project_path / filename

        if not backup_path.exists():
            raise SessionManagerError(
                f"Backup file does not exist: {filename}",
            )

        try:
            # Create backup of current session if it exists
            if self.session_file.exists():
                try:
                    self.create_backup()
                except Exception as e:
                    logger.warning(
                        f"Failed to backup current session before restore: {e}",
                    )

            # Read backup data
            with open(backup_path, 'r', encoding='utf-8') as src:
                data = src.read()

            # Write as current session
            with open(self.session_file, 'w', encoding='utf-8') as dst:
                dst.write(data)

            logger.info(
                f"Restored session from backup: {filename}",
            )

        except (OSError, IOError) as e:
            raise SessionManagerError(
                f"Failed to restore backup {filename}: {e}",
            ) from e

    def delete_backup(self, filename: str) -> None:
        """
        Delete a backup file.

        Args:
            filename: Name of the backup file to delete

        Raises:
            SessionManagerError: If backup file doesn't exist or deletion fails
        """
        backup_path = self.project_path / filename

        if not backup_path.exists():
            raise SessionManagerError(
                f"Backup file does not exist: {filename}",
            )

        # Verify it's actually a backup file (security check)
        # Check for path traversal attempts and invalid characters
        if ('/' in filename or '\\' in filename or '..' in filename or
            not filename.startswith('current_session.json.')):
            raise SessionManagerError(
                f"Invalid backup filename: {filename}",
            )

        try:
            backup_path.unlink()
            logger.info(f"Deleted backup: {filename}")

        except (OSError, IOError) as e:
            raise SessionManagerError(
                f"Failed to delete backup {filename}: {e}",
            ) from e

    def rotate_backups(self, max_backups: int) -> int:
        """
        Delete old backups beyond the maximum limit.

        Keeps the most recent max_backups files and deletes the rest.

        Args:
            max_backups: Maximum number of backups to keep

        Returns:
            Number of backups deleted

        Raises:
            SessionManagerError: If max_backups is invalid
        """
        if max_backups < 0:
            raise SessionManagerError(
                f"max_backups must be non-negative, got {max_backups}",
            )

        # Get all backups sorted by timestamp
        backups = self.list_backups()

        # Determine which backups to delete
        backups_to_delete = backups[max_backups:]

        deleted_count = 0
        for backup in backups_to_delete:
            try:
                self.delete_backup(backup.filename)
                deleted_count += 1
            except Exception as e:
                logger.warning(
                    f"Failed to delete old backup {backup.filename}: {e}",
                )

        if deleted_count > 0:
            logger.info(
                f"Rotated backups: deleted {deleted_count} old files, "
                f"kept {len(backups) - deleted_count}",
            )

        return deleted_count

    def _parse_timestamp(self, filename: str) -> Optional[datetime]:
        """
        Extract timestamp from backup filename.

        Expected format: current_session.json.YYYYMMDDHHMMSSFFFFFFF
        where FFFFFFF is microseconds.

        Args:
            filename: Backup filename to parse

        Returns:
            Parsed datetime object, or None if parsing fails
        """
        try:
            # Extract timestamp portion after "current_session.json."
            if not filename.startswith('current_session.json.'):
                return None

            timestamp_str = filename[len('current_session.json.'):]

            # Parse timestamp: YYYYMMDDHHMMSSFFFFFFF (20 digits total)
            # Year: 4 digits, Month: 2, Day: 2, Hour: 2, Minute: 2, Second: 2, Microsecond: 6
            if len(timestamp_str) < 14:
                return None

            # Parse without microseconds if not present
            if len(timestamp_str) == 14:
                # Format: YYYYMMDDHHMMSS
                return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            else:
                # Format: YYYYMMDDHHMMSSFFFFFFF (with microseconds)
                return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S%f")

        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse timestamp from {filename}: {e}")
            return None
