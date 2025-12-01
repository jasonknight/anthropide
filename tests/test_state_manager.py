"""
Comprehensive unit tests for StateManager class.

Tests cover:
- Loading/creating default state
- Saving state
- Getting/setting selected project
- Updating nested UI state values
- Error handling for load/save failures
- Path validation for update_ui_state
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from lib.data_models import UIState
from lib.file_operations import FileOperationError
from lib.state_manager import (
    StateLoadError,
    StateManager,
    StateManagerError,
    StateSaveError,
)


class TestStateManagerInit:
    """Tests for StateManager initialization."""

    def test_init_with_path(self, tmp_path):
        """Test that StateManager initializes with given path."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        assert sm.state_file_path == state_file

    def test_init_converts_string_to_path(self, tmp_path):
        """Test that StateManager converts string path to Path object."""
        state_file_str = str(tmp_path / "state.json")
        sm = StateManager(state_file_str)

        assert isinstance(sm.state_file_path, Path)
        assert str(sm.state_file_path) == state_file_str


class TestLoadState:
    """Tests for loading state."""

    def test_load_state_creates_default_when_missing(self, tmp_path):
        """Test that load_state creates default state if file doesn't exist."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        state = sm.load_state()

        assert isinstance(state, UIState)
        assert state.version == "1.0"
        assert state.selected_project is None
        assert state.ui == {}
        assert isinstance(state.last_modified, datetime)

        # Verify file was created
        assert state_file.exists()

    def test_load_state_reads_existing_file(self, tmp_path):
        """Test that load_state reads existing state file."""
        state_file = tmp_path / "state.json"

        # Create state file with test data
        test_state = {
            "version": "1.0",
            "selected_project": "test-project",
            "ui": {"theme": "dark", "sidebar": {"width": 300}},
            "last_modified": datetime.now().isoformat(),
        }
        state_file.write_text(
            json.dumps(test_state),
            encoding='utf-8',
        )

        sm = StateManager(state_file)
        state = sm.load_state()

        assert state.version == "1.0"
        assert state.selected_project == "test-project"
        assert state.ui == {"theme": "dark", "sidebar": {"width": 300}}
        assert isinstance(state.last_modified, datetime)

    def test_load_state_handles_invalid_json(self, tmp_path):
        """Test that load_state handles invalid JSON gracefully."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            "{invalid json}",
            encoding='utf-8',
        )

        sm = StateManager(state_file)

        with pytest.raises(StateLoadError, match="Failed to read state file"):
            sm.load_state()

    def test_load_state_handles_invalid_structure(self, tmp_path):
        """Test that load_state handles invalid state structure."""
        state_file = tmp_path / "state.json"

        # Create JSON with missing required fields
        invalid_state = {
            "version": "1.0",
            # Missing last_modified field
        }
        state_file.write_text(
            json.dumps(invalid_state),
            encoding='utf-8',
        )

        sm = StateManager(state_file)

        with pytest.raises(StateLoadError, match="Invalid state data"):
            sm.load_state()

    def test_load_state_handles_empty_file(self, tmp_path):
        """Test that load_state handles empty file."""
        state_file = tmp_path / "state.json"
        state_file.write_text("", encoding='utf-8')

        sm = StateManager(state_file)

        # Should create default state
        state = sm.load_state()
        assert state.version == "1.0"
        assert state.selected_project is None

    def test_load_state_with_permission_error(self, tmp_path):
        """Test that load_state handles permission errors."""
        state_file = tmp_path / "state.json"
        state_file.write_text("{}", encoding='utf-8')

        # Make file unreadable
        os.chmod(state_file, 0o000)

        sm = StateManager(state_file)

        try:
            with pytest.raises(StateLoadError):
                sm.load_state()
        finally:
            # Restore permissions for cleanup
            os.chmod(state_file, 0o644)


