# Plan 02: Project and Session Management

## Overview
This plan implements the core project and session management functionality, including CRUD operations for projects, session loading/saving, backup management, and related API endpoints.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Bottle application running
- Data models defined

## Module Dependencies
- lib/data_models.py
- lib/file_operations.py
- lib/validator.py
- config.py

## Tasks

### Task 2.1: Project Manager Implementation

#### 2.1.1 - Implement: ProjectManager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/project_manager.py created with ProjectManager class:
  - `__init__(projects_root)` - initialize with projects directory
  - `list_projects()` - returns list of Project objects
  - `create_project(name, description)` - creates project structure
  - `load_project(name)` - loads and validates project
  - `load_project_metadata(name)` - loads project.json
  - `delete_project(name)` - deletes project directory
  - `_create_missing_files(project_path, missing)` - creates missing structure
  - `_list_agents(project_path)` - returns agent names
  - `_list_skills(project_path)` - returns skill names
  - `_list_tools(project_path)` - returns tool names
  - `_list_snippet_categories(project_path)` - returns categories
- Creates complete directory structure per spec when creating project
- Creates default files (project.json, current_session.json, requirements.txt)
- Proper error handling and logging

**Files to Create**:
- `lib/project_manager.py`

#### 2.1.2 - Test: ProjectManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Comprehensive unit tests:
  - Project creation with valid/invalid names
  - Project listing with multiple projects
  - Project loading and structure validation
  - Project deletion
  - Missing file creation
  - Agent/skill/tool/snippet listing
  - Error cases (duplicate names, invalid paths, permission errors)
- Use pytest tmpdir fixtures
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_project_manager.py`

#### 2.1.3 - Validate: ProjectManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Project operations are atomic (no partial states)
- File structure matches spec exactly
- Error handling is comprehensive
- Default files have correct content
- No security vulnerabilities (path traversal, etc.)

---

### Task 2.2: Session Manager Implementation

#### 2.2.1 - Implement: SessionManager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/session_manager.py created with SessionManager class:
  - `__init__(project_path)` - initialize with project directory
  - `load_session()` - loads current_session.json, returns Session object
  - `save_session(session)` - saves session to current_session.json
  - `create_backup()` - creates timestamped backup
  - `list_backups()` - returns list of backup files with metadata
  - `restore_backup(filename)` - restores backup as current session
  - `delete_backup(filename)` - deletes backup file
  - `rotate_backups(max_backups)` - deletes old backups beyond limit
- Handles JSONDecodeError gracefully (returns None for UI to show raw editor)
- Auto-backup before overwriting current_session.json
- Backup timestamp format: current_session.json.YYYYMMDDHHMMSS
- Uses file_operations.safe_write_json for atomic writes

**Files to Create**:
- `lib/session_manager.py`

#### 2.2.2 - Test: SessionManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for all SessionManager operations:
  - Loading valid/invalid/missing session files
  - Saving sessions
  - Creating backups with correct timestamp format
  - Listing backups sorted by timestamp
  - Restoring backups
  - Deleting backups
  - Backup rotation (keeps only max_backups recent files)
  - Handling concurrent saves
  - JSONDecodeError handling
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_session_manager.py`

#### 2.2.3 - Validate: SessionManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Session operations are safe and atomic
- Backup creation never fails (even on full disk, just logs error)
- Backup rotation works correctly
- No data loss scenarios
- Error handling is comprehensive

---

### Task 2.3: Project API Endpoints

#### 2.3.1 - Implement: Project management API endpoints
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `GET /api/projects` - list all projects
  - `POST /api/projects` - create new project
  - `GET /api/projects/<name>` - load project and verify structure
  - `DELETE /api/projects/<name>` - delete project
- Each endpoint:
  - Uses ProjectManager for operations
  - Returns JSON responses per spec
  - Has proper error handling (400, 404, 500)
  - Logs operations
  - Validates input
- JSON request/response formats match spec exactly

**Files to Modify**:
- `app.py`

#### 2.3.2 - Test: Project API endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for each endpoint:
  - GET /api/projects returns empty list initially
  - POST /api/projects creates project successfully
  - POST /api/projects rejects invalid names
  - GET /api/projects/<name> returns project info
  - GET /api/projects/<name> returns 404 for missing project
  - DELETE /api/projects/<name> deletes project
  - DELETE /api/projects/<name> returns 404 for missing project
- Use pytest with Bottle test client
- Tests pass with good coverage

