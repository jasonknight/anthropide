# Plan 04: Tools System

## Overview
This plan implements the tool loading and execution system, including support for both JSON-defined and Python custom tools. It also implements essential core tools (Read, Edit, Write, Bash, Glob, Grep) needed for the system to be functional.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Plan 02 (Project and Session Management) completed
- Data models defined

## Module Dependencies
- lib/data_models.py
- lib/validator.py
- config.py

## Tasks

### Task 4.1: Tool Manager - Loading and Validation

#### 4.1.1 - Implement: ToolManager class for loading tools
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/tool_manager.py created with ToolManager class:
  - `__init__(project_path)` - initialize with project tools directory
  - `load_tools()` - loads all tools from tools/ directory
  - `load_json_tool(path)` - loads JSON tool definition
  - `load_python_tool(path)` - loads Python tool module
  - `validate_tool_schema(tool_def)` - validates tool definition
  - `get_tool(name)` - returns tool definition by name
  - `list_tools()` - returns list of all tool names
- Handles both .json and .py tool files
- For Python tools:
  - Imports module dynamically
  - Calls describe() function to get tool definition
  - Validates describe() returns correct format
- Error handling for:
  - Missing files
  - Invalid JSON
  - Python import errors
  - Missing describe() function
  - Invalid tool schemas
- Caches loaded tools

**Files to Create**:
- `lib/tool_manager.py`

#### 4.1.2 - Test: ToolManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for ToolManager:
  - Loading JSON tools (valid/invalid)
  - Loading Python tools (valid/invalid)
  - Schema validation
  - Error handling (missing files, import errors)
  - Tool caching
  - Getting tools by name
  - Listing all tools
- Create test fixtures:
  - Valid JSON tool
  - Invalid JSON tool
  - Valid Python tool
  - Invalid Python tool (missing describe, bad return)
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_manager.py`
- `tests/fixtures/tools/` (test tools)

#### 4.1.3 - Validate: ToolManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Tool loading is robust
- Error messages are helpful
- Schema validation is comprehensive
- No security vulnerabilities (code injection, etc.)
- Python import safety

---

### Task 4.2: Tool Executor - Execution Engine

#### 4.2.1 - Implement: ToolExecutor class for running tools
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/tool_executor.py created with ToolExecutor class:
  - `__init__(tool_manager, working_directory)` - initialize
  - `execute_tool(tool_name, parameters)` - executes tool and returns result
  - `execute_python_tool(tool_module, parameters)` - calls run() function
  - `execute_json_tool(tool_def, parameters)` - not implemented (JSON tools are reference only)
  - Error handling:
    - Tool not found
    - Invalid parameters
    - Execution errors
    - Timeout handling (optional for v1)
  - Returns tool result as string
  - Logs all tool executions
- Working directory is set before execution
- For Python tools:
  - Calls run() function with unpacked parameters
  - Captures return value as result
  - Catches exceptions and formats as error result

**Files to Create**:
- `lib/tool_executor.py`

#### 4.2.2 - Test: ToolExecutor tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for ToolExecutor:
  - Executing valid Python tools
  - Error handling (tool not found, invalid params, execution errors)
  - Working directory context
  - Result formatting
  - Exception handling
- Mock tool_manager for testing
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_executor.py`

#### 4.2.3 - Validate: ToolExecutor review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Tool execution is safe
- Error handling is comprehensive
- Working directory is correctly managed
- No security vulnerabilities (command injection, etc.)
- Result formatting is correct

---

### Task 4.3: Core Tool - Read

#### 4.3.1 - Implement: Read tool
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create tools/read.py with:
  - `describe()` - returns tool definition matching spec
  - `run(file_path, offset=None, limit=None)` - reads file
  - Reads file from filesystem
  - Supports optional offset/limit for large files
  - Returns file content with line numbers (cat -n format)
  - Handles:
    - Missing files (returns error)
    - Binary files (returns error or base64)
    - Permission errors
    - Encoding errors (try UTF-8, fallback to latin-1)
- Tool definition matches spec exactly

**Files to Create**:
- `tools/read.py`