class TestSaveState:
    """Tests for saving state."""

    def test_save_state_creates_file(self, tmp_path):
        """Test that save_state creates state file."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        state = UIState(
            version="1.0",
            selected_project="test-project",
            ui={"theme": "dark"},
            last_modified=datetime.now(),
        )

        sm.save_state(state)

        assert state_file.exists()

        # Verify content
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert data["selected_project"] == "test-project"
        assert data["ui"] == {"theme": "dark"}
        assert "last_modified" in data

    def test_save_state_updates_last_modified(self, tmp_path):
        """Test that save_state updates last_modified timestamp."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        old_timestamp = datetime(2020, 1, 1, 0, 0, 0)
        state = UIState(
            version="1.0",
            selected_project=None,
            ui={},
            last_modified=old_timestamp,
        )

        sm.save_state(state)

        # Verify timestamp was updated
        assert state.last_modified > old_timestamp

    def test_save_state_overwrites_existing_file(self, tmp_path):
        """Test that save_state overwrites existing file."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Save first state
        state1 = UIState(
            version="1.0",
            selected_project="project1",
            ui={"theme": "light"},
            last_modified=datetime.now(),
        )
        sm.save_state(state1)

        # Save second state
        state2 = UIState(
            version="1.0",
            selected_project="project2",
            ui={"theme": "dark"},
            last_modified=datetime.now(),
        )
        sm.save_state(state2)

        # Verify second state was saved
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["selected_project"] == "project2"
        assert data["ui"] == {"theme": "dark"}

    def test_save_state_with_complex_ui_data(self, tmp_path):
        """Test that save_state handles complex nested UI data."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        state = UIState(
            version="1.0",
            selected_project="test",
            ui={
                "sidebar": {
                    "width": 300,
                    "collapsed": False,
                    "tabs": ["files", "search", "git"],
                },
                "editor": {
                    "fontSize": 14,
                    "theme": "monokai",
                    "minimap": {"enabled": True, "side": "right"},
                },
            },
            last_modified=datetime.now(),
        )

        sm.save_state(state)

        # Load and verify
        loaded = sm.load_state()
        assert loaded.ui == state.ui

    def test_save_state_with_permission_error(self, tmp_path):
        """Test that save_state handles permission errors."""
        state_file = tmp_path / "state.json"

        # Create directory that can't be written to
        state_file.parent.mkdir(exist_ok=True)
        os.chmod(state_file.parent, 0o444)

        sm = StateManager(state_file)
        state = UIState(
            version="1.0",
            selected_project=None,
            ui={},
            last_modified=datetime.now(),
        )

        try:
            with pytest.raises(StateSaveError):
                sm.save_state(state)
        finally:
            # Restore permissions for cleanup
            os.chmod(state_file.parent, 0o755)


