"""
Comprehensive unit tests for the ToolManager class.

Tests cover:
- Loading JSON tools (valid/invalid)
- Loading Python tools (valid/invalid)
- Schema validation
- Error handling (missing files, import errors)
- Tool caching
- Getting tools by name
- Listing all tools
"""

import json
import logging
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

from lib.tool_manager import (
    ToolManager,
    ToolError,
    ToolNotFoundError,
    ToolLoadError,
    ToolValidationError,
)
from lib.data_models import ToolSchema


class TestToolManagerInit:
    """Test ToolManager initialization."""

    def test_init_creates_tools_directory(self, tmp_path):
        """Test that __init__ creates tools directory if it doesn't exist."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        assert manager.project_path == project_path
        assert manager.tools_dir == project_path / "tools"
        assert manager.tools_dir.exists()
        assert manager.tools_dir.is_dir()

    def test_init_with_existing_tools_directory(self, tmp_path):
        """Test that __init__ works with existing tools directory."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)

        assert manager.tools_dir.exists()
        assert len(manager._tool_cache) == 0

    def test_init_initializes_caches(self, tmp_path):
        """Test that __init__ initializes empty caches."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        assert isinstance(manager._tool_cache, dict)
        assert len(manager._tool_cache) == 0
        assert isinstance(manager._module_cache, dict)
        assert len(manager._module_cache) == 0
        assert isinstance(manager._tool_file_map, dict)
        assert len(manager._tool_file_map) == 0


class TestLoadJsonTool:
    """Test loading JSON tool definitions."""

    def test_load_valid_json_tool(self, tmp_path):
        """Test loading a valid JSON tool definition."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create valid JSON tool
        tool_file = tools_dir / "test_tool.json"
        tool_data = {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                },
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        tool_def = manager.load_json_tool(tool_file)

        assert isinstance(tool_def, ToolSchema)
        assert tool_def.name == "test_tool"
        assert tool_def.description == "A test tool"
        assert tool_def.input_schema["type"] == "object"

    def test_load_json_tool_with_all_fields(self, tmp_path):
        """Test loading JSON tool with all optional fields."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "complex_tool.json"
        tool_data = {
            "name": "complex_tool",
            "description": "A complex test tool",
            "input_schema": {
                "type": "object",
                "properties": {
                    "required_param": {
                        "type": "string",
                        "description": "A required parameter",
                    },
                    "optional_param": {
                        "type": "integer",
                        "description": "An optional parameter",
                    },
                },
                "required": ["required_param"],
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        tool_def = manager.load_json_tool(tool_file)

        assert tool_def.name == "complex_tool"
        assert "required" in tool_def.input_schema
        assert "required_param" in tool_def.input_schema["required"]

    def test_load_json_tool_file_not_found(self, tmp_path):
        """Test loading JSON tool raises error when file doesn't exist."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)
        non_existent = tools_dir / "nonexistent.json"

        with pytest.raises(ToolNotFoundError) as exc_info:
            manager.load_json_tool(non_existent)

        assert "not found" in str(exc_info.value).lower()

    def test_load_json_tool_invalid_json(self, tmp_path):
        """Test loading JSON tool with invalid JSON raises error."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "invalid.json"
        tool_file.write_text("{ invalid json }")

        manager = ToolManager(project_path)

        with pytest.raises(ToolLoadError) as exc_info:
            manager.load_json_tool(tool_file)

        assert "invalid json" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

    def test_load_json_tool_missing_required_fields(self, tmp_path):
        """Test loading JSON tool with missing required fields."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "incomplete.json"
        tool_data = {
            "name": "incomplete_tool",
            # Missing 'description' and 'input_schema'
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)

        with pytest.raises(ToolError):
            manager.load_json_tool(tool_file)