#### 4.3.2 - Test: Read tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Read tool:
  - Reading valid files
  - Reading with offset/limit
  - Reading large files
  - Error cases (missing file, binary file, permission denied)
  - Line number formatting
  - Encoding handling
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_read.py`

#### 4.3.3 - Validate: Read tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Tool works correctly for all file types
- Error messages are helpful
- No path traversal vulnerabilities
- Performance is acceptable for large files

---

### Task 4.4: Core Tool - Edit

#### 4.4.1 - Implement: Edit tool
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create tools/edit.py with:
  - `describe()` - returns tool definition
  - `run(file_path, old_string, new_string, replace_all=False)` - edits file
  - Performs exact string replacement
  - If not replace_all and old_string appears multiple times, returns error
  - If replace_all, replaces all occurrences
  - Creates backup before editing (optional)
  - Atomic write (write to temp file, then rename)
  - Handles:
    - Missing files
    - String not found
    - Permission errors
- Returns success message or error

**Files to Create**:
- `tools/edit.py`

#### 4.4.2 - Test: Edit tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Edit tool:
  - Editing files successfully
  - Replace single occurrence
  - Replace all occurrences
  - Error when old_string not unique
  - Error when old_string not found
  - Error cases (missing file, permission denied)
  - Atomic write behavior
- Use pytest tmpdir
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_edit.py`

#### 4.4.3 - Validate: Edit tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Edit operations are safe and atomic
- Error handling is comprehensive
- No data loss scenarios
- String matching is exact (no regex surprises)

---

### Task 4.5: Core Tool - Write

#### 4.5.1 - Implement: Write tool
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create tools/write.py with:
  - `describe()` - returns tool definition
  - `run(file_path, content)` - writes file
  - Creates file if not exists
  - Overwrites if exists (with backup optional)
  - Creates parent directories if needed
  - Atomic write
  - Handles:
    - Permission errors
    - Disk full errors
    - Invalid paths
- Returns success message or error

**Files to Create**:
- `tools/write.py`

#### 4.5.2 - Test: Write tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Write tool:
  - Writing new files
  - Overwriting existing files
  - Creating parent directories
  - Error cases (permission denied, invalid path)
  - Atomic write behavior
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_write.py`

#### 4.5.3 - Validate: Write tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Write operations are safe and atomic
- Directory creation is correct
- No path traversal vulnerabilities
- Error handling is comprehensive

---

### Task 4.6: Core Tool - Bash

#### 4.6.1 - Implement: Bash tool
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create tools/bash.py with:
  - `describe()` - returns tool definition
  - `run(command, timeout=120)` - executes bash command
  - Uses subprocess to execute command
  - Captures stdout and stderr
  - Returns combined output
  - Timeout after specified seconds
  - Working directory is project root or specified directory
  - Handles:
    - Command not found
    - Timeout
    - Non-zero exit codes (not error, just report)
  - Security: No shell injection prevention (user is trusted in this context)
  - Returns: stdout + stderr + exit code

**Files to Create**:
- `tools/bash.py`

#### 4.6.2 - Test: Bash tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Bash tool:
  - Executing simple commands (ls, echo, etc.)
  - Capturing stdout/stderr
  - Exit code handling
  - Timeout handling
  - Error cases
- Use safe test commands
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_bash.py`

#### 4.6.3 - Validate: Bash tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Command execution works correctly
- Output capturing is complete
- Timeout works
- Working directory is correct
- Security implications documented

---

### Task 4.7: Core Tool - Glob

#### 4.7.1 - Implement: Glob tool
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create tools/glob.py with:
  - `describe()` - returns tool definition
  - `run(pattern, path=".")` - finds files matching pattern
  - Uses Python's glob or pathlib for pattern matching
  - Supports ** for recursive matching
  - Returns list of matching file paths (relative to path)
  - Sorted by modification time (newest first)
  - Handles:
    - Invalid patterns
    - Permission errors
  - Example patterns: "*.py", "src/**/*.js", "**/test_*.py"

**Files to Create**:
- `tools/glob.py`

#### 4.7.2 - Test: Glob tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Glob tool:
  - Matching files with various patterns
  - Recursive patterns (**)
  - Sorting by modification time
  - Empty results
  - Error cases (invalid pattern)
- Create test directory structure
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_glob.py`

#### 4.7.3 - Validate: Glob tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Pattern matching works correctly
- Sorting is correct
- No performance issues with large directories
- Error handling is appropriate

---

### Task 4.8: Core Tool - Grep

#### 4.8.1 - Implement: Grep tool
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create tools/grep.py with:
  - `describe()` - returns tool definition
  - `run(pattern, path=".", glob="*", output_mode="files_with_matches")` - searches files
  - Pattern is regex
  - Glob filters which files to search
  - Output modes:
    - "files_with_matches" - just file paths
    - "content" - matching lines with context
    - "count" - count of matches per file
  - Context lines (-A, -B, -C) for content mode
  - Case insensitive option
  - Returns formatted results
  - Uses Python's re module

**Files to Create**:
- `tools/grep.py`

#### 4.8.2 - Test: Grep tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Grep tool:
  - Searching for patterns in files
  - Different output modes
  - Context lines
  - Case sensitivity
  - Glob filtering
  - Error cases (invalid regex)
- Create test files with content
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_tool_grep.py`

