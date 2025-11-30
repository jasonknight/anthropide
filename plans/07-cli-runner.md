# Plan 07: CLI Runner

## Overview
This plan implements the standalone CLI runner that can execute packaged projects outside the web application. The CLI loads a project, initializes tools and agents, and runs interactive conversations with the Anthropic API.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Plan 02 (Project and Session Management) completed
- Plan 04 (Tools System) completed
- Plan 05 (Agents and Skills) completed
- Plan 06 (Simulation and Testing) completed
- ExecutionEngine working

## Module Dependencies
- lib/execution_engine.py
- lib/project_manager.py
- lib/tool_manager.py
- lib/agent_manager.py
- lib/skill_manager.py
- lib/test_simulator.py

## Tasks

### Task 7.1: CLI Project Loader

#### 7.1.1 - Implement: CLIProjectLoader class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- cli/project_loader.py created with CLIProjectLoader class:
  - `__init__(project_path)` - initialize with project directory
  - `load_project()` - loads project metadata and validates structure
  - `load_session()` - loads current_session.json
  - `get_api_key(strategy)` - gets API key based on strategy:
    - `cli_argument` - from argument or env var
    - `env_file` - from .env file in project
    - `embedded` - from .api_key file
    - `prompt` - prompts user and optionally saves
  - `check_dependencies(skip_check)` - verifies requirements.txt dependencies
  - Error handling:
    - Missing project files
    - Invalid project structure
    - Missing dependencies
    - No API key

**Files to Create**:
- `cli/__init__.py`
- `cli/project_loader.py`

#### 7.1.2 - Test: CLIProjectLoader tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for CLIProjectLoader:
  - Loading valid project
  - Loading invalid project
  - Loading session
  - API key strategies (mock user input)
  - Dependency checking (mock subprocess)
  - Error cases
- Use pytest tmpdir for test projects
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_cli_project_loader.py`

#### 7.1.3 - Validate: CLIProjectLoader review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Project loading is robust
- API key handling is secure
- Dependency checking is reliable
- Error messages are helpful

---

### Task 7.2: Conversation History Manager

#### 7.2.1 - Implement: ConversationHistory class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- cli/history.py created with ConversationHistory class:
  - `__init__(history_file_path)` - initialize with log file path
  - `append_message(role, content)` - adds message to history
  - `append_tool_use(tool_name, parameters)` - logs tool call
  - `append_tool_result(tool_name, result)` - logs tool result
  - `append_agent_spawn(agent_name, prompt)` - logs agent spawning
  - `get_history()` - returns full history
  - `save()` - saves history to file
  - `load()` - loads history from file
  - `clear()` - clears history
- History format: timestamped log entries
- Optional: JSON format for programmatic access
- Creates history file if not exists

**Files to Create**:
- `cli/history.py`

#### 7.2.2 - Test: ConversationHistory tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for ConversationHistory:
  - Appending messages
  - Appending tool calls
  - Appending agent spawns
  - Saving/loading history
  - Clearing history
  - File operations
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_cli_history.py`

#### 7.2.3 - Validate: ConversationHistory review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- History logging is reliable
- File operations are safe
- Format is clear and useful
- No performance issues

---

### Task 7.3: CLI Interactive Runner

#### 7.3.1 - Implement: InteractiveRunner class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- cli/interactive.py created with InteractiveRunner class:
  - `__init__(execution_engine, history, verbose)` - initialize
  - `run()` - starts interactive REPL loop:
    - Displays prompt: "You: "
    - Reads user input
    - Adds user message to session
    - Calls execution_engine.execute_session()
    - Streams assistant response to stdout
    - Logs to history
    - Continues until user types "exit" or Ctrl+D
  - `display_streaming_response(stream)` - handles streaming output
  - `display_tool_use(tool_name, params)` - shows tool calls
  - `display_tool_result(result)` - shows tool results
  - Commands:
    - `/exit` - quit
    - `/clear` - clear conversation history
    - `/history` - show conversation log
    - `/save` - save session
    - `/help` - show commands
  - Handles Ctrl+C gracefully (confirm exit)

**Files to Create**:
- `cli/interactive.py`

#### 7.3.2 - Test: InteractiveRunner tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for InteractiveRunner:
  - Running conversation loop (mock input/output)
  - Handling commands (/exit, /clear, /history, /save, /help)
  - Streaming display
  - Tool call display
  - Ctrl+C handling (mock signal)
  - Error handling
