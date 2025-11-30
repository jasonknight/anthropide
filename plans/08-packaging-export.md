# Plan 08: Packaging and Export System

## Overview
This plan implements the project packaging and export functionality, allowing users to package their prompts as distributable zip files that can be run standalone via the CLI. It includes export/import API endpoints, package configuration management, and the UI for configuring packaging options.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Plan 02 (Project and Session Management) completed
- Plan 04 (Tools System) completed
- Plan 05 (Agents and Skills) completed
- Plan 07 (CLI Runner) completed
- CLI runner working

## Module Dependencies
- lib/project_manager.py
- cli/main.py
- run_project.py

## Tasks

### Task 8.1: Packager Implementation

#### 8.1.1 - Implement: Packager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/packager.py created with Packager class:
  - `__init__(project_path)` - initialize with project directory
  - `export_project(output_path, options)` - creates zip archive:
    - Includes all project files (agents, skills, tools, snippets, tests)
    - Includes current_session.json
    - Includes project.json (with package_config)
    - Includes requirements.txt
    - Copies CLI runner script (run_project.py)
    - Copies lib/ directory (core libraries)
    - Copies cli/ directory (CLI components)
    - Creates README_PACKAGED.md with usage instructions
    - Handles API key based on strategy:
      - `embedded` - creates .api_key file with key
      - Other strategies - no key file, instructions in README
  - `validate_package(zip_path)` - validates zip structure
  - `list_package_contents(zip_path)` - lists files in package
  - Options:
    - `api_key` - for embedded strategy
    - `include_backups` - include session backups (default: false)
    - `compress_level` - compression level (default: 9)
- Error handling for:
  - Missing files
  - Disk space errors
  - Permission errors
  - Invalid paths

**Files to Create**:
- `lib/packager.py`

#### 8.1.2 - Test: Packager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Packager:
  - Exporting project to zip
  - Validating package structure
  - Listing package contents
  - Different API key strategies
  - Including/excluding backups
  - Error cases (missing files, disk full, etc.)
- Create test project
- Verify zip contents
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_packager.py`

#### 8.1.3 - Validate: Packager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Package structure is correct
- All necessary files are included
- API key handling is secure
- Compression works correctly
- Error handling is comprehensive
- No data corruption

---

### Task 8.2: Importer Implementation

#### 8.2.1 - Implement: Importer class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/importer.py created with Importer class:
  - `__init__(projects_root)` - initialize with projects directory
  - `import_project(zip_path, options)` - extracts and validates project:
    - Validates zip structure
    - Extracts to temporary directory first
    - Validates project structure
    - Checks for name conflicts
    - Moves to projects directory
    - Returns project name
  - `validate_import(zip_path)` - pre-validates before import
  - Options:
    - `rename_if_exists` - auto-rename if conflict (default: true)
    - `validate_dependencies` - check requirements.txt (default: false)
- Error handling:
  - Invalid zip file
  - Missing required files
  - Name conflicts
  - Invalid project structure
  - Extraction errors

**Files to Create**:
- `lib/importer.py`

#### 8.2.2 - Test: Importer tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for Importer:
  - Importing valid package
  - Importing invalid package
  - Name conflict handling
  - Validation before import
  - Error cases (corrupt zip, missing files, etc.)
- Create test packages
- Use pytest tmpdir
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_importer.py`

#### 8.2.3 - Validate: Importer review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Import process is safe
  - Validation is thorough
- Name conflict resolution works
- Error handling is comprehensive
- No security vulnerabilities (zip bombs, path traversal)

---

### Task 8.3: Package Configuration Management

#### 8.3.1 - Implement: PackageConfigManager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/package_config_manager.py created with PackageConfigManager class:
  - `__init__(project_path)` - initialize
  - `load_config()` - loads package_config from project.json
  - `save_config(config)` - saves package_config to project.json
  - `validate_config(config)` - validates configuration
  - `get_api_key_strategy()` - returns current strategy
  - `set_api_key_strategy(strategy)` - updates strategy
  - `get_dependencies_checked()` - returns dependency check setting
  - `set_dependencies_checked(enabled)` - updates setting
- Validates API key strategy values
- Warns if embedded strategy is used
- Updates project.json atomically

**Files to Create**:
- `lib/package_config_manager.py`

