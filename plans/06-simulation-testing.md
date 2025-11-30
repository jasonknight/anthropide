# Plan 06: Simulation and Testing System

## Overview
This plan implements the test simulation engine that allows testing prompts without calling the Anthropic API. It uses test configuration files to define expected request patterns and canned responses, enabling deterministic testing of prompt workflows.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Plan 02 (Project and Session Management) completed
- Plan 04 (Tools System) completed
- Plan 05 (Agents and Skills) completed
- ExecutionEngine working

## Module Dependencies
- lib/data_models.py (TestConfig, TestCase, TestSequenceItem)
- lib/execution_engine.py
- lib/tool_executor.py

## Tasks

### Task 6.1: Test Configuration Manager

#### 6.1.1 - Implement: TestConfigManager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/test_config_manager.py created with TestConfigManager class:
  - `__init__(project_path)` - initialize with project tests directory
  - `load_test_config()` - loads tests/config.json
  - `save_test_config(config)` - saves test configuration
  - `get_test(test_name)` - returns specific test case
  - `list_tests()` - returns list of test names
  - `validate_config(config)` - validates test configuration structure
- Validates TestConfig using Pydantic model
- Error handling for:
  - Missing config file
  - Invalid JSON
  - Invalid test structure
- Creates default config if not exists

**Files to Create**:
- `lib/test_config_manager.py`

#### 6.1.2 - Test: TestConfigManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for TestConfigManager:
  - Loading valid config
  - Loading invalid config
  - Saving config
  - Getting test by name
  - Listing tests
  - Validation
  - Error cases
- Create test fixtures
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_test_config_manager.py`
- `tests/fixtures/test_configs/` (test configurations)

#### 6.1.3 - Validate: TestConfigManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Config loading is robust
- Validation is comprehensive
- Error messages are helpful
- File operations are safe

---

### Task 6.2: Request Matcher

#### 6.2.1 - Implement: RequestMatcher class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/request_matcher.py created with RequestMatcher class:
  - `match(request, match_rule)` - checks if request matches rule
  - `get_value_at_path(obj, path)` - extracts value using dot notation
  - `match_regex(value, pattern)` - regex matching
  - `match_contains(value, substring)` - substring matching
- Supports dot notation paths:
  - `messages.-1.content.0.text` - last message, first content block text
  - `system.0.text` - first system block text
  - `tools.0.name` - first tool name
- Handles array indexing including negative indices
- Match types:
  - `regex` - value matches regex pattern
  - `contains` - value contains substring
- Error handling for invalid paths

**Files to Create**:
- `lib/request_matcher.py`

#### 6.2.2 - Test: RequestMatcher tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for RequestMatcher:
  - Path extraction (various paths, negative indices)
  - Regex matching
  - Contains matching
  - Error cases (invalid path, missing keys)
  - Complex nested structures
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_request_matcher.py`

#### 6.2.3 - Validate: RequestMatcher review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Path extraction is correct
- Matching logic is accurate
- Error handling is appropriate
- No edge case bugs

---

### Task 6.3: Test Simulator Engine

#### 6.3.1 - Implement: TestSimulator class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/test_simulator.py created with TestSimulator class:
  - `__init__(test_config, tool_executor)` - initialize
  - `simulate(session, test_name)` - simulates session execution
    - Finds matching test case
    - Iterates through test sequence
    - For each sequence item:
      - Checks if current request matches the match rule
      - If match: returns canned response
      - Handles tool_behavior:
        - `mock` - returns mock tool results from config
        - `execute` - executes real tools
        - `skip` - no tool execution
    - Continues until sequence complete or no match
  - `_match_request(request, match_rule)` - uses RequestMatcher
  - `_apply_response(response)` - returns canned response
  - `_handle_tools(tool_uses, tool_behavior, tool_results)` - handles tool execution
- Maintains conversation state (messages array)
- Supports multi-turn conversations
- Returns final response when sequence completes

**Files to Create**:
- `lib/test_simulator.py`

#### 6.3.2 - Test: TestSimulator tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for TestSimulator:
  - Simulating simple test (no tools)
  - Simulating test with tool calls
  - Mock tool behavior
  - Execute tool behavior
  - Skip tool behavior
  - Multi-turn simulation
  - No matching test (error)
  - Partial sequence match
