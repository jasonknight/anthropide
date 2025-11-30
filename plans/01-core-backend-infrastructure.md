# Plan 01: Core Backend Infrastructure

## Overview
This plan covers the foundational backend components needed for AnthropIDE: configuration, data models, file operations, and the basic Bottle web application structure. This must be completed first as all other modules depend on it.

## Prerequisites
- Python 3.x installed
- Virtual environment set up
- Git repository initialized

## Module Dependencies
- None (this is the foundation)

## Tasks

### Task 1.1: Project Structure and Configuration

#### 1.1.1 - Implement: Create basic project structure and configuration
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Directory structure created per spec (lib/, static/, templates/, cli/, projects/)
- config.py created with all configuration constants
- requirements.txt created with dependencies:
  - bottle>=0.12.25
  - pydantic>=2.0.0
  - anthropic>=0.18.0
  - pytest>=7.4.0
  - pytest-cov>=4.1.0
- README.md with setup instructions
- .gitignore file

**Files to Create**:
- `config.py`
- `requirements.txt`
- `README.md`
- `.gitignore`

#### 1.1.2 - Test: Verify configuration module
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for config.py that verify:
  - All path constants are properly defined
  - Configuration values can be accessed
  - Environment variables are read correctly
- Tests pass with 100% coverage for config.py

**Files to Create**:
- `tests/test_config.py`

#### 1.1.3 - Validate: Configuration integration check
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Configuration module can be imported without errors
- All paths resolve correctly
- No circular dependencies
- Code follows Python best practices

---

### Task 1.2: Pydantic Data Models

#### 1.2.1 - Implement: Create all Pydantic data models
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/data_models.py created with all models from spec:
  - ProjectSettings
  - Project
  - SystemBlock
  - ToolSchema
  - ContentBlock
  - Message
  - Session (with validate() method)
  - AgentConfig
  - SkillConfig
  - TestMatch, TestResponse, TestSequenceItem, TestCase, TestConfig
  - UIState
- All validation logic implemented per spec
- Docstrings for all classes and methods
- Type hints throughout

**Files to Create**:
- `lib/__init__.py`
- `lib/data_models.py`

#### 1.2.2 - Test: Data model validation tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Comprehensive unit tests for each model covering:
  - Valid data creation
  - Invalid data rejection
  - Edge cases (empty lists, None values, boundary values)
  - Session validation logic (role alternation, tool_use_id references, etc.)
  - max_tokens and temperature boundary validation
- Tests pass with >90% coverage for data_models.py

**Files to Create**:
- `tests/test_data_models.py`

#### 1.2.3 - Validate: Data models review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- All models match spec exactly
- Validation logic is comprehensive
- No potential bugs or edge cases missed
- Pydantic validators are correctly implemented
- Error messages are clear and helpful

---

### Task 1.3: File Operations and JSON Handling

#### 1.3.1 - Implement: Safe file operations utility
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/file_operations.py created with:
  - `safe_read_json(path)` - reads JSON with error handling
  - `safe_write_json(path, data)` - writes JSON with atomic operations
  - `create_backup(path, backup_dir, max_backups)` - creates timestamped backups
  - `ensure_directory(path)` - creates directory if not exists
  - File locking mechanism to prevent concurrent writes
  - Proper error handling and logging
- All functions have docstrings and type hints

**Files to Create**:
- `lib/file_operations.py`

#### 1.3.2 - Test: File operations tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for all file operations:
  - Reading valid/invalid JSON files
  - Writing JSON files atomically
  - Creating backups with timestamp format
  - Backup rotation (max_backups enforcement)
  - Directory creation
  - Error handling (missing files, permission errors, invalid JSON)
  - Concurrent write handling