#### 8.3.2 - Test: PackageConfigManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for PackageConfigManager:
  - Loading/saving configuration
  - Validating configuration
  - Getting/setting strategies
  - Getting/setting dependency check
  - Error cases (invalid strategy, file errors)
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_package_config_manager.py`

#### 8.3.3 - Validate: PackageConfigManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Configuration management is reliable
- Validation is comprehensive
- File operations are safe
- API is clear

---

### Task 8.4: Export API Endpoint

#### 8.4.1 - Implement: Project export endpoint
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `POST /api/projects/<name>/export` - exports project as zip
  - Request body (optional):
    ```json
    {
      "api_key": "optional_for_embedded",
      "include_backups": false
    }
    ```
  - Uses Packager to create zip
  - Returns zip file as binary download
  - Sets appropriate headers:
    - Content-Type: application/zip
    - Content-Disposition: attachment; filename=project_name.zip
  - Temporary file cleanup after download
  - Error handling:
    - Project not found
    - Export errors
    - Missing API key (if embedded strategy)

**Files to Modify**:
- `app.py`

#### 8.4.2 - Test: Export endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for export endpoint:
  - Exporting project
  - Downloading zip file
  - Verifying zip contents
  - Different API key strategies
  - Error cases (missing project, etc.)
- Use pytest with Bottle test client
- Tests pass

**Files to Create**:
- `tests/test_api_export.py`

#### 8.4.3 - Validate: Export endpoint review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Export endpoint works correctly
- Zip file is valid
- Downloads work properly
- Error handling is comprehensive
- Temporary files are cleaned up

---

### Task 8.5: Import API Endpoint

#### 8.5.1 - Implement: Project import endpoint
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `POST /api/projects/import` - imports project from zip
  - Request: multipart/form-data with zip file upload
  - Optional query params:
    - `rename_if_exists=true/false`
  - Uses Importer to extract and validate
  - Returns project name and status
  - Response:
    ```json
    {
      "success": true,
      "project_name": "imported_project",
      "renamed": false
    }
    ```
  - Error handling:
    - Invalid zip file
    - Upload errors
    - Import errors
    - Name conflicts (if rename disabled)

**Files to Modify**:
- `app.py`

#### 8.5.2 - Test: Import endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for import endpoint:
  - Importing valid package
  - Importing invalid package
  - Name conflict handling
  - Error cases
- Create test zip files
- Use pytest with Bottle test client
- Tests pass

**Files to Create**:
- `tests/test_api_import.py`

#### 8.5.3 - Validate: Import endpoint review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Import endpoint works correctly
- File upload is reliable
- Validation prevents broken imports
- Error handling is comprehensive

---

### Task 8.6: Package Config API Endpoints

#### 8.6.1 - Implement: Package configuration endpoints
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `GET /api/projects/<name>/package-config` - get package configuration
  - `POST /api/projects/<name>/package-config` - save package configuration
  - Request body:
    ```json
    {
      "api_key_strategy": "cli_argument",
      "dependencies_checked": true
    }
    ```
  - Uses PackageConfigManager
  - Validates configuration before saving
  - Returns current configuration
  - Error handling

**Files to Modify**:
- `app.py`

#### 8.6.2 - Test: Package config endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for package config endpoints:
  - Getting configuration
  - Saving configuration
  - Validation
  - Error cases
- Tests pass

**Files to Create**:
- `tests/test_api_package_config.py`

#### 8.6.3 - Validate: Package config endpoints review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Endpoints work correctly
- Configuration is validated
- Error handling is comprehensive

---

### Task 8.7: Package Config UI Modal

#### 8.7.1 - Implement: Package configuration modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/project.js:
  - `showPackageConfigModal()` - opens config modal
  - Modal layout:
    - API Key Strategy radio buttons:
      - CLI Argument (default, recommended)
      - Environment File
      - Embedded (with warning ⚠️)
      - Prompt User
    - Dependency check checkbox
    - requirements.txt preview (first 10 lines)
    - [Edit requirements.txt] button (opens CodeMirror modal)
    - Save/Cancel buttons
  - Warning dialog for embedded strategy:
    - "API keys will be stored in plain text. Only use for trusted distribution."
  - Save calls package-config API endpoint
  - Accessible from Project menu: "Package Settings..."

**Files to Modify**:
- `static/js/project.js`

#### 8.7.2 - Test: Package config modal functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal opens correctly
- Radio buttons work
- Warning appears for embedded strategy
- requirements.txt preview shows
- Edit button opens requirements editor
- Save operation works
- API calls are correct

#### 8.7.3 - Validate: Package config modal review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Modal is user-friendly
- Warnings are clear
- requirements.txt editing works
- Validation is helpful

---

### Task 8.8: Export/Import UI

#### 8.8.1 - Implement: Export and import UI components
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/project.js:
  - Export button in header bar:
    - Calls export API endpoint
    - Triggers file download
    - Shows progress spinner
    - Success notification
  - Import button opens file picker:
    - Accept .zip files only
    - Uploads to import API
    - Shows progress bar
    - Success notification with project name
    - Updates project list
    - Switches to imported project
  - Error handling for both operations
  - Confirmation dialogs where appropriate

**Files to Modify**:
- `static/js/project.js`
- `templates/index.html` (add buttons)

#### 8.8.2 - Test: Export/import UI functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Export button works
- File downloads correctly
- Import file picker works
- Upload shows progress
- Project list updates after import
- Error handling works
- UI updates correctly

#### 8.8.3 - Validate: Export/import UI review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- UI is intuitive
- Progress indicators are clear
- Error messages are helpful
- File operations work reliably

---

### Task 8.9: Packaged Project README

#### 8.9.1 - Implement: Generate packaged README
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Update lib/packager.py to generate README_PACKAGED.md:
  - Usage instructions:
    - How to run: `python3 run_project.py <project_path>`
    - Command-line arguments
    - API key setup based on strategy
  - Requirements:
    - Python version
    - Dependencies installation: `pip install -r requirements.txt`
  - Project description (from project.json)
  - Tool descriptions (list of available tools)
  - Agent descriptions (list of available agents)
  - Examples:
    - Interactive mode
    - One-shot mode
    - Test mode
  - Troubleshooting:
    - Common errors and solutions
    - Dependency issues
    - API key issues
- Template-based generation
- Clear and professional formatting

**Files to Modify**:
- `lib/packager.py`

**Files to Create**:
- `templates/README_PACKAGED.md.template`

#### 8.9.2 - Test: README generation test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Test README generation for different projects
- Verify all sections are included
- Verify API key instructions match strategy
- Ensure markdown is valid

**Files to Modify**:
- `tests/test_packager.py`

#### 8.9.3 - Validate: README quality review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- README is comprehensive
- Instructions are clear
- Examples are correct
- Formatting is professional

---

## Integration Tests

### Task 8.10: Packaging System Integration Test

#### 8.10.1 - Implement: End-to-end packaging test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies:
  1. Create test project with all components
  2. Configure package settings via API
  3. Export project to zip via API
  4. Verify zip contents
  5. Import zip as new project via API
  6. Verify imported project structure
  7. Extract zip and run CLI on packaged project
  8. Verify CLI works with packaged project
  9. Test different API key strategies
  10. Verify README is accurate
- Uses real file system
- Subprocess to test CLI execution
- Verifies complete workflow

**Files to Create**:
- `tests/integration/test_packaging_system.py`

#### 8.10.2 - Validate: Packaging system validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Complete packaging workflow works
- Exported packages are functional
- Import process is reliable
- CLI works with packaged projects
- Different API key strategies work
- Documentation is accurate
- No data loss

---

## Deliverables

1. Packager class (lib/packager.py)
2. Importer class (lib/importer.py)
3. PackageConfigManager class (lib/package_config_manager.py)
4. Export API endpoint in app.py
5. Import API endpoint in app.py
6. Package config API endpoints in app.py
7. Package config UI modal
8. Export/Import UI components
9. README template for packaged projects
10. All unit tests with >90% coverage
11. Integration test for complete packaging system

## Success Criteria

- All tests pass
- Projects can be exported as zip files
- Zip files contain all necessary components
- Projects can be imported from zip files
- CLI works with packaged projects
- Different API key strategies work correctly
- Package configuration UI is functional
- README is generated and accurate
- No security vulnerabilities
- Code follows Python best practices

## Notes

- Package zip structure:
  ```
  project_name.zip
  ├── run_project.py (CLI entry script)
  ├── lib/ (core libraries)
  ├── cli/ (CLI components)
  ├── project_name/
  │   ├── project.json
  │   ├── current_session.json
  │   ├── requirements.txt
  │   ├── agents/
  │   ├── skills/
  │   ├── tools/
  │   ├── snippets/
  │   ├── tests/
  │   └── .api_key (if embedded strategy)
  └── README_PACKAGED.md
  ```
- API key handling security:
  - Embedded strategy should warn user
  - .api_key file should be in .gitignore
  - Consider encryption for embedded keys (future enhancement)
- Import validation:
  - Check for malicious file paths (../)
  - Verify zip integrity
  - Limit extraction size (prevent zip bombs)
- Future enhancements:
  - Selective export (exclude certain components)
  - Version tracking in packages
  - Package signing for authenticity
  - Automatic dependency detection
  - Multi-project packages