**Files to Create**:
- `tests/test_api_projects.py`

#### 2.3.3 - Validate: Project API review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- All endpoints follow REST conventions
- Error responses are consistent
- Input validation is thorough
- No security vulnerabilities
- Response formats match spec

---

### Task 2.4: Session API Endpoints

#### 2.4.1 - Implement: Session management API endpoints
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `GET /api/projects/<name>/session` - load current session
  - `POST /api/projects/<name>/session` - save session (auto-save)
  - `POST /api/projects/<name>/session/new` - create new session (backup current)
  - `GET /api/projects/<name>/session/backups` - list backups
  - `POST /api/projects/<name>/session/restore` - restore backup
  - `DELETE /api/projects/<name>/session/backups/<filename>` - delete backup
- Each endpoint:
  - Uses SessionManager for operations
  - Returns JSON responses per spec
  - Has proper error handling
  - Validates session structure (optional validation, doesn't block save)
  - Logs operations

**Files to Modify**:
- `app.py`

#### 2.4.2 - Test: Session API endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for each endpoint:
  - GET session returns default session for new project
  - POST session saves successfully
  - POST session/new creates backup and returns empty session
  - GET backups returns list of backups
  - POST restore loads backup as current
  - DELETE backup removes backup file
  - Error cases (invalid session data, missing project, missing backup)
- Tests verify backup rotation
- Use pytest with Bottle test client

**Files to Create**:
- `tests/test_api_session.py`

#### 2.4.3 - Validate: Session API review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Session endpoints work correctly
- Auto-save doesn't lose data
- Backup system is reliable
- Error handling is appropriate
- No race conditions in save operations

---

### Task 2.5: State Management Implementation

#### 2.5.1 - Implement: Global UI state management
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/state_manager.py created with StateManager class:
  - `__init__(state_file_path)` - initialize with state.json path
  - `load_state()` - loads global UI state
  - `save_state(state)` - saves UI state
  - `get_selected_project()` - returns currently selected project name
  - `set_selected_project(name)` - updates selected project
  - `update_ui_state(path, value)` - updates nested UI state value
- Creates default state.json if not exists
- Uses UIState data model for validation
- API endpoints in app.py:
  - `GET /api/state` - get global UI state
  - `POST /api/state` - save UI state

**Files to Create**:
- `lib/state_manager.py`

**Files to Modify**:
- `app.py`

#### 2.5.2 - Test: State management tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for StateManager:
  - Loading/creating default state
  - Saving state
  - Getting/setting selected project
  - Updating nested UI state values
- Integration tests for API endpoints:
  - GET /api/state returns state
  - POST /api/state saves state
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_state_manager.py`
- Add to `tests/test_app.py`

#### 2.5.3 - Validate: State management review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- State management is reliable
- No data corruption
- UI state structure matches spec
- State file location is correct (app root, not per-project)

---

## Integration Tests

### Task 2.6: Project and Session Integration Test

#### 2.6.1 - Implement: End-to-end project/session workflow test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies complete workflow:
  1. Create new project via API
  2. Verify project structure is created
  3. Load project and get default session
  4. Modify and save session
  5. Create backup
  6. Modify session again
  7. Restore from backup
  8. List all backups
  9. Delete backup
  10. Delete project
- Test verifies data consistency at each step
- Test uses real file system (tmpdir)

**Files to Create**:
- `tests/integration/test_project_session_workflow.py`

#### 2.6.2 - Validate: Project and session management validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Complete workflow works end-to-end
- No data loss in any scenario
- API responses are consistent
- Error handling works correctly
- Performance is acceptable

---

## Deliverables

1. ProjectManager class (lib/project_manager.py)
2. SessionManager class (lib/session_manager.py)
3. StateManager class (lib/state_manager.py)
4. Project API endpoints in app.py
5. Session API endpoints in app.py
6. State API endpoints in app.py
7. All unit tests with >90% coverage
8. Integration test for project/session workflow
9. Updated README with API documentation

## Success Criteria

- All tests pass
- Can create, list, load, and delete projects via API
- Can save, load, backup, and restore sessions via API
- State management works correctly
- No data loss scenarios
- API responses match spec exactly
- Code follows Python best practices

## Notes

- Session saves should never fail (validation is optional/warning only)
- Backup rotation should happen automatically on backup creation
- State file is global (at app root), not per-project
- All API endpoints should use proper HTTP status codes
- Error messages should be clear and actionable
