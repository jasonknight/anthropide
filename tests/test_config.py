"""
Unit tests for config module.

Tests configuration settings, path constants, and environment variable handling.
"""

import os
import pytest
from pathlib import Path


def test_config_imports():
    """Test that config module can be imported without errors."""
    import config
    assert config is not None


def test_path_constants_defined():
    """Test that all path constants are properly defined."""
    import config

    assert hasattr(config, 'APP_ROOT')
    assert hasattr(config, 'PROJECT_ROOT')
    assert hasattr(config, 'STATIC_ROOT')
    assert hasattr(config, 'TEMPLATE_ROOT')

    assert isinstance(config.APP_ROOT, Path)
    assert isinstance(config.PROJECT_ROOT, Path)
    assert isinstance(config.STATIC_ROOT, Path)
    assert isinstance(config.TEMPLATE_ROOT, Path)


def test_path_constants_are_absolute():
    """Test that all path constants are absolute paths."""
    import config

    assert config.APP_ROOT.is_absolute()
    assert config.PROJECT_ROOT.is_absolute()
    assert config.STATIC_ROOT.is_absolute()
    assert config.TEMPLATE_ROOT.is_absolute()


def test_path_resolution():
    """Test that path constants resolve correctly relative to config file."""
    import config

    # APP_ROOT should be the directory containing config.py
    assert config.APP_ROOT.name == 'anthropide'

    # PROJECT_ROOT should be APP_ROOT/projects
    assert config.PROJECT_ROOT == config.APP_ROOT / 'projects'

    # STATIC_ROOT should be APP_ROOT/static
    assert config.STATIC_ROOT == config.APP_ROOT / 'static'

    # TEMPLATE_ROOT should be APP_ROOT/templates
    assert config.TEMPLATE_ROOT == config.APP_ROOT / 'templates'


def test_required_directories_created():
    """Test that required directories are created on import."""
    import config

    assert config.PROJECT_ROOT.exists()
    assert config.STATIC_ROOT.exists()
    assert config.TEMPLATE_ROOT.exists()


def test_api_settings_defined():
    """Test that API settings are properly defined."""
    import config

    assert hasattr(config, 'ANTHROPIC_API_KEY')
    assert hasattr(config, 'DEFAULT_MODEL')

    assert config.DEFAULT_MODEL == 'claude-sonnet-4-5-20250929'


def test_project_settings_defined():
    """Test that project settings are properly defined."""
    import config

    assert hasattr(config, 'MAX_SESSION_BACKUPS')
    assert hasattr(config, 'AUTO_SAVE')
    assert hasattr(config, 'SESSION_BACKUP_FORMAT')

    assert isinstance(config.MAX_SESSION_BACKUPS, int)
    assert config.MAX_SESSION_BACKUPS > 0
    assert isinstance(config.AUTO_SAVE, bool)
    assert isinstance(config.SESSION_BACKUP_FORMAT, str)


def test_file_extension_settings():
    """Test that file extension constants are defined."""
    import config

    assert config.AGENT_EXT == '.md'
    assert config.SKILL_EXT == '.md'
    assert config.TOOL_JSON_EXT == '.json'
    assert config.TOOL_PY_EXT == '.py'
    assert config.SNIPPET_EXT == '.md'


def test_validation_settings():
    """Test that validation constants are defined."""
    import config

    assert hasattr(config, 'MAX_PROJECT_NAME_LENGTH')
    assert hasattr(config, 'ALLOWED_PROJECT_NAME_CHARS')
    assert hasattr(config, 'MAX_SNIPPET_CATEGORIES')

    assert isinstance(config.MAX_PROJECT_NAME_LENGTH, int)
    assert config.MAX_PROJECT_NAME_LENGTH > 0
    assert isinstance(config.ALLOWED_PROJECT_NAME_CHARS, str)
    assert isinstance(config.MAX_SNIPPET_CATEGORIES, int)


def test_server_settings_defined():
    """Test that server settings are properly defined."""
    import config

    assert hasattr(config, 'HOST')
    assert hasattr(config, 'PORT')
    assert hasattr(config, 'DEBUG')
    assert hasattr(config, 'RELOADER')
    assert hasattr(config, 'LOG_LEVEL')

    assert isinstance(config.HOST, str)
    assert isinstance(config.PORT, int)
    assert isinstance(config.DEBUG, bool)
    assert isinstance(config.RELOADER, bool)
    assert isinstance(config.LOG_LEVEL, str)


def test_environment_variable_host(monkeypatch):
    """Test that HOST can be set via environment variable."""
    monkeypatch.setenv('ANTHROPIDE_HOST', '0.0.0.0')

    # Reload config module to pick up env var
    import importlib
    import config
    importlib.reload(config)

    assert config.HOST == '0.0.0.0'


def test_environment_variable_port(monkeypatch):
    """Test that PORT can be set via environment variable."""
    monkeypatch.setenv('ANTHROPIDE_PORT', '9000')

    # Reload config module to pick up env var
    import importlib
    import config
    importlib.reload(config)

    assert config.PORT == 9000


def test_environment_variable_debug(monkeypatch):
    """Test that DEBUG can be set via environment variable."""
    monkeypatch.setenv('ANTHROPIDE_DEBUG', 'false')

    # Reload config module to pick up env var
    import importlib
    import config
    importlib.reload(config)

    assert config.DEBUG is False


def test_environment_variable_log_level(monkeypatch):
    """Test that LOG_LEVEL can be set via environment variable."""
    monkeypatch.setenv('ANTHROPIDE_LOG_LEVEL', 'DEBUG')

    # Reload config module to pick up env var
    import importlib
    import config
    importlib.reload(config)

    assert config.LOG_LEVEL == 'DEBUG'


def test_environment_variable_api_key(monkeypatch):
    """Test that ANTHROPIC_API_KEY can be read from environment."""
    test_key = 'sk-ant-test-key-12345'
    monkeypatch.setenv('ANTHROPIC_API_KEY', test_key)

    # Reload config module to pick up env var
    import importlib
    import config
    importlib.reload(config)

    assert config.ANTHROPIC_API_KEY == test_key


def test_configuration_values_accessible():
    """Test that configuration values can be accessed without errors."""
    import config

    # Access all major configuration values
    _ = config.APP_ROOT
    _ = config.PROJECT_ROOT
    _ = config.STATIC_ROOT
    _ = config.TEMPLATE_ROOT
    _ = config.ANTHROPIC_API_KEY
    _ = config.DEFAULT_MODEL
    _ = config.MAX_SESSION_BACKUPS
    _ = config.AUTO_SAVE
    _ = config.SESSION_BACKUP_FORMAT
    _ = config.AGENT_EXT
    _ = config.SKILL_EXT
    _ = config.TOOL_JSON_EXT
    _ = config.TOOL_PY_EXT
    _ = config.SNIPPET_EXT
    _ = config.MAX_PROJECT_NAME_LENGTH
    _ = config.ALLOWED_PROJECT_NAME_CHARS
    _ = config.MAX_SNIPPET_CATEGORIES
    _ = config.HOST
    _ = config.PORT
    _ = config.DEBUG
    _ = config.RELOADER
    _ = config.LOG_LEVEL


def test_no_circular_dependencies():
    """Test that config module can be imported without circular dependencies."""
    import sys

    # Clear any cached imports
    if 'config' in sys.modules:
        del sys.modules['config']

    # Import should succeed without circular dependency errors
    import config
    assert config is not None
