"""
Comprehensive unit tests for TestConfigManager class.

Tests cover:
- Initialization and directory structure
- Loading valid configurations
- Loading invalid configurations (JSON errors, validation errors)
- Saving configurations
- Getting test by name
- Listing all tests
- Validation
- Adding tests
- Removing tests
- Error cases (missing directory, invalid JSON, invalid structure)
- Edge cases (empty configs, duplicate names, non-existent tests)
"""

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from lib.data_models import (
    ContentBlock,
    TestCase,
    TestConfig,
    TestMatch,
    TestResponse,
    TestSequenceItem,
)
from lib.test_config_manager import TestConfigManager


class TestTestConfigManagerInit:
    """Tests for TestConfigManager initialization."""

    def test_init_sets_paths(self, tmp_path):
        """Test that initialization sets correct paths."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = TestConfigManager(project_path)

        assert manager.project_path == project_path
        assert manager.tests_dir == project_path / "tests"
        assert manager.config_path == project_path / "tests" / "config.json"

    def test_init_accepts_string_path(self, tmp_path):
        """Test that initialization accepts string paths."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = TestConfigManager(str(project_path))

        assert manager.project_path == project_path

    def test_init_converts_to_path(self, tmp_path):
        """Test that paths are converted to Path objects."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = TestConfigManager(project_path)

        assert isinstance(manager.project_path, Path)
        assert isinstance(manager.tests_dir, Path)
        assert isinstance(manager.config_path, Path)


class TestLoadTestConfig:
    """Tests for loading test configurations."""

    def test_load_creates_default_if_missing(self, tmp_path):
        """Test that loading creates default config if file doesn't exist."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)
        config = manager.load_test_config()

        # Should return empty config
        assert isinstance(config, TestConfig)
        assert len(config.tests) == 0

        # Should have created the file
        assert manager.config_path.exists()

        # File should contain valid JSON
        with open(manager.config_path, 'r') as f:
            data = json.load(f)
        assert data == {"tests": []}

    def test_load_raises_error_if_tests_dir_missing(self, tmp_path):
        """Test that loading raises FileNotFoundError if tests dir missing."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        # Don't create tests directory

        manager = TestConfigManager(project_path)

        with pytest.raises(
            FileNotFoundError,
            match="Tests directory not found",
        ):
            manager.load_test_config()

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        config = manager.load_test_config()

        assert isinstance(config, TestConfig)
        assert len(config.tests) == 2
        assert config.tests[0].name == "simple_test"
        assert config.tests[1].name == "regex_test"

    def test_load_empty_config(self, tmp_path):
        """Test loading an empty but valid configuration."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy empty config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "empty_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        config = manager.load_test_config()

        assert isinstance(config, TestConfig)
        assert len(config.tests) == 0

    def test_load_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises ValueError."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy invalid JSON fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "invalid_json.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.load_test_config()

    def test_load_invalid_structure_raises_validation_error(self, tmp_path):
        """Test that invalid structure raises ValidationError."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy invalid structure fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "invalid_structure.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        with pytest.raises(ValidationError):
            manager.load_test_config()

    def test_load_missing_required_fields_raises_validation_error(self, tmp_path):
        """Test that missing required fields raises ValidationError."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy missing fields fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "missing_required_fields.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        with pytest.raises(ValidationError):
            manager.load_test_config()

    def test_load_config_with_tool_results(self, tmp_path):
        """Test loading config with tool results."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy tool results fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "tool_results_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        config = manager.load_test_config()

        assert len(config.tests) == 1
        test = config.tests[0]
        assert test.name == "tool_test"
        assert test.sequence[0].tool_behavior == "mock"
        assert test.sequence[0].tool_results == {"tool_123": "Tool executed successfully"}


class TestSaveTestConfig:
    """Tests for saving test configurations."""

    def test_save_creates_tests_directory(self, tmp_path):
        """Test that saving creates tests directory if it doesn't exist."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = TestConfigManager(project_path)
        config = TestConfig(tests=[])

        manager.save_test_config(config)

        assert manager.tests_dir.exists()
        assert manager.config_path.exists()

    def test_save_empty_config(self, tmp_path):
        """Test saving an empty configuration."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)
        config = TestConfig(tests=[])

        manager.save_test_config(config)

        # Verify file was created and contains correct data
        assert manager.config_path.exists()
        with open(manager.config_path, 'r') as f:
            data = json.load(f)
        assert data == {"tests": []}

    def test_save_config_with_tests(self, tmp_path):
        """Test saving configuration with test cases."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        # Create test config with a test case
        test_case = TestCase(
            name="test1",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content",
                        value="hello",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Hello!",
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                ),
            ],
        )
        config = TestConfig(tests=[test_case])

        manager.save_test_config(config)

        # Verify file contents
        assert manager.config_path.exists()
        with open(manager.config_path, 'r') as f:
            data = json.load(f)

        assert "tests" in data
        assert len(data["tests"]) == 1
        assert data["tests"][0]["name"] == "test1"

    def test_save_overwrites_existing_config(self, tmp_path):
        """Test that saving overwrites existing configuration."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        # Save first config
        config1 = TestConfig(
            tests=[
                TestCase(
                    name="test1",
                    sequence=[],
                ),
            ],
        )
        manager.save_test_config(config1)

        # Save second config
        config2 = TestConfig(
            tests=[
                TestCase(
                    name="test2",
                    sequence=[],
                ),
            ],
        )
        manager.save_test_config(config2)

        # Load and verify
        loaded_config = manager.load_test_config()
        assert len(loaded_config.tests) == 1
        assert loaded_config.tests[0].name == "test2"

    def test_save_validates_config(self, tmp_path):
        """Test that save validates config before writing."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        # Create an invalid test case (missing pattern for regex match)
        # Note: Pydantic validation happens at construction time,
        # so we need to construct a valid object first, then modify it
        test_case = TestCase(
            name="invalid_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content",
                        value="test",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Response",
                            ),
                        ],
                    ),
                ),
            ],
        )

        # Manually modify to create invalid state (bypass Pydantic validation)
        test_case.sequence[0].match.type = "regex"
        test_case.sequence[0].match.pattern = None
        test_case.sequence[0].match.value = "test"

        config = TestConfig(tests=[test_case])

        # Should raise ValidationError when trying to save
        with pytest.raises(ValidationError):
            manager.save_test_config(config)

        # Verify file was not created
        assert not manager.config_path.exists()

    def test_save_preserves_formatting(self, tmp_path):
        """Test that saved JSON is properly formatted."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)
        config = TestConfig(tests=[])

        manager.save_test_config(config)

        # Read raw file content
        content = manager.config_path.read_text()

        # Should have indentation
        assert "  " in content or "\t" in content


class TestGetTest:
    """Tests for getting a specific test by name."""

    def test_get_existing_test(self, tmp_path):
        """Test getting an existing test case."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        test = manager.get_test("simple_test")

        assert test is not None
        assert test.name == "simple_test"
        assert len(test.sequence) == 1

    def test_get_non_existent_test(self, tmp_path):
        """Test getting a non-existent test returns None."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        test = manager.get_test("non_existent_test")

        assert test is None

    def test_get_test_from_empty_config(self, tmp_path):
        """Test getting test from empty config returns None."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy empty config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "empty_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        test = manager.get_test("any_test")

        assert test is None

    def test_get_test_creates_default_if_missing(self, tmp_path):
        """Test that get_test creates default config if file doesn't exist."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)
        test = manager.get_test("any_test")

        assert test is None
        assert manager.config_path.exists()


class TestListTests:
    """Tests for listing all test names."""

    def test_list_tests_with_multiple_tests(self, tmp_path):
        """Test listing multiple test names."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        test_names = manager.list_tests()

        assert isinstance(test_names, list)
        assert len(test_names) == 2
        assert "simple_test" in test_names
        assert "regex_test" in test_names

    def test_list_tests_empty_config(self, tmp_path):
        """Test listing tests from empty config."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy empty config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "empty_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)
        test_names = manager.list_tests()

        assert isinstance(test_names, list)
        assert len(test_names) == 0

    def test_list_tests_creates_default_if_missing(self, tmp_path):
        """Test that list_tests creates default config if file doesn't exist."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)
        test_names = manager.list_tests()

        assert isinstance(test_names, list)
        assert len(test_names) == 0
        assert manager.config_path.exists()