class TestLoadPythonTool:
    """Test loading Python tool modules."""

    def test_load_valid_python_tool(self, tmp_path):
        """Test loading a valid Python tool module."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create valid Python tool
        tool_file = tools_dir / "python_tool.py"
        tool_code = '''
def describe():
    return {
        "name": "python_tool",
        "description": "A Python test tool",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
            },
        },
    }

def run(param1):
    return f"Executed with {param1}"
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        tool_def = manager.load_python_tool(tool_file)

        assert isinstance(tool_def, ToolSchema)
        assert tool_def.name == "python_tool"
        assert tool_def.description == "A Python test tool"

    def test_load_python_tool_caches_module(self, tmp_path):
        """Test that Python modules are cached after loading."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "cached_tool.py"
        tool_code = '''
def describe():
    return {
        "name": "cached_tool",
        "description": "A tool for caching test",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        # Load once
        tool_def1 = manager.load_python_tool(tool_file)

        # Check module is cached
        module_name = f"anthropide_tool_{tool_file.stem}"
        assert module_name in manager._module_cache
        assert module_name in sys.modules

        # Load again - should use cached module
        tool_def2 = manager.load_python_tool(tool_file)

        assert tool_def1.name == tool_def2.name

    def test_load_python_tool_file_not_found(self, tmp_path):
        """Test loading Python tool raises error when file doesn't exist."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)
        non_existent = tools_dir / "nonexistent.py"

        with pytest.raises(ToolNotFoundError) as exc_info:
            manager.load_python_tool(non_existent)

        assert "not found" in str(exc_info.value).lower()

    def test_load_python_tool_missing_describe(self, tmp_path):
        """Test loading Python tool without describe() function."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "no_describe.py"
        tool_code = '''
def run():
    return "I have no describe function"
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        with pytest.raises(ToolValidationError) as exc_info:
            manager.load_python_tool(tool_file)

        assert "describe" in str(exc_info.value).lower()

    def test_load_python_tool_describe_not_callable(self, tmp_path):
        """Test loading Python tool where describe is not callable."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "describe_not_callable.py"
        tool_code = '''
describe = "I am not a function"
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        with pytest.raises(ToolValidationError) as exc_info:
            manager.load_python_tool(tool_file)

        assert "not callable" in str(exc_info.value).lower()

    def test_load_python_tool_describe_returns_non_dict(self, tmp_path):
        """Test loading Python tool where describe() returns non-dictionary."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "bad_return.py"
        tool_code = '''
def describe():
    return "I should return a dict"
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        with pytest.raises(ToolValidationError) as exc_info:
            manager.load_python_tool(tool_file)

        assert "dictionary" in str(exc_info.value).lower()

    def test_load_python_tool_describe_raises_exception(self, tmp_path):
        """Test loading Python tool where describe() raises exception."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "describe_error.py"
        tool_code = '''