#### 4.8.3 - Validate: Grep tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Search functionality is correct
- Regex handling is safe
- Output formatting is clear
- Performance is acceptable

---

### Task 4.9: Tool Management API Endpoints

#### 4.9.1 - Implement: Tool API endpoints
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `GET /api/projects/<name>/tools` - list all tools in project
  - `GET /api/projects/<name>/tools/<tool_name>` - get tool definition
  - `POST /api/projects/<name>/tools` - create new tool (JSON or Python)
  - `PUT /api/projects/<name>/tools/<tool_name>` - update tool
  - `DELETE /api/projects/<name>/tools/<tool_name>` - delete tool
- Uses ToolManager for operations
- Returns:
  - Tool definitions (from describe() for Python tools)
  - Tool source code for editing
  - Error messages
- Validates tool schemas before saving
- Handles file extensions correctly (.json vs .py)

**Files to Modify**:
- `app.py`

#### 4.9.2 - Test: Tool API endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for tool endpoints:
  - Listing tools
  - Getting tool definition
  - Creating JSON tool
  - Creating Python tool
  - Updating tools
  - Deleting tools
  - Error cases (invalid tool, missing tool, invalid schema)
- Use pytest with Bottle test client
- Tests pass with good coverage

**Files to Create**:
- `tests/test_api_tools.py`

#### 4.9.3 - Validate: Tool API review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- All endpoints work correctly
- Tool loading/saving is reliable
- Validation prevents broken tools
- Error handling is comprehensive
- File operations are safe

---

### Task 4.10: Tool Editor UI Components

#### 4.10.1 - Implement: Tool editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/tools.js with:
  - `loadTools()` - fetches tools from API
  - `showToolEditor(toolName)` - opens editor modal
  - For JSON tools:
    - Form with name, description, input_schema (JSON editor)
  - For Python tools:
    - CodeMirror editor with Python mode
    - Read-only name (from filename)
    - Syntax highlighting
  - Save button validates and saves via API
  - Delete button confirms and deletes
  - Test button (optional) calls describe() and validates
- Tools tab in main UI shows list of tools with edit/delete buttons

**Files to Create**:
- `static/js/tools.js`

#### 4.10.2 - Test: Tool editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Tool editor modal works
- JSON tool editing works
- Python tool editing works
- Save/delete operations work
- Validation prevents invalid tools
- API calls are correct

#### 4.10.3 - Validate: Tool editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Editor is functional
- CodeMirror configuration is appropriate
- Validation is helpful
- UI is intuitive

---

## Integration Tests

### Task 4.11: Tools System Integration Test

#### 4.11.1 - Implement: End-to-end tool system test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies:
  1. Create project with tools directory
  2. Create JSON tool via API
  3. Create Python tool via API
  4. Load tools via ToolManager
  5. Execute Read tool on test file
  6. Execute Edit tool on test file
  7. Execute Write tool to create file
  8. Execute Bash tool to run command
  9. Execute Glob tool to find files
  10. Execute Grep tool to search files
  11. Verify all tools work correctly
  12. Delete tools via API
- Uses real file system and tool execution

**Files to Create**:
- `tests/integration/test_tools_system.py`

#### 4.11.2 - Validate: Tools system validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Complete tool workflow works
- All core tools function correctly
- Tool loading is reliable
- Tool execution is safe
- No security vulnerabilities
- Performance is acceptable

---

## Deliverables

1. ToolManager class (lib/tool_manager.py)
2. ToolExecutor class (lib/tool_executor.py)
3. Core tools:
   - Read (tools/read.py)
   - Edit (tools/edit.py)
   - Write (tools/write.py)
   - Bash (tools/bash.py)
   - Glob (tools/glob.py)
   - Grep (tools/grep.py)
4. Tool API endpoints in app.py
5. Tool editor UI (static/js/tools.js)
6. All unit tests with >90% coverage
7. Integration test for complete tool system
8. Tool documentation

## Success Criteria

- All tests pass
- All core tools work correctly
- Tool loading system is robust
- Tool execution is safe
- API endpoints work correctly
- UI tool editor is functional
- No security vulnerabilities
- Code follows Python best practices

## Notes

- Tools run in the project's root directory (web app) or CLI invocation directory
- No sandboxing in v1 - tools have full system access
- Tool execution timeout: 120 seconds default
- Python tools must have describe() and run() functions
- JSON tools are reference-only (not executable)
- Error results should be formatted clearly
- All tool operations should be logged
- Consider adding more core tools in future (WebFetch, etc.)