- Mock execution_engine responses
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_cli_interactive.py`

#### 7.3.3 - Validate: InteractiveRunner review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Interactive mode is user-friendly
- Commands work correctly
- Streaming is smooth
- Error handling is appropriate
- Exit handling is graceful

---

### Task 7.4: CLI Main Entry Point

#### 7.4.1 - Implement: CLI main function and argument parsing
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- cli/main.py created with:
  - `main()` - main entry point
  - Argument parsing using argparse:
    - `project_path` - positional, required
    - `--api-key` - API key (optional, can use env var)
    - `--input` / `-i` - input message for one-shot mode (optional)
    - `--history` - history file path (optional, default: project/conversation.log)
    - `--test` - run in test/simulation mode
    - `--skip-dependency-check` - skip dependency validation
    - `--verbose` / `-v` - verbose output
  - Workflow:
    1. Parse arguments
    2. Load project using CLIProjectLoader
    3. Check dependencies (unless skipped or disabled in config)
    4. Get API key
    5. Initialize Anthropic client
    6. Load managers (tool, agent, skill)
    7. Initialize execution engine
    8. If --test: use TestSimulator instead of real API
    9. If --input: run one-shot mode
    10. Else: run interactive mode
  - Error handling with helpful messages
  - Logging based on --verbose flag

**Files to Create**:
- `cli/main.py`

#### 7.4.2 - Test: CLI main function tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for CLI main:
  - Parsing arguments (valid/invalid)
  - Loading project
  - One-shot mode (mock API)
  - Interactive mode (mock input)
  - Test mode (simulation)
  - Error handling (missing project, no API key, etc.)
- Mock Anthropic API and user input
- Tests pass

**Files to Create**:
- `tests/test_cli_main.py`

#### 7.4.3 - Validate: CLI main review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- CLI interface is intuitive
- Argument parsing is correct
- Error messages are helpful
- All modes work correctly
- Code is production-ready

---

### Task 7.5: CLI Entry Script

#### 7.5.1 - Implement: Standalone CLI script
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Create run_project.py at project root:
  - Shebang: `#!/usr/bin/env python3`
  - Adds project lib/ to Python path
  - Imports cli.main and calls main()
  - Handles import errors with helpful message
  - Executable permissions
- Simple wrapper that can be packaged with projects
- No dependencies on web app components

**Files to Create**:
- `run_project.py`

#### 7.5.2 - Test: CLI entry script test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Manual testing:
  - Script is executable
  - Runs without errors
  - Shows help message with --help
  - Can run example project
- Integration test that invokes script

**Files to Create**:
- Add to `tests/integration/test_cli_integration.py`

#### 7.5.3 - Validate: CLI entry script review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Script is simple and robust
- Error handling is clear
- Works as standalone entry point

---

### Task 7.6: CLI Help and Documentation

#### 7.6.1 - Implement: Comprehensive CLI help
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Enhance cli/main.py argparse with:
  - Detailed help messages for each argument
  - Usage examples in epilog
  - Version information
- Create CLI_README.md with:
  - Installation instructions
  - Usage guide
  - Examples (one-shot, interactive, test mode)
  - Command reference
  - Troubleshooting guide
  - API key setup instructions

**Files to Create**:
- `CLI_README.md`

**Files to Modify**:
- `cli/main.py`

#### 7.6.2 - Test: CLI help output
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Run --help and verify output
- Check that examples work
- Verify documentation is accurate and complete

#### 7.6.3 - Validate: CLI documentation review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Help messages are clear
- Documentation is comprehensive
- Examples are correct
- Troubleshooting covers common issues

---

## Integration Tests

### Task 7.7: CLI End-to-End Integration Test

#### 7.7.1 - Implement: Complete CLI workflow test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies:
  1. Create test project with session
  2. Run CLI in test mode (simulation)
  3. Verify interactive mode works (mock input)
  4. Test tool execution in CLI
  5. Test agent spawning in CLI
  6. Verify history logging
  7. Test one-shot mode
  8. Test commands (/exit, /clear, /history, /save)
  9. Verify conversation.log is created
  10. Test --verbose flag
- Uses subprocess to run actual CLI script
- Verifies output and behavior

**Files to Create**:
- `tests/integration/test_cli_integration.py`

#### 7.7.2 - Validate: CLI system validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Complete CLI workflow works
- All modes function correctly
- Tool and agent systems work in CLI
- History logging is reliable
- Error handling is comprehensive
- Performance is acceptable

---

## Deliverables

1. CLIProjectLoader class (cli/project_loader.py)
2. ConversationHistory class (cli/history.py)
3. InteractiveRunner class (cli/interactive.py)
4. CLI main function (cli/main.py)
5. CLI entry script (run_project.py)
6. CLI documentation (CLI_README.md)
7. All unit tests with >90% coverage
8. Integration test for complete CLI workflow

## Success Criteria

- All tests pass
- CLI can load and run projects
- Interactive mode works smoothly
- One-shot mode works
- Test/simulation mode works
- Tool execution works in CLI
- Agent spawning works in CLI
- History logging works
- API key handling is secure
- Documentation is complete
- Code follows Python best practices

## Notes

- CLI should be completely independent of web app (no Flask/Bottle dependencies)
- Interactive mode is prioritized for initial implementation
- Streaming mode can be added later if needed
- Working directory for tools is where CLI is invoked (not project directory)
- CLI should handle Ctrl+C and Ctrl+D gracefully
- Conversation history is optional (flag to disable)
- Test mode uses TestSimulator (no API calls)
- Future: Add streaming mode (pipe to stdout, non-interactive)
- Future: Add session selection (run specific session file)
- Future: Add conversation branching (save/load checkpoints)
- Consider using rich library for better CLI output formatting (optional enhancement)