def describe():
    raise ValueError("Describe error")
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        with pytest.raises(ToolLoadError) as exc_info:
            manager.load_python_tool(tool_file)

        assert "describe()" in str(exc_info.value).lower()

    def test_load_python_tool_syntax_error(self, tmp_path):
        """Test loading Python tool with syntax errors."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "syntax_error.py"
        tool_code = '''
def describe()
    return {"name": "bad"}  # Missing colon
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        with pytest.raises(ToolLoadError) as exc_info:
            manager.load_python_tool(tool_file)

        assert "failed" in str(exc_info.value).lower()

    def test_load_python_tool_import_error(self, tmp_path):
        """Test loading Python tool with import errors."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "import_error.py"
        tool_code = '''
import nonexistent_module

def describe():
    return {"name": "import_error"}
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)

        with pytest.raises(ToolLoadError) as exc_info:
            manager.load_python_tool(tool_file)

        assert "failed" in str(exc_info.value).lower()


class TestValidateToolSchema:
    """Test tool schema validation."""

    def test_validate_valid_schema(self, tmp_path):
        """Test validating a valid tool schema."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "valid_tool",
            "description": "A valid tool",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                },
            },
        }

        tool_schema = manager.validate_tool_schema(tool_data)

        assert isinstance(tool_schema, ToolSchema)
        assert tool_schema.name == "valid_tool"

    def test_validate_schema_missing_name(self, tmp_path):
        """Test validation fails when name is missing."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "description": "Missing name",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }

        with pytest.raises(ToolValidationError):
            manager.validate_tool_schema(tool_data)

    def test_validate_schema_missing_description(self, tmp_path):
        """Test validation fails when description is missing."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "no_description",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }

        with pytest.raises(ToolValidationError):
            manager.validate_tool_schema(tool_data)

    def test_validate_schema_missing_input_schema(self, tmp_path):
        """Test validation fails when input_schema is missing."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "no_input_schema",
            "description": "Missing input schema",
        }

        with pytest.raises(ToolValidationError):
            manager.validate_tool_schema(tool_data)

    def test_validate_schema_input_schema_not_dict(self, tmp_path):
        """Test validation fails when input_schema is not a dictionary."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "bad_schema",
            "description": "Bad input schema",
            "input_schema": "not a dict",
        }

        with pytest.raises(ToolValidationError) as exc_info:
            manager.validate_tool_schema(tool_data)

        assert "dictionary" in str(exc_info.value).lower()

    def test_validate_schema_missing_type(self, tmp_path):
        """Test validation fails when input_schema missing 'type' field."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "missing_type",
            "description": "Missing type",
            "input_schema": {
                "properties": {},
            },
        }

        with pytest.raises(ToolValidationError) as exc_info:
            manager.validate_tool_schema(tool_data)

        assert "type" in str(exc_info.value).lower()

    def test_validate_schema_wrong_type(self, tmp_path):
        """Test validation fails when input_schema type is not 'object'."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "wrong_type",
            "description": "Wrong type",
            "input_schema": {
                "type": "string",
                "properties": {},
            },
        }

        with pytest.raises(ToolValidationError) as exc_info:
            manager.validate_tool_schema(tool_data)

        assert "object" in str(exc_info.value).lower()

    def test_validate_schema_missing_properties(self, tmp_path):
        """Test validation fails when input_schema missing 'properties'."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "missing_properties",
            "description": "Missing properties",
            "input_schema": {
                "type": "object",
            },
        }

        with pytest.raises(ToolValidationError) as exc_info:
            manager.validate_tool_schema(tool_data)

        assert "properties" in str(exc_info.value).lower()

    def test_validate_schema_properties_not_dict(self, tmp_path):
        """Test validation fails when properties is not a dictionary."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        tool_data = {
            "name": "bad_properties",
            "description": "Bad properties",
            "input_schema": {
                "type": "object",
                "properties": "not a dict",
            },
        }

        with pytest.raises(ToolValidationError) as exc_info:
            manager.validate_tool_schema(tool_data)

        assert "properties" in str(exc_info.value).lower()


class TestLoadTools:
    """Test loading all tools from directory."""

    def test_load_tools_empty_directory(self, tmp_path):
        """Test loading tools from empty directory returns empty dict."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)
        tools = manager.load_tools()

        assert isinstance(tools, dict)
        assert len(tools) == 0

    def test_load_tools_json_only(self, tmp_path):
        """Test loading tools with only JSON files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create JSON tools
        for i in range(3):
            tool_file = tools_dir / f"tool{i}.json"
            tool_data = {
                "name": f"tool{i}",
                "description": f"Tool {i}",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            }
            tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        tools = manager.load_tools()

        assert len(tools) == 3
        assert "tool0" in tools
        assert "tool1" in tools
        assert "tool2" in tools

    def test_load_tools_python_only(self, tmp_path):
        """Test loading tools with only Python files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create Python tools
        for i in range(2):
            tool_file = tools_dir / f"pytool{i}.py"
            tool_code = f'''
def describe():
    return {{
        "name": "pytool{i}",
        "description": "Python Tool {i}",
        "input_schema": {{
            "type": "object",
            "properties": {{}},
        }},
    }}
'''
            tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        tools = manager.load_tools()

        assert len(tools) == 2
        assert "pytool0" in tools
        assert "pytool1" in tools

    def test_load_tools_mixed(self, tmp_path):
        """Test loading tools with both JSON and Python files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create JSON tool
        json_file = tools_dir / "json_tool.json"
        json_data = {
            "name": "json_tool",
            "description": "JSON Tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        json_file.write_text(json.dumps(json_data))

        # Create Python tool
        py_file = tools_dir / "py_tool.py"
        py_code = '''
