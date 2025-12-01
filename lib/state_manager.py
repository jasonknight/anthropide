"""
State management for global UI state.

This module provides the StateManager class for managing the global UI state
stored in state.json at the application root. The state includes the currently
selected project and arbitrary UI state data.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from lib.data_models import UIState
from lib.file_operations import (
    safe_read_json,
    safe_write_json,
    FileOperationError,
)

# Set up logging
logger = logging.getLogger(__name__)


class StateManagerError(Exception):
    """Base exception for state manager errors."""
    pass


class StateLoadError(StateManagerError):
    """Exception raised when state loading fails."""
    pass


class StateSaveError(StateManagerError):
    """Exception raised when state saving fails."""
    pass


class StateManager:
    """
    Manager for global UI state persistence.

    The StateManager handles loading, saving, and updating the global UI state
    stored in state.json at the application root level (not per-project).

    Attributes:
        state_file_path: Path to the state.json file
    """

    def __init__(self, state_file_path: Path):
        """
        Initialize StateManager.

        Args:
            state_file_path: Path to state.json file at application root
        """
        self.state_file_path = Path(state_file_path)
        logger.debug(f"StateManager initialized with path: {self.state_file_path}")

    def load_state(self) -> UIState:
        """
        Load global UI state from state.json.

        Creates a default state file if it doesn't exist.

        Returns:
            UIState object with current state

        Raises:
            StateLoadError: If state cannot be loaded or parsed
        """
        try:
            # Try to read existing state file
            data = safe_read_json(
                self.state_file_path,
                default=None,
            )

            # If no state file exists, create default state
            if data is None:
                logger.info("No state file found, creating default state")
                default_state = UIState(
                    version="1.0",
                    selected_project=None,
                    ui={},
                    last_modified=datetime.now(),
                )

                # Save default state
                try:
                    self.save_state(default_state)
                except StateSaveError as e:
                    logger.warning(f"Failed to save default state: {e}")

                return default_state

            # Parse and validate state data
            try:
                state = UIState(**data)
                logger.debug("Successfully loaded UI state")
                return state
            except Exception as e:
                raise StateLoadError(
                    f"Invalid state data in {self.state_file_path}: {e}",
                ) from e

        except FileOperationError as e:
            raise StateLoadError(
                f"Failed to read state file {self.state_file_path}: {e}",
            ) from e
        except Exception as e:
            raise StateLoadError(
                f"Unexpected error loading state: {e}",
            ) from e

    def save_state(self, state: UIState) -> None:
        """
        Save global UI state to state.json.

        Updates the last_modified timestamp before saving.

        Args:
            state: UIState object to save

        Raises:
            StateSaveError: If state cannot be saved
        """
        try:
            # Update last_modified timestamp
            state.last_modified = datetime.now()

            # Convert to dict for JSON serialization
            state_data = state.model_dump(mode='json')

            # Write to file
            safe_write_json(
                self.state_file_path,
                state_data,
                indent=2,
            )

            logger.info(f"Saved UI state to {self.state_file_path}")

        except FileOperationError as e:
            raise StateSaveError(
                f"Failed to write state file {self.state_file_path}: {e}",
            ) from e
        except Exception as e:
            raise StateSaveError(
                f"Unexpected error saving state: {e}",
            ) from e

    def get_selected_project(self) -> Optional[str]:
        """
        Get the currently selected project name.

        Returns:
            Selected project name, or None if no project is selected

        Raises:
            StateLoadError: If state cannot be loaded
        """
        try:
            state = self.load_state()
            return state.selected_project
        except StateLoadError:
            raise

    def set_selected_project(self, name: Optional[str]) -> None:
        """
        Update the currently selected project.

        Args:
            name: Project name to select, or None to deselect

        Raises:
            StateLoadError: If state cannot be loaded
            StateSaveError: If state cannot be saved
        """
        try:
            state = self.load_state()
            state.selected_project = name
            self.save_state(state)
            logger.info(f"Set selected project to: {name}")
        except (StateLoadError, StateSaveError):
            raise

    def update_ui_state(self, path: str, value: Any) -> None:
        """
        Update a nested UI state value using dot notation path.

        Args:
            path: Dot notation path to the value (e.g., "sidebar.width")
            value: Value to set at the path

        Raises:
            StateLoadError: If state cannot be loaded
            StateSaveError: If state cannot be saved
            ValueError: If path is invalid

        Examples:
            >>> manager.update_ui_state("sidebar.width", 300)
            >>> manager.update_ui_state("theme", "dark")
            >>> manager.update_ui_state("editor.fontSize", 14)
        """
        if not path:
            raise ValueError("Path cannot be empty")

        try:
            state = self.load_state()

            # Split path into parts
            parts = path.split('.')

            # Navigate to the parent of the target location
            current = state.ui
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    raise ValueError(
                        f"Cannot navigate path '{path}': '{part}' is not a dictionary",
                    )
                current = current[part]

            # Set the value at the final key
            final_key = parts[-1]
            current[final_key] = value

            # Save updated state
            self.save_state(state)
            logger.debug(f"Updated UI state at path '{path}' to: {value}")

        except (StateLoadError, StateSaveError):
            raise
        except Exception as e:
            raise StateSaveError(
                f"Failed to update UI state at path '{path}': {e}",
            ) from e