- Create test configurations and sessions
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_test_simulator.py`

#### 6.3.3 - Validate: TestSimulator review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Simulation logic is correct
- Tool handling works properly
- State management is accurate
- Error handling is comprehensive

---

### Task 6.4: Simulate API Endpoint

#### 6.4.1 - Implement: Simulation endpoint
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `POST /api/projects/<name>/simulate` - simulate session execution
  - Request body: `{"test_name": "optional", "stream": true/false}`
  - Loads test configuration from project
  - Uses TestSimulator to simulate session
  - If test_name provided: runs specific test
  - If test_name not provided: tries to auto-match based on request
  - Returns simulated response
  - If stream=true: simulates streaming with delays
  - If stream=false: returns complete response
- Error handling:
  - No test config
  - Test not found
  - No matching test
  - Simulation errors

**Files to Modify**:
- `app.py`

#### 6.4.2 - Test: Simulate endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for simulate endpoint:
  - Simulating with specific test name
  - Simulating with auto-match
  - Simulating with streaming
  - Tool execution in simulation
  - Error cases
- Create test project with test config
- Tests pass

**Files to Create**:
- `tests/test_api_simulate.py`

#### 6.4.3 - Validate: Simulate endpoint review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Simulation endpoint works correctly
- Auto-matching works
- Streaming simulation is realistic
- Error handling is comprehensive

---

### Task 6.5: Test Configuration Editor UI

#### 6.5.1 - Implement: Test config editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/tests.js with:
  - `loadTestConfig()` - fetches test config from API
  - `showTestConfigEditor()` - opens editor modal
  - Modal layout:
    - List of test cases (left panel)
    - Test case editor (right panel)
    - Add/delete test buttons
  - Test case editor:
    - Name input
    - Sequence items list (add/remove/reorder)
    - Each sequence item has:
      - Match rule editor (path, type, pattern/value)
      - Response editor (JSON)
      - Tool behavior dropdown
      - Tool results editor (JSON, optional)
  - Save button saves config via API
- Tests tab in main UI shows list of tests with edit/delete/run buttons

**Files to Create**:
- `static/js/tests.js`

#### 6.5.2 - Test: Test config editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Test config editor modal works
- Test list displays correctly
- Test case editor works
- Sequence items can be added/removed/reordered
- Match rules can be edited
- Responses can be edited
- Save operation works
- API calls are correct

#### 6.5.3 - Validate: Test config editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Editor is functional
- Complex test configs can be created
- UI is not overwhelming
- Validation is helpful

---

### Task 6.6: Test Runner UI

#### 6.6.1 - Implement: Test runner interface
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/tests.js:
  - `runTest(testName)` - runs simulation for specific test
  - Test runner UI:
    - Test list with "Run" buttons
    - Results display area
    - Shows each sequence step
    - Shows matched patterns
    - Shows responses
    - Shows pass/fail status
  - "Run All Tests" button runs all tests sequentially
  - Results summary (X passed, Y failed)
- Integration with session editor:
  - "Test" button next to "Execute" button
  - Opens test selection modal
  - Runs simulation instead of real execution

**Files to Modify**:
- `static/js/tests.js`
- `static/js/session.js`

#### 6.6.2 - Test: Test runner functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Test runner works
- Individual tests can be run
- All tests can be run
- Results display correctly
- Pass/fail detection works
- Integration with session editor works

#### 6.6.3 - Validate: Test runner review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Test runner is user-friendly
- Results are clear
- API calls are correct
- Error handling works

---

### Task 6.7: Example Test Configurations

#### 6.7.1 - Implement: Create example test configurations
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create example tests/config.json for demo project with:
  - Test 1: Simple text response (no tools)
  - Test 2: Single tool call (Read tool)
  - Test 3: Multiple tool calls (Read, Edit)
  - Test 4: Agent spawning via Task tool
  - Test 5: Multi-turn conversation
- Each test demonstrates different features
- Well-documented with comments (where JSON allows)
- Realistic scenarios

**Files to Create**:
- `projects/example_project/tests/config.json`

#### 6.7.2 - Test: Example tests validation
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Run example tests using TestSimulator
- Verify all tests pass
- Verify tests cover main scenarios
- Ensure tests are reproducible

#### 6.7.3 - Validate: Example tests review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Example tests are comprehensive
- Tests demonstrate system capabilities
- Test configuration is well-structured
- Tests are useful for learning

---

## Integration Tests

### Task 6.8: Simulation System Integration Test

#### 6.8.1 - Implement: End-to-end simulation test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies:
  1. Create project with test configuration
  2. Create session with messages
  3. Run simulation via API
  4. Verify canned responses returned
  5. Test mock tool behavior
  6. Test execute tool behavior
  7. Test multi-turn simulation
  8. Test agent spawning in simulation
  9. Verify no real API calls made
  10. Verify deterministic results
- Uses TestSimulator and TestConfigManager
- Verifies complete workflow

**Files to Create**:
- `tests/integration/test_simulation_system.py`

#### 6.8.2 - Validate: Simulation system validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Complete simulation workflow works
- Test configuration is reliable
- Matching logic is accurate
- Tool behaviors work correctly
- No real API calls during simulation
- Results are deterministic

---

## Deliverables

1. TestConfigManager class (lib/test_config_manager.py)
2. RequestMatcher class (lib/request_matcher.py)
3. TestSimulator class (lib/test_simulator.py)
4. Simulate API endpoint in app.py
5. Test config editor UI (static/js/tests.js)
6. Test runner UI
7. Example test configurations
8. All unit tests with >90% coverage
9. Integration test for simulation system
10. Test documentation

## Success Criteria

- All tests pass
- Test configuration can be created and edited
- Simulation executes without API calls
- Matching logic works correctly
- Tool behaviors work as expected
- UI components are functional
- Example tests demonstrate capabilities
- Code follows best practices

## Notes

- Simulation is deterministic - same input always produces same output
- Tool behavior modes:
  - `mock` - fastest, returns canned results
  - `execute` - runs real tools (slower but more realistic)
  - `skip` - no tool execution, just continues
- Request matching uses dot notation for flexibility
- Negative array indices supported (e.g., -1 for last item)
- Simulation can handle recursive agent spawning
- Test configs should be version controlled with projects
- Future: Consider test coverage analysis (which paths exercised)
- Future: Test recording mode (record real API interactions as tests)