class TestValidateConfig:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, tmp_path):
        """Test validating a valid configuration."""
        project_path = tmp_path / "test_project"
        manager = TestConfigManager(project_path)

        config = TestConfig(
            tests=[
                TestCase(
                    name="test1",
                    sequence=[
                        TestSequenceItem(
                            match=TestMatch(
                                type="contains",
                                path="messages.0.content",
                                value="hello",
                            ),
                            response=TestResponse(
                                role="assistant",
                                content=[
                                    ContentBlock(
                                        type="text",
                                        text="Hello!",
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ],
        )

        # Should not raise any exception
        manager.validate_config(config)

    def test_validate_empty_config(self, tmp_path):
        """Test validating an empty configuration."""
        project_path = tmp_path / "test_project"
        manager = TestConfigManager(project_path)

        config = TestConfig(tests=[])

        # Should not raise any exception
        manager.validate_config(config)

    def test_validate_config_with_multiple_tests(self, tmp_path):
        """Test validating config with multiple test cases."""
        project_path = tmp_path / "test_project"
        manager = TestConfigManager(project_path)

        config = TestConfig(
            tests=[
                TestCase(
                    name="test1",
                    sequence=[],
                ),
                TestCase(
                    name="test2",
                    sequence=[],
                ),
            ],
        )

        # Should not raise any exception
        manager.validate_config(config)

    def test_validate_invalid_config_raises_error(self, tmp_path):
        """Test that validating invalid config raises ValidationError."""
        project_path = tmp_path / "test_project"
        manager = TestConfigManager(project_path)

        # Create a test with missing required field
        test_case = TestCase(
            name="test1",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="regex",
                        path="messages.0.content",
                        pattern="test.*",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Response",
                            ),
                        ],
                    ),
                ),
            ],
        )

        # Manually corrupt the match to bypass Pydantic validation
        test_case.sequence[0].match.pattern = None

        config = TestConfig(tests=[test_case])

        with pytest.raises(ValidationError):
            manager.validate_config(config)


class TestAddTest:
    """Tests for adding test cases."""

    def test_add_test_to_empty_config(self, tmp_path):
        """Test adding a test to an empty configuration."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        test_case = TestCase(
            name="new_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content",
                        value="hello",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Hello!",
                            ),
                        ],
                    ),
                ),
            ],
        )

        manager.add_test(test_case)

        # Verify test was added
        config = manager.load_test_config()
        assert len(config.tests) == 1
        assert config.tests[0].name == "new_test"

    def test_add_test_to_existing_config(self, tmp_path):
        """Test adding a test to existing configuration."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        test_case = TestCase(
            name="new_test",
            sequence=[],
        )

        manager.add_test(test_case)

        # Verify test was added
        config = manager.load_test_config()
        assert len(config.tests) == 3
        test_names = [t.name for t in config.tests]
        assert "new_test" in test_names

    def test_add_test_replaces_existing(self, tmp_path):
        """Test that adding a test with existing name replaces it."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        # Replace existing test
        test_case = TestCase(
            name="simple_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content",
                        value="new value",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="New response",
                            ),
                        ],
                    ),
                ),
            ],
        )

        manager.add_test(test_case)

        # Verify test was replaced, not added
        config = manager.load_test_config()
        assert len(config.tests) == 2

        # Verify the test was updated
        simple_test = manager.get_test("simple_test")
        assert simple_test.sequence[0].match.value == "new value"


class TestRemoveTest:
    """Tests for removing test cases."""

    def test_remove_existing_test(self, tmp_path):
        """Test removing an existing test case."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        result = manager.remove_test("simple_test")

        assert result is True

        # Verify test was removed
        config = manager.load_test_config()
        assert len(config.tests) == 1
        assert config.tests[0].name == "regex_test"

    def test_remove_non_existent_test(self, tmp_path):
        """Test removing a non-existent test returns False."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy valid config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "valid_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        result = manager.remove_test("non_existent_test")

        assert result is False

        # Verify config unchanged
        config = manager.load_test_config()
        assert len(config.tests) == 2

    def test_remove_from_empty_config(self, tmp_path):
        """Test removing from empty config returns False."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Copy empty config fixture
        fixture_path = Path(__file__).parent / "fixtures" / "test_configs" / "empty_config.json"
        shutil.copy(fixture_path, tests_dir / "config.json")

        manager = TestConfigManager(project_path)

        result = manager.remove_test("any_test")

        assert result is False

    def test_remove_last_test(self, tmp_path):
        """Test removing the last test in config."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        # Add a single test
        test_case = TestCase(
            name="only_test",
            sequence=[],
        )
        manager.add_test(test_case)

        # Remove it
        result = manager.remove_test("only_test")

        assert result is True

        # Verify config is empty
        config = manager.load_test_config()
        assert len(config.tests) == 0


class TestErrorCases:
    """Tests for various error cases."""

    def test_operations_without_tests_directory(self, tmp_path):
        """Test that operations fail gracefully without tests directory."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = TestConfigManager(project_path)

        # load_test_config should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            manager.load_test_config()

        # get_test should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            manager.get_test("test")

        # list_tests should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            manager.list_tests()

        # add_test should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            test_case = TestCase(name="test", sequence=[])
            manager.add_test(test_case)

        # remove_test should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            manager.remove_test("test")

    def test_save_creates_missing_directory(self, tmp_path):
        """Test that save creates missing tests directory."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = TestConfigManager(project_path)
        config = TestConfig(tests=[])

        # Should not raise error, should create directory
        manager.save_test_config(config)

        assert manager.tests_dir.exists()
        assert manager.config_path.exists()

    def test_load_corrupted_file(self, tmp_path):
        """Test loading a completely corrupted file."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Create a file with binary garbage
        config_path = tests_dir / "config.json"
        config_path.write_bytes(b'\x00\x01\x02\x03\x04')

        manager = TestConfigManager(project_path)

        with pytest.raises(ValueError, match="Invalid JSON|Error reading"):
            manager.load_test_config()

    def test_load_with_permission_error(self, tmp_path):
        """Test loading config when file is not readable."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        config_path = tests_dir / "config.json"
        config_path.write_text('{"tests": []}')

        # Make file unreadable
        config_path.chmod(0o000)

        manager = TestConfigManager(project_path)

        try:
            with pytest.raises(ValueError, match="Error reading"):
                manager.load_test_config()
        finally:
            # Restore permissions for cleanup
            config_path.chmod(0o644)

    def test_save_with_permission_error(self, tmp_path):
        """Test saving config when directory is not writable."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        # Make directory read-only
        tests_dir.chmod(0o444)

        manager = TestConfigManager(project_path)
        config = TestConfig(tests=[])

        try:
            with pytest.raises(OSError, match="Error writing"):
                manager.save_test_config(config)
        finally:
            # Restore permissions for cleanup
            tests_dir.chmod(0o755)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_config_with_very_long_test_name(self, tmp_path):
        """Test handling test with very long name."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        long_name = "a" * 1000
        test_case = TestCase(
            name=long_name,
            sequence=[],
        )

        manager.add_test(test_case)

        # Should be able to retrieve it
        test = manager.get_test(long_name)
        assert test is not None
        assert test.name == long_name

    def test_config_with_special_characters_in_name(self, tmp_path):
        """Test handling test names with special characters."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        special_name = "test-with_special.chars@123"
        test_case = TestCase(
            name=special_name,
            sequence=[],
        )

        manager.add_test(test_case)

        # Should be able to retrieve it
        test = manager.get_test(special_name)
        assert test is not None
        assert test.name == special_name

    def test_config_with_unicode_characters(self, tmp_path):
        """Test handling test names with unicode characters."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        unicode_name = "test_测试_🎉"
        test_case = TestCase(
            name=unicode_name,
            sequence=[],
        )

        manager.add_test(test_case)

        # Should be able to retrieve it
        test = manager.get_test(unicode_name)
        assert test is not None
        assert test.name == unicode_name

    def test_multiple_saves_and_loads(self, tmp_path):
        """Test multiple save/load cycles."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        # Save and load multiple times
        for i in range(10):
            test_case = TestCase(
                name=f"test_{i}",
                sequence=[],
            )
            manager.add_test(test_case)

            config = manager.load_test_config()
            assert len(config.tests) == i + 1

    def test_concurrent_modifications(self, tmp_path):
        """Test handling concurrent modifications."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager1 = TestConfigManager(project_path)
        manager2 = TestConfigManager(project_path)

        # Manager 1 adds a test
        test1 = TestCase(name="test1", sequence=[])
        manager1.add_test(test1)

        # Manager 2 adds a different test (will load existing config first)
        test2 = TestCase(name="test2", sequence=[])
        manager2.add_test(test2)

        # Both tests should be present since add_test loads before saving
        config = manager1.load_test_config()
        assert len(config.tests) == 2
        test_names = [t.name for t in config.tests]
        assert "test1" in test_names
        assert "test2" in test_names

    def test_empty_sequence_in_test(self, tmp_path):
        """Test handling test with empty sequence."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        test_case = TestCase(
            name="empty_sequence_test",
            sequence=[],
        )

        manager.add_test(test_case)

        # Should be able to load it
        test = manager.get_test("empty_sequence_test")
        assert test is not None
        assert len(test.sequence) == 0

    def test_complex_nested_structure(self, tmp_path):
        """Test handling complex nested test structure."""
        project_path = tmp_path / "test_project"
        tests_dir = project_path / "tests"
        tests_dir.mkdir(parents=True)

        manager = TestConfigManager(project_path)

        # Create a complex test with nested structures
        test_case = TestCase(
            name="complex_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content",
                        value="complex",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Response 1",
                            ),
                            ContentBlock(
                                type="tool_use",
                                id="tool_1",
                                name="test_tool",
                                input={"param": "value"},
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                    tool_results={
                        "tool_1": "Tool result",
                    },
                ),
            ],
        )

        manager.add_test(test_case)

        # Load and verify structure is preserved
        test = manager.get_test("complex_test")
        assert test is not None
        assert len(test.sequence) == 1
        assert len(test.sequence[0].response.content) == 2
        assert test.sequence[0].tool_results == {"tool_1": "Tool result"}
