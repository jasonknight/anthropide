"""
Tests for safe file operations module.
"""

import json
import tempfile
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from lib.file_operations import (
    BackupError,
    FileOperationError,
    FileReadError,
    FileWriteError,
    create_backup_file,
    ensure_directory,
    list_backups,
    restore_from_backup,
    safe_read_json,
    safe_write_json,
)


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "test" / "nested" / "dir"
        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test with existing directory (should not raise)."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        ensure_directory(existing_dir)
        assert existing_dir.exists()


class TestSafeReadJson:
    """Tests for safe_read_json function."""

    def test_read_valid_json(self, tmp_path):
        """Test reading valid JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}

        test_file.write_text(json.dumps(test_data))

        result = safe_read_json(test_file)
        assert result == test_data

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading non-existent file returns default."""
        test_file = tmp_path / "nonexistent.json"

        result = safe_read_json(test_file, default={"default": True})
        assert result == {"default": True}

    def test_read_empty_file(self, tmp_path):
        """Test reading empty file returns default."""
        test_file = tmp_path / "empty.json"
        test_file.write_text("")

        result = safe_read_json(test_file, default=None)
        assert result is None

    def test_read_invalid_json(self, tmp_path):
        """Test reading invalid JSON raises FileReadError."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")

        with pytest.raises(FileReadError):
            safe_read_json(test_file)


class TestSafeWriteJson:
    """Tests for safe_write_json function."""

    def test_write_simple_data(self, tmp_path):
        """Test writing simple JSON data."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "list": [1, 2, 3]}

        safe_write_json(test_file, test_data)

        assert test_file.exists()
        result = json.loads(test_file.read_text())
        assert result == test_data

    def test_write_with_indentation(self, tmp_path):
        """Test writing with custom indentation."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}

        safe_write_json(test_file, test_data, indent=4)

        content = test_file.read_text()
        assert "    " in content  # 4-space indentation

    def test_write_creates_directory(self, tmp_path):
        """Test that write creates parent directories."""
        test_file = tmp_path / "nested" / "dir" / "test.json"
        test_data = {"key": "value"}

        safe_write_json(test_file, test_data)

        assert test_file.exists()
        assert test_file.parent.exists()

    def test_write_with_backup(self, tmp_path):
        """Test writing with backup creation."""
        test_file = tmp_path / "test.json"
        backup_dir = tmp_path / "backups"

        # Write initial data
        initial_data = {"version": 1}
        safe_write_json(test_file, initial_data)

        # Write with backup
        new_data = {"version": 2}
        safe_write_json(
            test_file,
            new_data,
            create_backup=True,
            backup_dir=backup_dir,
        )

        # Check backup was created
        backups = list(backup_dir.glob("test_*.json"))
        assert len(backups) == 1

        # Check backup contains old data
        backup_data = json.loads(backups[0].read_text())
        assert backup_data == initial_data

        # Check file has new data
        current_data = json.loads(test_file.read_text())
        assert current_data == new_data

    def test_atomic_write(self, tmp_path):
        """Test that writes are atomic (file always has valid content)."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}

        safe_write_json(test_file, test_data)

        # Verify no temp files left behind
        temp_files = list(tmp_path.glob(".test.json.*.tmp"))
        assert len(temp_files) == 0

    def test_concurrent_writes(self, tmp_path):
        """Test that concurrent writes don't corrupt file."""
        test_file = tmp_path / "test.json"

        def write_data(i):
            data = {"writer": i, "data": list(range(i))}
            safe_write_json(test_file, data)

        # Execute concurrent writes
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(write_data, range(10)))

        # File should still be valid JSON
        result = safe_read_json(test_file)
        assert isinstance(result, dict)
        assert "writer" in result