- Use pytest fixtures for temp directories
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_file_operations.py`

#### 1.3.3 - Validate: File operations security review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- File operations are safe and atomic
- No race conditions in file writing
- Proper error handling for all failure modes
- No path traversal vulnerabilities
- Backup rotation works correctly

---

### Task 1.4: Basic Bottle Web Application

#### 1.4.1 - Implement: Bottle app skeleton
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- app.py created with:
  - Bottle application initialization
  - CORS headers configured
  - Error handlers (404, 500)
  - Static file serving configured
  - Health check endpoint: GET /health
  - Root endpoint: GET / (serves index.html)
  - Logging configured using Python logging module
- Templates directory with base.html template:
  - HTML5 structure
  - Bootstrap CSS from CDN
  - jQuery, jQuery UI, CodeMirror from CDN
  - Marked.js for markdown rendering
  - Basic layout structure

**Files to Create**:
- `app.py`
- `templates/base.html`
- `templates/index.html`

#### 1.4.2 - Test: Web application basic tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for app.py:
  - Health check endpoint returns 200
  - Root endpoint serves HTML
  - Static files are accessible
  - 404 errors are handled
  - 500 errors are handled
- Use pytest with bottle testing utilities
- Tests pass with basic coverage

**Files to Create**:
- `tests/test_app.py`
- `tests/conftest.py` (pytest configuration and fixtures)

#### 1.4.3 - Validate: Web application review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Application starts without errors
- All endpoints respond correctly
- Error handling is appropriate
- CORS configuration is correct
- Logging is properly configured
- HTML template structure is valid

---

### Task 1.5: Validator Utility Module

#### 1.5.1 - Implement: Validation utilities
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/validator.py created with:
  - `validate_project_structure(project_path)` - checks directory structure
  - `validate_project_name(name)` - validates project naming rules
  - `validate_agent_name(name)` - validates agent naming rules
  - `validate_tool_schema(schema)` - validates tool JSON schema
  - Returns tuple of (is_valid, errors/missing_items)
- Comprehensive docstrings

**Files to Create**:
- `lib/validator.py`

#### 1.5.2 - Test: Validator tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for all validation functions:
  - Valid inputs pass
  - Invalid inputs fail with appropriate errors
  - Edge cases handled
  - Error messages are descriptive
- Use pytest tmpdir for structure validation tests
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_validator.py`

#### 1.5.3 - Validate: Validator review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Validation logic is complete and correct
- All edge cases are covered
- Error messages are helpful
- No potential for false positives/negatives

---

## Integration Tests

### Task 1.6: Core Infrastructure Integration Test

#### 1.6.1 - Implement: End-to-end core infrastructure test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies:
  - Virtual environment can be created
  - All dependencies install correctly
  - Config module imports and all paths exist
  - Data models can be instantiated and validated
  - File operations work correctly
  - Web application starts and responds to health check
  - All imports work without circular dependencies
- Test creates a temporary project directory structure

**Files to Create**:
- `tests/integration/test_core_infrastructure.py`

#### 1.6.2 - Validate: Core infrastructure validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- All components work together
- No missing dependencies
- No import errors
- Application can start successfully
- Documentation is clear and accurate
- Code quality is production-ready

---

## Deliverables

1. Complete project structure
2. Configuration module (config.py)
3. Data models (lib/data_models.py)
4. File operations (lib/file_operations.py)
5. Validator utilities (lib/validator.py)
6. Basic Bottle application (app.py)
7. HTML templates (templates/base.html, templates/index.html)
8. All unit tests with >90% coverage
9. Integration test for core infrastructure
10. README.md with setup instructions

## Success Criteria

- All tests pass
- Code coverage >90% for core modules
- Application starts without errors
- Health check endpoint returns 200
- All code follows Python best practices (PEP 8)
- Documentation is complete and accurate

## Notes

- This module must be completed before any other modules
- Use Python logging module with console output for this phase
- CDN links for frontend libraries should use specific versions
- Bootstrap version: 5.3.x
- jQuery version: 3.7.x
- jQuery UI version: 1.13.x
- CodeMirror version: 5.65.x
- Marked.js version: 9.x