class TestGetSelectedProject:
    """Tests for getting selected project."""

    def test_get_selected_project_from_new_state(self, tmp_path):
        """Test getting selected project from newly created state."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        selected = sm.get_selected_project()

        assert selected is None

    def test_get_selected_project_from_existing_state(self, tmp_path):
        """Test getting selected project from existing state."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set a project
        state = UIState(
            version="1.0",
            selected_project="my-project",
            ui={},
            last_modified=datetime.now(),
        )
        sm.save_state(state)

        # Get selected project
        selected = sm.get_selected_project()

        assert selected == "my-project"

    def test_get_selected_project_propagates_load_error(self, tmp_path):
        """Test that get_selected_project propagates StateLoadError."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            "{invalid json}",
            encoding='utf-8',
        )

        sm = StateManager(state_file)

        with pytest.raises(StateLoadError):
            sm.get_selected_project()


class TestSetSelectedProject:
    """Tests for setting selected project."""

    def test_set_selected_project_updates_state(self, tmp_path):
        """Test that set_selected_project updates state."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        sm.set_selected_project("new-project")

        # Verify state was updated
        state = sm.load_state()
        assert state.selected_project == "new-project"

    def test_set_selected_project_to_none(self, tmp_path):
        """Test that set_selected_project can clear selection."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set a project
        sm.set_selected_project("project1")

        # Clear selection
        sm.set_selected_project(None)

        # Verify selection was cleared
        state = sm.load_state()
        assert state.selected_project is None

    def test_set_selected_project_preserves_ui_state(self, tmp_path):
        """Test that set_selected_project preserves UI state."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set up initial state with UI data
        state = UIState(
            version="1.0",
            selected_project="old-project",
            ui={"theme": "dark", "sidebar": {"width": 300}},
            last_modified=datetime.now(),
        )
        sm.save_state(state)

        # Change selected project
        sm.set_selected_project("new-project")

        # Verify UI state was preserved
        updated_state = sm.load_state()
        assert updated_state.selected_project == "new-project"
        assert updated_state.ui == {"theme": "dark", "sidebar": {"width": 300}}

    def test_set_selected_project_propagates_errors(self, tmp_path):
        """Test that set_selected_project propagates load/save errors."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            "{invalid json}",
            encoding='utf-8',
        )

        sm = StateManager(state_file)

        with pytest.raises(StateLoadError):
            sm.set_selected_project("test-project")


class TestUpdateUIState:
    """Tests for updating nested UI state values."""

    def test_update_ui_state_simple_path(self, tmp_path):
        """Test updating a simple top-level UI state value."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        sm.update_ui_state("theme", "dark")

        # Verify state was updated
        state = sm.load_state()
        assert state.ui["theme"] == "dark"

    def test_update_ui_state_nested_path(self, tmp_path):
        """Test updating a nested UI state value."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        sm.update_ui_state("sidebar.width", 350)

        # Verify state was updated
        state = sm.load_state()
        assert state.ui["sidebar"]["width"] == 350

    def test_update_ui_state_deeply_nested_path(self, tmp_path):
        """Test updating a deeply nested UI state value."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        sm.update_ui_state("editor.minimap.side", "left")

        # Verify state was updated
        state = sm.load_state()
        assert state.ui["editor"]["minimap"]["side"] == "left"

    def test_update_ui_state_creates_intermediate_keys(self, tmp_path):
        """Test that update_ui_state creates intermediate keys if needed."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set a deeply nested value without creating intermediate keys first
        sm.update_ui_state("panel.bottom.height", 200)

        # Verify all keys were created
        state = sm.load_state()
        assert state.ui["panel"]["bottom"]["height"] == 200

    def test_update_ui_state_preserves_other_values(self, tmp_path):
        """Test that update_ui_state preserves other UI values."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set up initial state
        sm.update_ui_state("theme", "dark")
        sm.update_ui_state("sidebar.width", 300)

        # Update one value
        sm.update_ui_state("sidebar.collapsed", True)

        # Verify all values are present
        state = sm.load_state()
        assert state.ui["theme"] == "dark"
        assert state.ui["sidebar"]["width"] == 300
        assert state.ui["sidebar"]["collapsed"] is True

    def test_update_ui_state_overwrites_existing_value(self, tmp_path):
        """Test that update_ui_state overwrites existing values."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set initial value
        sm.update_ui_state("fontSize", 12)

        # Update to new value
        sm.update_ui_state("fontSize", 16)

        # Verify value was updated
        state = sm.load_state()
        assert state.ui["fontSize"] == 16

    def test_update_ui_state_with_various_types(self, tmp_path):
        """Test that update_ui_state handles various value types."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Test string
        sm.update_ui_state("string_val", "hello")

        # Test integer
        sm.update_ui_state("int_val", 42)

        # Test float
        sm.update_ui_state("float_val", 3.14)

        # Test boolean
        sm.update_ui_state("bool_val", True)

        # Test list
        sm.update_ui_state("list_val", [1, 2, 3])

        # Test dict
        sm.update_ui_state("dict_val", {"key": "value"})

        # Test null
        sm.update_ui_state("null_val", None)

        # Verify all values
        state = sm.load_state()
        assert state.ui["string_val"] == "hello"
        assert state.ui["int_val"] == 42
        assert state.ui["float_val"] == 3.14
        assert state.ui["bool_val"] is True
        assert state.ui["list_val"] == [1, 2, 3]
        assert state.ui["dict_val"] == {"key": "value"}
        assert state.ui["null_val"] is None

    def test_update_ui_state_empty_path_raises_error(self, tmp_path):
        """Test that update_ui_state raises error for empty path."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        with pytest.raises(ValueError, match="Path cannot be empty"):
            sm.update_ui_state("", "value")

    def test_update_ui_state_non_dict_intermediate_raises_error(self, tmp_path):
        """Test that update_ui_state raises error if intermediate value is not a dict."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set a non-dict value
        sm.update_ui_state("theme", "dark")

        # Try to navigate through it as if it were a dict
        # The implementation wraps ValueError in StateSaveError
        with pytest.raises(StateSaveError, match="is not a dictionary"):
            sm.update_ui_state("theme.mode", "high-contrast")

    def test_update_ui_state_preserves_selected_project(self, tmp_path):
        """Test that update_ui_state preserves selected project."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Set selected project
        sm.set_selected_project("my-project")

        # Update UI state
        sm.update_ui_state("theme", "dark")

        # Verify selected project is preserved
        state = sm.load_state()
        assert state.selected_project == "my-project"
        assert state.ui["theme"] == "dark"

    def test_update_ui_state_propagates_errors(self, tmp_path):
        """Test that update_ui_state propagates load/save errors."""
        state_file = tmp_path / "state.json"
        state_file.write_text(
            "{invalid json}",
            encoding='utf-8',
        )

        sm = StateManager(state_file)

        with pytest.raises(StateLoadError):
            sm.update_ui_state("theme", "dark")


class TestStateManagerEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_multiple_operations_in_sequence(self, tmp_path):
        """Test multiple operations work correctly in sequence."""
        state_file = tmp_path / "state.json"
        sm = StateManager(state_file)

        # Perform multiple operations
        sm.set_selected_project("project1")
        sm.update_ui_state("theme", "dark")
        sm.update_ui_state("sidebar.width", 300)
        sm.set_selected_project("project2")
        sm.update_ui_state("sidebar.collapsed", True)

        # Verify final state
        state = sm.load_state()
        assert state.selected_project == "project2"
        assert state.ui["theme"] == "dark"
        assert state.ui["sidebar"]["width"] == 300
        assert state.ui["sidebar"]["collapsed"] is True

    def test_state_file_path_with_nested_directories(self, tmp_path):
        """Test StateManager works with nested directory paths."""
        nested_dir = tmp_path / "data" / "config"
        state_file = nested_dir / "state.json"

        # Don't create directory - StateManager should handle it
        sm = StateManager(state_file)

        # This should create the directory structure
        sm.set_selected_project("test-project")

        assert state_file.exists()
        assert state_file.parent == nested_dir

    def test_concurrent_modifications_last_write_wins(self, tmp_path):
        """Test that concurrent modifications use last-write-wins."""
        state_file = tmp_path / "state.json"
        sm1 = StateManager(state_file)
        sm2 = StateManager(state_file)

        # Both managers start with same state
        sm1.set_selected_project("project1")

        # Both modify state
        sm1.update_ui_state("theme", "dark")
        sm2.update_ui_state("theme", "light")

        # Last write wins
        final_state = sm1.load_state()
        assert final_state.ui["theme"] == "light"