class TestBackupOperations:
    """Tests for backup-related functions."""

    def test_create_backup(self, tmp_path):
        """Test creating a backup file."""
        test_file = tmp_path / "test.json"
        backup_dir = tmp_path / "backups"
        test_data = {"key": "value"}

        test_file.write_text(json.dumps(test_data))

        backup_path = create_backup_file(
            path=test_file,
            backup_dir=backup_dir,
            max_backups=10,
        )

        assert backup_path.exists()
        assert backup_path.parent == backup_dir
        assert backup_path.stem.startswith("test_")

        # Verify backup content
        backup_data = json.loads(backup_path.read_text())
        assert backup_data == test_data

    def test_backup_nonexistent_file(self, tmp_path):
        """Test backing up non-existent file raises error."""
        test_file = tmp_path / "nonexistent.json"
        backup_dir = tmp_path / "backups"

        with pytest.raises(BackupError):
            create_backup_file(
                path=test_file,
                backup_dir=backup_dir,
            )

    def test_max_backups_cleanup(self, tmp_path):
        """Test that old backups are removed when max_backups is exceeded."""
        test_file = tmp_path / "test.json"
        backup_dir = tmp_path / "backups"
        max_backups = 3

        test_file.write_text(json.dumps({"version": 0}))

        # Create multiple backups
        for i in range(5):
            test_file.write_text(json.dumps({"version": i}))
            create_backup_file(
                path=test_file,
                backup_dir=backup_dir,
                max_backups=max_backups,
            )
            time.sleep(0.01)  # Ensure different timestamps

        # Should only have max_backups files
        backups = list(backup_dir.glob("test_*.json"))
        assert len(backups) == max_backups

    def test_list_backups(self, tmp_path):
        """Test listing backup files."""
        test_file = tmp_path / "test.json"
        backup_dir = tmp_path / "backups"

        test_file.write_text(json.dumps({"version": 0}))

        # Create multiple backups
        for i in range(3):
            test_file.write_text(json.dumps({"version": i}))
            create_backup_file(
                path=test_file,
                backup_dir=backup_dir,
            )
            time.sleep(0.01)

        backups = list_backups(
            backup_dir=backup_dir,
            file_stem="test",
            file_suffix=".json",
        )

        assert len(backups) == 3
        # Should be sorted newest first
        assert backups[0].stat().st_mtime >= backups[1].stat().st_mtime

    def test_restore_from_backup(self, tmp_path):
        """Test restoring a file from backup."""
        test_file = tmp_path / "test.json"
        backup_dir = tmp_path / "backups"

        # Create original and backup
        original_data = {"version": 1}
        test_file.write_text(json.dumps(original_data))

        backup_path = create_backup_file(
            path=test_file,
            backup_dir=backup_dir,
        )

        # Modify original
        test_file.write_text(json.dumps({"version": 2}))

        # Restore from backup
        restore_from_backup(
            target_path=test_file,
            backup_path=backup_path,
        )

        # Check restored data
        restored_data = json.loads(test_file.read_text())
        assert restored_data == original_data

    def test_restore_nonexistent_backup(self, tmp_path):
        """Test restoring from non-existent backup raises error."""
        test_file = tmp_path / "test.json"
        backup_path = tmp_path / "backups" / "nonexistent.json"

        with pytest.raises(BackupError):
            restore_from_backup(
                target_path=test_file,
                backup_path=backup_path,
            )


class TestFileLocking:
    """Tests for file locking mechanism."""

    def test_lock_prevents_concurrent_access(self, tmp_path):
        """Test that file locking prevents concurrent writes from corrupting data."""
        test_file = tmp_path / "test.json"
        results = []

        def write_sequential_data(writer_id):
            """Write a sequence of numbers to test atomicity."""
            data = {"writer": writer_id, "sequence": list(range(100))}
            safe_write_json(test_file, data)
            results.append(writer_id)

        # Run concurrent writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(write_sequential_data, range(20)))

        # Verify final file is valid and complete
        final_data = safe_read_json(test_file)
        assert isinstance(final_data, dict)
        assert "writer" in final_data
        assert "sequence" in final_data
        assert len(final_data["sequence"]) == 100
        assert final_data["sequence"] == list(range(100))

        # All writes should have completed
        assert len(results) == 20
