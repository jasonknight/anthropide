"""
Test configuration manager for AnthropIDE.

This module provides functionality for loading, saving, and validating
test configurations stored in a project's tests/config.json file. Test
configurations are used in simulation mode to provide canned responses
for testing without making real API calls.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from pydantic import ValidationError

from lib.data_models import TestConfig, TestCase

logger = logging.getLogger(__name__)


class TestConfigManager:
    """
    Manages test configuration for a project.

    Handles loading, saving, and validating test configuration files that
    define sequences of API request patterns and canned responses for
    simulation mode testing.

    Attributes:
        project_path: Path to the project directory
        config_path: Path to the tests/config.json file
    """

    def __init__(self, project_path: Path):
        """
        Initialize the TestConfigManager.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.tests_dir = self.project_path / "tests"
        self.config_path = self.tests_dir / "config.json"

        logger.debug(
            f"Initialized TestConfigManager for project at {self.project_path}",
        )

    def load_test_config(self) -> TestConfig:
        """
        Load the test configuration from tests/config.json.

        If the config file does not exist, creates a default empty configuration.

        Returns:
            TestConfig: Validated test configuration

        Raises:
            FileNotFoundError: If the tests directory does not exist
            ValueError: If the config file contains invalid JSON
            ValidationError: If the config structure is invalid
        """
        # Check if tests directory exists
        if not self.tests_dir.exists():
            raise FileNotFoundError(
                f"Tests directory not found: {self.tests_dir}",
            )

        # If config file doesn't exist, create default
        if not self.config_path.exists():
            logger.info(
                f"Test config not found at {self.config_path}, creating default",
            )
            default_config = TestConfig(tests=[])
            self.save_test_config(default_config)
            return default_config

        # Load and parse JSON
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in test config file {self.config_path}: {e}",
            ) from e
        except Exception as e:
            raise ValueError(
                f"Error reading test config file {self.config_path}: {e}",
            ) from e

        # Validate with Pydantic model
        try:
            config = TestConfig(**data)
            logger.debug(
                f"Loaded test config with {len(config.tests)} test(s)",
            )
            return config
        except ValidationError as e:
            logger.error(
                f"Invalid test configuration structure: {e}",
            )
            raise

    def save_test_config(self, config: TestConfig) -> None:
        """
        Save test configuration to tests/config.json.

        Validates the configuration before saving and creates the tests
        directory if it doesn't exist.

        Args:
            config: Test configuration to save

        Raises:
            ValidationError: If the config structure is invalid
            OSError: If unable to write the file
        """
        # Validate config
        try:
            self.validate_config(config)
        except ValidationError as e:
            logger.error(
                f"Cannot save invalid test configuration: {e}",
            )
            raise

        # Create tests directory if it doesn't exist
        self.tests_dir.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save
        try:
            data = config.model_dump()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            logger.info(
                f"Saved test config with {len(config.tests)} test(s) to {self.config_path}",
            )
        except Exception as e:
            raise OSError(
                f"Error writing test config file {self.config_path}: {e}",
            ) from e

    def get_test(self, test_name: str) -> Optional[TestCase]:
        """
        Get a specific test case by name.

        Args:
            test_name: Name of the test case to retrieve

        Returns:
            TestCase if found, None otherwise

        Raises:
            FileNotFoundError: If the tests directory does not exist
            ValueError: If the config file contains invalid JSON or structure
        """
        config = self.load_test_config()

        for test in config.tests:
            if test.name == test_name:
                logger.debug(
                    f"Found test '{test_name}' with {len(test.sequence)} sequence item(s)",
                )
                return test

        logger.debug(
            f"Test '{test_name}' not found",
        )
        return None

    def list_tests(self) -> List[str]:
        """
        Get a list of all test case names.

        Returns:
            List of test case names

        Raises:
            FileNotFoundError: If the tests directory does not exist
            ValueError: If the config file contains invalid JSON or structure
        """
        config = self.load_test_config()
        test_names = [test.name for test in config.tests]

        logger.debug(
            f"Found {len(test_names)} test(s): {test_names}",
        )
        return test_names

    def validate_config(self, config: TestConfig) -> None:
        """
        Validate test configuration structure.

        Performs validation using the Pydantic TestConfig model, which
        ensures all required fields are present and properly structured
        according to the specification.

        Args:
            config: Test configuration to validate

        Raises:
            ValidationError: If the config structure is invalid
        """
        # Pydantic will validate on construction
        # This method provides an explicit validation interface
        try:
            # Re-validate by reconstructing from dict
            data = config.model_dump()
            TestConfig(**data)
            logger.debug(
                f"Test config validation passed for {len(config.tests)} test(s)",
            )
        except ValidationError as e:
            logger.error(
                f"Test config validation failed: {e}",
            )
            raise

    def add_test(self, test: TestCase) -> None:
        """
        Add a new test case to the configuration.

        If a test with the same name exists, it will be replaced.

        Args:
            test: Test case to add

        Raises:
            FileNotFoundError: If the tests directory does not exist
            ValueError: If the config file contains invalid JSON or structure
            ValidationError: If the test case is invalid
            OSError: If unable to write the file
        """
        config = self.load_test_config()

        # Remove existing test with same name if present
        config.tests = [t for t in config.tests if t.name != test.name]

        # Add new test
        config.tests.append(test)

        # Save updated config
        self.save_test_config(config)
        logger.info(
            f"Added test '{test.name}' to config",
        )

    def remove_test(self, test_name: str) -> bool:
        """
        Remove a test case by name.

        Args:
            test_name: Name of the test case to remove

        Returns:
            True if test was found and removed, False otherwise

        Raises:
            FileNotFoundError: If the tests directory does not exist
            ValueError: If the config file contains invalid JSON or structure
            OSError: If unable to write the file
        """
        config = self.load_test_config()

        # Filter out the test
        original_count = len(config.tests)
        config.tests = [t for t in config.tests if t.name != test_name]

        # Check if anything was removed
        if len(config.tests) == original_count:
            logger.debug(
                f"Test '{test_name}' not found, nothing removed",
            )
            return False

        # Save updated config
        self.save_test_config(config)
        logger.info(
            f"Removed test '{test_name}' from config",
        )
        return True
