"""
Tool management operations for AnthropIDE.

This module provides the ToolManager class for loading and validating tools,
including both JSON-defined tools and Python custom tools. Supports dynamic
module loading, schema validation, and caching for performance.
"""

import hashlib
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from lib.data_models import ToolSchema
from lib.file_operations import (
    safe_read_json,
    FileReadError,
    FileOperationError,
)
import config

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """Base exception for tool operations."""
    pass


class ToolNotFoundError(ToolError):
    """Exception raised when tool does not exist."""
    pass


class ToolLoadError(ToolError):
    """Exception raised when tool cannot be loaded."""
    pass


class ToolValidationError(ToolError):
    """Exception raised when tool definition is invalid."""
    pass


class ToolManager:
    """
    Manages tool loading and validation.

    This class handles loading tools from a project's tools/ directory,
    supporting both JSON-defined tools and Python custom tools. Provides
    validation, caching, and error handling for tool operations.

    Attributes:
        project_path: Path to the project directory
        tools_dir: Path to the tools/ directory within the project
        _tool_cache: Cache of loaded tool definitions {tool_name: ToolSchema}
        _module_cache: Cache of loaded Python modules {module_name: module}
        _tool_file_map: Maps tool names to their file paths {tool_name: Path}
    """

    def __init__(self, project_path: Path):
        """
        Initialize ToolManager with project tools directory.

        Args:
            project_path: Path to the project directory

        Raises:
            FileOperationError: If tools directory cannot be accessed

        Security Warning:
            Python tools execute arbitrary code with FULL SYSTEM ACCESS.
            Only load tools from trusted sources. Malicious tools can:
            - Read/write any file on the system
            - Execute arbitrary commands
            - Make network requests
            - Access sensitive data
            See load_python_tool() for details.

        Thread Safety:
            This class is NOT thread-safe. External synchronization required
            when used in multi-threaded environments (e.g., web servers).
        """
        self.project_path = Path(project_path)
        self.tools_dir = self.project_path / "tools"
        self._tool_cache: Dict[str, ToolSchema] = {}
        self._module_cache: Dict[str, Any] = {}
        self._tool_file_map: Dict[str, Path] = {}  # Maps tool name to file path
        self._failed_tools: Set[str] = set()  # Track tools that failed to load

        # Generate unique project ID for module namespacing (prevents collisions)
        self._project_id = hashlib.md5(
            str(project_path.absolute()).encode(),
        ).hexdigest()[:8]

        # Ensure tools directory exists
        if not self.tools_dir.exists():
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created tools directory: {self.tools_dir}")

        logger.info(
            f"ToolManager initialized for project: {self.project_path} "
            f"(project_id: {self._project_id})",
        )

    def load_tools(self) -> Dict[str, ToolSchema]:
        """
        Load all tools from the tools/ directory.

        Scans the tools directory for .json and .py files, loads each tool,
        validates it, and caches the result. Tools are loaded in alphabetical
        order for consistency.

        Returns:
            Dictionary mapping tool names to ToolSchema objects

        Raises:
            ToolError: If critical errors occur during loading
        """
        logger.info(f"Loading tools from {self.tools_dir}")

        # Clear cache to ensure fresh load
        self._tool_cache.clear()
        self._module_cache.clear()
        self._tool_file_map.clear()

        # Get all tool files (both .json and .py)
        json_files = sorted(self.tools_dir.glob(f"*{config.TOOL_JSON_EXT}"))
        py_files = sorted(self.tools_dir.glob(f"*{config.TOOL_PY_EXT}"))

        # Track loaded tool names to detect conflicts
        tool_names = set()

        # Load JSON tools
        for tool_file in json_files:
            try:
                tool_def = self.load_json_tool(tool_file)

                # Check for name conflicts
                if tool_def.name in tool_names:
                    logger.warning(
                        f"Duplicate tool name '{tool_def.name}' in {tool_file.name}, skipping"
                    )
                    continue

                tool_names.add(tool_def.name)
                self._tool_cache[tool_def.name] = tool_def
                self._tool_file_map[tool_def.name] = tool_file
                logger.debug(f"Loaded JSON tool: {tool_def.name}")

            except ToolError as e:
                logger.error(f"Failed to load JSON tool {tool_file.name}: {e}")
                # Continue loading other tools
                continue

        # Load Python tools
        for tool_file in py_files:
            try:
                tool_def = self.load_python_tool(tool_file)

                # Check for name conflicts
                if tool_def.name in tool_names:
                    logger.warning(
                        f"Duplicate tool name '{tool_def.name}' in {tool_file.name}, skipping"
                    )
                    continue

                tool_names.add(tool_def.name)
                self._tool_cache[tool_def.name] = tool_def
                self._tool_file_map[tool_def.name] = tool_file
                logger.debug(f"Loaded Python tool: {tool_def.name}")

            except ToolError as e:
                logger.error(f"Failed to load Python tool {tool_file.name}: {e}")
                # Continue loading other tools
                continue

        logger.info(f"Successfully loaded {len(self._tool_cache)} tools")
        return self._tool_cache.copy()

    def load_json_tool(self, path: Path) -> ToolSchema:
        """
        Load a JSON tool definition from file.

        Args:
            path: Path to the JSON tool file

        Returns:
            ToolSchema object representing the tool

        Raises:
            ToolNotFoundError: If file does not exist
            ToolLoadError: If JSON is invalid or cannot be read
            ToolValidationError: If tool schema is invalid
        """
        path = Path(path)

        if not path.exists():
            raise ToolNotFoundError(f"Tool file not found: {path}")

        logger.debug(f"Loading JSON tool from {path}")

        try:
            # Read JSON file
            tool_data = safe_read_json(path)

            # Validate and create ToolSchema
            tool_def = self.validate_tool_schema(tool_data)

            return tool_def

        except FileReadError as e:
            raise ToolLoadError(f"Failed to read JSON tool {path.name}: {e}")
        except json.JSONDecodeError as e:
            raise ToolLoadError(f"Invalid JSON in tool {path.name}: {e}")
        except Exception as e:
            raise ToolLoadError(f"Unexpected error loading JSON tool {path.name}: {e}")

    def load_python_tool(self, path: Path) -> ToolSchema:
        """
        Load a Python tool module and call its describe() function.

        Dynamically imports the Python module, validates it has describe() and
        run() functions, calls describe() to get the tool definition, and validates
        the result.

        SECURITY WARNING:
            This method executes arbitrary Python code from the tool file with
            FULL SYSTEM PRIVILEGES. The tool code runs in the same process as
            AnthropIDE with no sandboxing or restrictions. Malicious tools can:
            - Read/write ANY file on the system
            - Execute arbitrary commands via os.system/subprocess
            - Make network requests
            - Access environment variables and secrets
            - Modify or delete data

            Only load tools from TRUSTED sources. This is acceptable for local
            development tools where the user controls all tool files, but would
            be dangerous if tools could be uploaded by untrusted users.

        Args:
            path: Path to the Python tool file

        Returns:
            ToolSchema object representing the tool

        Raises:
            ToolNotFoundError: If file does not exist
            ToolLoadError: If module cannot be imported or executed
            ToolValidationError: If describe()/run() missing or schema invalid
        """
        path = Path(path)

        if not path.exists():
            raise ToolNotFoundError(f"Tool file not found: {path}")

        logger.debug(f"Loading Python tool from {path}")

        try:
            # Create a unique module name to avoid conflicts between projects
            # Include project_id to prevent collisions when same tool name in different projects
            module_name = f"anthropide_tool_{self._project_id}_{path.stem}"

            # Check if already loaded in module cache
            if module_name in self._module_cache:
                module = self._module_cache[module_name]
            else:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(module_name, path)
                if spec is None or spec.loader is None:
                    raise ToolLoadError(
                        f"Failed to create module spec for {path.name}"
                    )

                module = importlib.util.module_from_spec(spec)

                # Add to sys.modules before executing to support relative imports
                sys.modules[module_name] = module

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    # Clean up sys.modules on failure
                    sys.modules.pop(module_name, None)
                    raise ToolLoadError(
                        f"Failed to execute Python module {path.name}: {e}"
                    )

                # Cache the loaded module
                self._module_cache[module_name] = module

            # Validate module has describe() function
            if not hasattr(module, 'describe'):
                raise ToolValidationError(
                    f"Python tool {path.name} missing required describe() function"
                )

            describe_func = getattr(module, 'describe')
            if not callable(describe_func):
                raise ToolValidationError(
                    f"describe in {path.name} is not callable"
                )

            # Validate module has run() function (required for execution)
            if not hasattr(module, 'run'):
                raise ToolValidationError(
                    f"Python tool {path.name} missing required run() function"
                )

            run_func = getattr(module, 'run')
            if not callable(run_func):
                raise ToolValidationError(
                    f"run in {path.name} is not callable"
                )

            # Call describe() to get tool definition
            try:
                tool_data = describe_func()
            except Exception as e:
                raise ToolLoadError(
                    f"Error calling describe() in {path.name}: {e}"
                )

            # Validate the returned tool definition
            if not isinstance(tool_data, dict):
                raise ToolValidationError(
                    f"describe() in {path.name} must return a dictionary, got {type(tool_data)}"
                )

            # Validate and create ToolSchema
            tool_def = self.validate_tool_schema(tool_data)

            return tool_def

        except ToolError:
            # Re-raise tool errors as-is
            raise
        except Exception as e:
            raise ToolLoadError(f"Unexpected error loading Python tool {path.name}: {e}")

    def validate_tool_schema(self, tool_def: Dict[str, Any]) -> ToolSchema:
        """
        Validate a tool definition against the ToolSchema model.

        Args:
            tool_def: Dictionary containing tool definition

        Returns:
            Validated ToolSchema object

        Raises:
            ToolValidationError: If schema validation fails
        """
        try:
            # Use Pydantic to validate the tool definition
            tool_schema = ToolSchema(**tool_def)

            # Additional validation: ensure input_schema has required structure
            input_schema = tool_schema.input_schema
            if not isinstance(input_schema, dict):
                raise ToolValidationError(
                    f"input_schema must be a dictionary, got {type(input_schema)}"
                )

            # Validate input_schema has 'type' field
            if 'type' not in input_schema:
                raise ToolValidationError(
                    "input_schema missing required 'type' field"
                )

            # Validate input_schema type is 'object' (Anthropic requirement)
            if input_schema.get('type') != 'object':
                raise ToolValidationError(
                    f"input_schema type must be 'object', got '{input_schema.get('type')}'"
                )

            # Validate input_schema has 'properties' field
            if 'properties' not in input_schema:
                raise ToolValidationError(
                    "input_schema missing required 'properties' field"
                )

            if not isinstance(input_schema['properties'], dict):
                raise ToolValidationError(
                    "input_schema 'properties' must be a dictionary"
                )

            logger.debug(f"Validated tool schema: {tool_schema.name}")
            return tool_schema

        except ToolValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            raise ToolValidationError(f"Schema validation failed: {e}")

    def get_tool(self, name: str) -> Optional[ToolSchema]:
        """
        Get a tool definition by name.

        First checks the cache, then attempts to load the tool from disk if
        not cached. If not in cache and file map not available, scans the
        tools directory to find the tool. Returns None if tool is not found.

        Args:
            name: Tool name (from the tool definition, not filename) to retrieve

        Returns:
            ToolSchema object if found, None otherwise

        Note:
            Tools that previously failed to load are tracked and skipped to
            avoid repeated failed load attempts.
        """
        # Check if this tool previously failed to load
        if name in self._failed_tools:
            logger.debug(f"Tool '{name}' previously failed to load, skipping")
            return None

        # Check cache first
        if name in self._tool_cache:
            logger.debug(f"Tool '{name}' found in cache")
            return self._tool_cache[name]

        # Try to load tool from disk using file map
        logger.debug(f"Tool '{name}' not in cache, attempting to load from disk")

        if name in self._tool_file_map:
            tool_path = self._tool_file_map[name]
            try:
                if tool_path.suffix == config.TOOL_JSON_EXT:
                    tool_def = self.load_json_tool(tool_path)
                else:
                    tool_def = self.load_python_tool(tool_path)
                self._tool_cache[name] = tool_def
                return tool_def
            except ToolError as e:
                logger.error(f"Failed to load tool '{name}' from {tool_path}: {e}")
                self._failed_tools.add(name)
                return None

        # File map not available, scan directory for tool files
        # This handles the case where get_tool is called before load_tools
        for tool_file in self.tools_dir.glob(f"*{config.TOOL_JSON_EXT}"):
            try:
                tool_def = self.load_json_tool(tool_file)
                if tool_def.name == name:
                    self._tool_cache[name] = tool_def
                    self._tool_file_map[name] = tool_file
                    return tool_def
            except ToolError:
                continue

        for tool_file in self.tools_dir.glob(f"*{config.TOOL_PY_EXT}"):
            try:
                tool_def = self.load_python_tool(tool_file)
                if tool_def.name == name:
                    self._tool_cache[name] = tool_def
                    self._tool_file_map[name] = tool_file
                    return tool_def
            except ToolError:
                continue

        logger.warning(f"Tool '{name}' not found in {self.tools_dir}")
        return None

    def list_tools(self) -> List[str]:
        """
        Return a list of all available tool names.

        Scans the tools directory for all .json and .py files and returns
        their names (without extensions). Does not load or validate tools,
        making this a lightweight operation.

        Returns:
            List of tool names sorted alphabetically
        """
        tool_names = set()

        # Get JSON tool names
        for json_file in self.tools_dir.glob(f"*{config.TOOL_JSON_EXT}"):
            tool_names.add(json_file.stem)

        # Get Python tool names
        for py_file in self.tools_dir.glob(f"*{config.TOOL_PY_EXT}"):
            tool_names.add(py_file.stem)

        # Return sorted list
        return sorted(tool_names)

    def reload_tool(self, name: str) -> Optional[ToolSchema]:
        """
        Reload a tool from disk, bypassing the cache.

        Useful when a tool has been modified and needs to be reloaded.
        For Python tools, also clears the module cache.

        Args:
            name: Tool name (from the tool definition, not filename) to reload

        Returns:
            ToolSchema object if found and loaded successfully, None otherwise
        """
        logger.info(f"Reloading tool: {name}")

        # Get the file path before clearing cache
        tool_path = self._tool_file_map.get(name)

        # Clear from cache
        self._tool_cache.pop(name, None)

        # Clear Python module from cache if present
        # We need to find the module name from the file path
        if tool_path and tool_path.suffix == config.TOOL_PY_EXT:
            module_name = f"anthropide_tool_{self._project_id}_{tool_path.stem}"
            if module_name in self._module_cache:
                self._module_cache.pop(module_name)
                sys.modules.pop(module_name, None)

        # Clear from failed tools list (allow retry)
        self._failed_tools.discard(name)

        # Load fresh from disk
        return self.get_tool(name)

    def clear_cache(self) -> None:
        """
        Clear all cached tools and modules.

        Useful when tools have been modified or when performing a full reload.
        Also clears the failed tools list to allow retry attempts.
        """
        logger.info("Clearing tool cache")

        # Clear module cache and sys.modules
        for module_name in list(self._module_cache.keys()):
            sys.modules.pop(module_name, None)

        self._tool_cache.clear()
        self._module_cache.clear()
        self._failed_tools.clear()
