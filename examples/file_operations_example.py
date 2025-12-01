"""
Example usage of the safe file operations module.

This script demonstrates how to use the various functions in lib/file_operations.py
for safe, atomic file operations with locking and backup support.
"""

from pathlib import Path
from lib.file_operations import (
    create_backup_file,
    ensure_directory,
    list_backups,
    restore_from_backup,
    safe_read_json,
    safe_write_json,
)


def main():
    """Demonstrate file operations usage."""
    # Create example directories
    project_dir = Path("./example_project")
    data_file = project_dir / "data.json"
    backup_dir = project_dir / "backups"

    ensure_directory(project_dir)

    print("=== Safe File Operations Example ===\n")

    # 1. Write initial data
    print("1. Writing initial data...")
    initial_data = {
        "version": 1,
        "settings": {
            "theme": "dark",
            "language": "en",
        },
        "users": ["alice", "bob"],
    }
    safe_write_json(data_file, initial_data)
    print(f"   Written to: {data_file}\n")

    # 2. Read the data back
    print("2. Reading data...")
    read_data = safe_read_json(data_file)
    print(f"   Version: {read_data['version']}")
    print(f"   Theme: {read_data['settings']['theme']}\n")

    # 3. Update with automatic backup
    print("3. Updating data with backup...")
    updated_data = {
        "version": 2,
        "settings": {
            "theme": "light",
            "language": "en",
        },
        "users": ["alice", "bob", "charlie"],
    }
    safe_write_json(
        data_file,
        updated_data,
        create_backup=True,
        backup_dir=backup_dir,
        max_backups=5,
    )
    print(f"   Updated to version 2\n")

    # 4. List backups
    print("4. Listing backups...")
    backups = list_backups(
        backup_dir=backup_dir,
        file_stem="data",
        file_suffix=".json",
    )
    print(f"   Found {len(backups)} backup(s)")
    for backup in backups:
        print(f"   - {backup.name}")
    print()

    # 5. Make another update with backup
    print("5. Making another update...")
    updated_data["version"] = 3
    updated_data["users"].append("david")
    safe_write_json(
        data_file,
        updated_data,
        create_backup=True,
        backup_dir=backup_dir,
        max_backups=5,
    )
    print(f"   Updated to version 3\n")

    # 6. Restore from backup
    if backups:
        print("6. Restoring from first backup...")
        restore_from_backup(
            target_path=data_file,
            backup_path=backups[0],
        )
        restored_data = safe_read_json(data_file)
        print(f"   Restored to version: {restored_data['version']}\n")

    # 7. Demonstrate handling non-existent files
    print("7. Reading non-existent file with default...")
    non_existent = project_dir / "missing.json"
    default_data = safe_read_json(
        non_existent,
        default={"status": "default"},
    )
    print(f"   Result: {default_data}\n")

    print("=== Example completed successfully ===")


if __name__ == "__main__":
    main()