def describe():
    return {
        "name": "py_tool",
        "description": "Python Tool",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        py_file.write_text(py_code)

        manager = ToolManager(project_path)
        tools = manager.load_tools()

        assert len(tools) == 2
        assert "json_tool" in tools
        assert "py_tool" in tools

    def test_load_tools_populates_cache(self, tmp_path):
        """Test that load_tools populates the cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "cache_test.json"
        tool_data = {
            "name": "cache_test",
            "description": "Cache Test",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        manager.load_tools()

        assert "cache_test" in manager._tool_cache
        assert "cache_test" in manager._tool_file_map

    def test_load_tools_clears_previous_cache(self, tmp_path):
        """Test that load_tools clears previous cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)

        # Manually add to cache
        manager._tool_cache["old_tool"] = Mock()

        # Load tools (should clear old cache)
        manager.load_tools()

        assert "old_tool" not in manager._tool_cache

    def test_load_tools_continues_on_error(self, tmp_path, caplog):
        """Test that load_tools continues loading other tools when one fails."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create valid tool
        valid_file = tools_dir / "valid.json"
        valid_data = {
            "name": "valid",
            "description": "Valid tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        valid_file.write_text(json.dumps(valid_data))

        # Create invalid tool
        invalid_file = tools_dir / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        manager = ToolManager(project_path)

        with caplog.at_level(logging.ERROR):
            tools = manager.load_tools()

        # Should load the valid tool and skip the invalid one
        assert len(tools) == 1
        assert "valid" in tools
        assert "invalid" not in tools

    def test_load_tools_handles_duplicate_names(self, tmp_path, caplog):
        """Test that load_tools handles duplicate tool names."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create two tools with same name
        tool1 = tools_dir / "tool1.json"
        tool1_data = {
            "name": "duplicate_name",
            "description": "First tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool1.write_text(json.dumps(tool1_data))

        tool2 = tools_dir / "tool2.json"
        tool2_data = {
            "name": "duplicate_name",
            "description": "Second tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool2.write_text(json.dumps(tool2_data))

        manager = ToolManager(project_path)

        with caplog.at_level(logging.WARNING):
            tools = manager.load_tools()

        # Should only load the first one
        assert len(tools) == 1
        assert "duplicate_name" in tools
        assert "duplicate" in caplog.text.lower()


class TestGetTool:
    """Test getting tool by name."""

    def test_get_tool_from_cache(self, tmp_path):
        """Test getting tool from cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "cached.json"
        tool_data = {
            "name": "cached",
            "description": "Cached tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        manager.load_tools()

        # Get from cache
        tool = manager.get_tool("cached")

        assert tool is not None
        assert tool.name == "cached"

    def test_get_tool_loads_from_disk(self, tmp_path):
        """Test getting tool loads from disk if not in cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "on_disk.json"
        tool_data = {
            "name": "on_disk",
            "description": "On disk tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        # Don't call load_tools(), get_tool should load it

        tool = manager.get_tool("on_disk")

        assert tool is not None
        assert tool.name == "on_disk"
        # Should now be in cache
        assert "on_disk" in manager._tool_cache

    def test_get_tool_not_found(self, tmp_path):
        """Test getting non-existent tool returns None."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)

        tool = manager.get_tool("nonexistent")

        assert tool is None

    def test_get_tool_with_file_map(self, tmp_path):
        """Test getting tool using file map."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "mapped.json"
        tool_data = {
            "name": "mapped",
            "description": "Mapped tool",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        manager.load_tools()

        # Clear cache but keep file map
        manager._tool_cache.clear()

        # Should still be able to load using file map
        tool = manager.get_tool("mapped")

        assert tool is not None
        assert tool.name == "mapped"

    def test_get_tool_handles_load_error(self, tmp_path, caplog):
        """Test get_tool handles errors when loading from disk."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "bad.json"
        tool_file.write_text("{ invalid }")

        manager = ToolManager(project_path)

        with caplog.at_level(logging.ERROR):
            tool = manager.get_tool("bad")

        assert tool is None


class TestListTools:
    """Test listing all tools."""

    def test_list_tools_empty(self, tmp_path):
        """Test listing tools in empty directory."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 0

    def test_list_tools_json_files(self, tmp_path):
        """Test listing JSON tool files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create JSON files
        for name in ["alpha", "beta", "gamma"]:
            tool_file = tools_dir / f"{name}.json"
            tool_file.write_text("{}")

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        assert len(tools) == 3
        assert tools == ["alpha", "beta", "gamma"]  # Should be sorted

    def test_list_tools_python_files(self, tmp_path):
        """Test listing Python tool files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create Python files
        for name in ["tool_a", "tool_b"]:
            tool_file = tools_dir / f"{name}.py"
            tool_file.write_text("")

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        assert len(tools) == 2
        assert tools == ["tool_a", "tool_b"]

    def test_list_tools_mixed_files(self, tmp_path):
        """Test listing mixed JSON and Python files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create mixed files
        (tools_dir / "json_tool.json").write_text("{}")
        (tools_dir / "python_tool.py").write_text("")

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        assert len(tools) == 2
        assert "json_tool" in tools
        assert "python_tool" in tools

    def test_list_tools_sorted(self, tmp_path):
        """Test that list_tools returns sorted names."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create files in non-alphabetical order
        for name in ["zebra", "alpha", "middle"]:
            (tools_dir / f"{name}.json").write_text("{}")

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        assert tools == ["alpha", "middle", "zebra"]

    def test_list_tools_no_duplicates(self, tmp_path):
        """Test that list_tools handles duplicate names."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create JSON and Python with same stem
        (tools_dir / "tool.json").write_text("{}")
        (tools_dir / "tool.py").write_text("")

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        # Should only list once
        assert tools.count("tool") == 1

    def test_list_tools_ignores_other_files(self, tmp_path):
        """Test that list_tools ignores non-tool files."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create tool files
        (tools_dir / "tool.json").write_text("{}")
        # Create non-tool files
        (tools_dir / "readme.txt").write_text("")
        (tools_dir / "config.yaml").write_text("")

        manager = ToolManager(project_path)
        tools = manager.list_tools()

        assert len(tools) == 1
        assert tools == ["tool"]


class TestReloadTool:
    """Test reloading tools."""

    def test_reload_tool_clears_cache(self, tmp_path):
        """Test that reload_tool clears the cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "reload_test.json"
        tool_data = {
            "name": "reload_test",
            "description": "Original",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        manager.load_tools()

        # Modify the file
        tool_data["description"] = "Modified"
        tool_file.write_text(json.dumps(tool_data))

        # Reload
        tool = manager.reload_tool("reload_test")

        assert tool is not None
        assert tool.description == "Modified"

    def test_reload_python_tool_clears_module_cache(self, tmp_path):
        """Test that reloading Python tool clears module cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "py_reload.py"
        tool_code = '''
def describe():
    return {
        "name": "py_reload",
        "description": "Original",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        manager.load_tools()

        module_name = f"anthropide_tool_{tool_file.stem}"
        assert module_name in manager._module_cache

        # Reload should clear module cache
        manager.reload_tool("py_reload")

        # Module should be reloaded (still in cache but potentially different)
        # The key test is that sys.modules was cleared
        assert module_name in manager._module_cache

    def test_reload_tool_not_found(self, tmp_path):
        """Test reloading non-existent tool."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)

        tool = manager.reload_tool("nonexistent")

        assert tool is None


class TestClearCache:
    """Test cache clearing."""

    def test_clear_cache_empties_tool_cache(self, tmp_path):
        """Test that clear_cache empties the tool cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "cache_tool.json"
        tool_data = {
            "name": "cache_tool",
            "description": "Test",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        manager.load_tools()

        assert len(manager._tool_cache) > 0

        manager.clear_cache()

        assert len(manager._tool_cache) == 0

    def test_clear_cache_empties_module_cache(self, tmp_path):
        """Test that clear_cache empties the module cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "py_cache.py"
        tool_code = '''
def describe():
    return {
        "name": "py_cache",
        "description": "Test",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        manager.load_tools()

        assert len(manager._module_cache) > 0

        manager.clear_cache()

        assert len(manager._module_cache) == 0

    def test_clear_cache_removes_from_sys_modules(self, tmp_path):
        """Test that clear_cache removes modules from sys.modules."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "sys_module_test.py"
        tool_code = '''
def describe():
    return {
        "name": "sys_module_test",
        "description": "Test",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        manager.load_tools()

        module_name = f"anthropide_tool_{tool_file.stem}"
        assert module_name in sys.modules

        manager.clear_cache()

        assert module_name not in sys.modules


class TestToolCaching:
    """Test tool caching behavior."""

    def test_tool_cached_after_load(self, tmp_path):
        """Test that tools are cached after loading."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "cache_test.json"
        tool_data = {
            "name": "cache_test",
            "description": "Test caching",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)

        assert len(manager._tool_cache) == 0

        manager.load_tools()

        assert len(manager._tool_cache) == 1
        assert "cache_test" in manager._tool_cache

    def test_get_tool_uses_cache(self, tmp_path):
        """Test that get_tool uses cached version."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "cached.json"
        tool_data = {
            "name": "cached",
            "description": "Original",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        manager.load_tools()

        # Modify file after loading
        tool_data["description"] = "Modified"
        tool_file.write_text(json.dumps(tool_data))

        # Get tool should return cached version
        tool = manager.get_tool("cached")

        assert tool.description == "Original"

    def test_python_module_cached_after_load(self, tmp_path):
        """Test that Python modules are cached."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "py_cached.py"
        tool_code = '''
def describe():
    return {
        "name": "py_cached",
        "description": "Test",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        manager.load_tools()

        module_name = f"anthropide_tool_{tool_file.stem}"
        assert module_name in manager._module_cache
        assert module_name in sys.modules


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_tools_directory(self, tmp_path):
        """Test handling of empty tools directory."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        manager = ToolManager(project_path)
        tools = manager.load_tools()

        assert len(tools) == 0
        assert len(manager.list_tools()) == 0

    def test_load_tools_with_python_duplicate_names(self, tmp_path, caplog):
        """Test loading Python tools with duplicate names."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create two Python tools with same name
        tool1 = tools_dir / "tool1.py"
        tool1_code = '''
def describe():
    return {
        "name": "duplicate_py_name",
        "description": "First tool",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool1.write_text(tool1_code)

        tool2 = tools_dir / "tool2.py"
        tool2_code = '''
def describe():
    return {
        "name": "duplicate_py_name",
        "description": "Second tool",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool2.write_text(tool2_code)

        manager = ToolManager(project_path)

        with caplog.at_level(logging.WARNING):
            tools = manager.load_tools()

        # Should only load the first one
        assert len(tools) == 1
        assert "duplicate_py_name" in tools

    def test_load_tools_with_python_error(self, tmp_path, caplog):
        """Test loading Python tools with errors continues loading others."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        # Create valid Python tool
        valid_file = tools_dir / "valid.py"
        valid_code = '''
def describe():
    return {
        "name": "valid_py",
        "description": "Valid",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        valid_file.write_text(valid_code)

        # Create invalid Python tool
        invalid_file = tools_dir / "invalid.py"
        invalid_code = '''
def describe():
    raise ValueError("Error in describe")
'''
        invalid_file.write_text(invalid_code)

        manager = ToolManager(project_path)

        with caplog.at_level(logging.ERROR):
            tools = manager.load_tools()

        # Should load the valid tool and skip the invalid one
        assert len(tools) == 1
        assert "valid_py" in tools

    def test_get_tool_scans_python_files(self, tmp_path):
        """Test get_tool scans for Python files when not in cache."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "scan_test.py"
        tool_code = '''
def describe():
    return {
        "name": "scan_test",
        "description": "Test scanning",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
'''
        tool_file.write_text(tool_code)

        manager = ToolManager(project_path)
        # Don't call load_tools, force get_tool to scan

        tool = manager.get_tool("scan_test")

        assert tool is not None
        assert tool.name == "scan_test"

    def test_load_json_tool_with_file_read_error(self, tmp_path):
        """Test loading JSON tool with FileReadError."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "test.json"
        tool_file.write_text('{"name": "test"}')

        manager = ToolManager(project_path)

        # Mock safe_read_json to raise FileReadError
        from lib.file_operations import FileReadError

        with patch('lib.tool_manager.safe_read_json', side_effect=FileReadError("Read error")):
            with pytest.raises(ToolLoadError) as exc_info:
                manager.load_json_tool(tool_file)

            assert "failed to read" in str(exc_info.value).lower()

    def test_validate_tool_schema_catches_exception(self, tmp_path):
        """Test validate_tool_schema catches unexpected exceptions."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        manager = ToolManager(project_path)

        # Create data that will cause an exception in Pydantic validation
        tool_data = {
            "name": 123,  # Should be string
            "description": "Test",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }

        with pytest.raises(ToolValidationError):
            manager.validate_tool_schema(tool_data)

    def test_tools_with_unicode_names(self, tmp_path):
        """Test handling tools with unicode characters in names."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "unicode_tool.json"
        tool_data = {
            "name": "unicode_tool",
            "description": "Tool with unicode: αβγ 你好",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data, ensure_ascii=False))

        manager = ToolManager(project_path)
        tool = manager.load_json_tool(tool_file)

        assert "αβγ" in tool.description or "你好" in tool.description

    def test_tool_with_complex_input_schema(self, tmp_path):
        """Test tool with complex nested input schema."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "complex.json"
        tool_data = {
            "name": "complex",
            "description": "Complex schema",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nested": {
                        "type": "object",
                        "properties": {
                            "deep": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["nested"],
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)
        tool = manager.load_json_tool(tool_file)

        assert "nested" in tool.input_schema["properties"]

    def test_multiple_load_tools_calls(self, tmp_path):
        """Test calling load_tools multiple times."""
        project_path = tmp_path / "test_project"
        tools_dir = project_path / "tools"
        tools_dir.mkdir(parents=True)

        tool_file = tools_dir / "test.json"
        tool_data = {
            "name": "test",
            "description": "Test",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        }
        tool_file.write_text(json.dumps(tool_data))

        manager = ToolManager(project_path)

        tools1 = manager.load_tools()
        tools2 = manager.load_tools()

        assert len(tools1) == len(tools2)
        assert len(manager._tool_cache) == 1
