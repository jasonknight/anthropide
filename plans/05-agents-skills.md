# Plan 05: Agents and Skills System

## Overview
This plan implements the agent and skill management system, including the Task tool for agent spawning, agent/skill loading, CRUD operations, and the UI components for managing agents and skills.

## Prerequisites
- Plan 01 (Core Backend Infrastructure) completed
- Plan 02 (Project and Session Management) completed
- Plan 04 (Tools System) completed
- ToolManager and ToolExecutor working

## Module Dependencies
- lib/data_models.py (AgentConfig, SkillConfig)
- lib/tool_manager.py
- lib/validator.py

## Tasks

### Task 5.1: Skill Manager Implementation

#### 5.1.1 - Implement: SkillManager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/skill_manager.py created with SkillManager class:
  - `__init__(project_path)` - initialize with project skills directory
  - `load_skills()` - loads all skills from skills/ directory
  - `load_skill(name)` - loads single skill markdown file
  - `parse_skill(content)` - parses YAML frontmatter + markdown
  - `save_skill(skill_config)` - saves skill to file
  - `delete_skill(name)` - deletes skill file
  - `list_skills()` - returns list of skill names
  - `get_skill(name)` - returns SkillConfig object
- Parses markdown files with YAML frontmatter
- Validates skill structure
- Caches loaded skills
- Error handling for:
  - Missing files
  - Invalid YAML
  - Missing required fields

**Files to Create**:
- `lib/skill_manager.py`

#### 5.1.2 - Test: SkillManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for SkillManager:
  - Loading skills (valid/invalid)
  - Parsing YAML frontmatter
  - Saving skills
  - Deleting skills
  - Listing skills
  - Error cases (missing file, invalid YAML, missing fields)
- Create test skill fixtures
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_skill_manager.py`
- `tests/fixtures/skills/` (test skills)

#### 5.1.3 - Validate: SkillManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Skill loading is robust
- YAML parsing is correct
- File operations are safe
- Error messages are helpful
- Validation is comprehensive

---

### Task 5.2: Agent Manager Implementation

#### 5.2.1 - Implement: AgentManager class
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/agent_manager.py created with AgentManager class:
  - `__init__(project_path, skill_manager, tool_manager)` - initialize
  - `load_agents()` - loads all agents from agents/ directory
  - `load_agent(name)` - loads single agent markdown file
  - `parse_agent(content)` - parses YAML frontmatter + markdown
  - `save_agent(agent_config)` - saves agent to file
  - `delete_agent(name)` - deletes agent file
  - `list_agents()` - returns list of agent names
  - `get_agent(name)` - returns AgentConfig object
  - `validate_agent(agent_config)` - validates:
    - Tools exist in project
    - Skills exist in project
    - Model is valid (or "inherit")
- Similar to SkillManager but for agents
- Validates agent references to tools/skills

**Files to Create**:
- `lib/agent_manager.py`

#### 5.2.2 - Test: AgentManager tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for AgentManager:
  - Loading agents (valid/invalid)
  - Parsing YAML frontmatter
  - Saving agents
  - Deleting agents
  - Validation (tool/skill existence)
  - Listing agents
  - Error cases
- Mock skill_manager and tool_manager
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_agent_manager.py`
- `tests/fixtures/agents/` (test agents)

#### 5.2.3 - Validate: AgentManager review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Agent loading is robust
- Validation prevents broken references
- File operations are safe
- Error handling is comprehensive

---

### Task 5.3: Task Tool - Agent Spawning

#### 5.3.1 - Implement: Task tool for agent spawning
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/task_tool.py created with TaskTool class:
  - `generate_task_tool_schema(agent_manager)` - generates Task tool definition
    - Enums available agents
    - Includes agent descriptions in tool description
  - `execute_task(agent_name, prompt, context)` - spawns agent
    - Loads agent configuration
    - Creates new Anthropic API request with:
      - Agent's system prompt
      - Agent's skills loaded and cached in system
      - Agent's tools only
      - Agent's model (or inherit from parent)
      - Provided prompt as first user message
    - Executes request (recursive agent support)
    - Returns agent's final response
  - Context includes:
    - Anthropic client
    - ToolManager
    - SkillManager
    - AgentManager
    - Working directory
- Supports recursive agent spawning (agents can spawn sub-agents)
- Stack depth limit (prevent infinite recursion)

**Files to Create**:
- `lib/task_tool.py`

#### 5.3.2 - Test: Task tool tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Unit tests for TaskTool:
  - Generating Task tool schema with agent enums
  - Loading agent configuration
  - Building agent system prompt with skills
  - Tool filtering for agent
  - Model inheritance
  - Error cases (agent not found, invalid agent)
- Mock Anthropic API for testing
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_task_tool.py`

#### 5.3.3 - Validate: Task tool review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Task tool schema is correct
- Agent spawning works correctly
- Skills are loaded into system prompt
- Tool filtering is correct
- Model inheritance works
- Recursion limit prevents infinite loops

---

### Task 5.4: Execution Engine - With Agent Support

#### 5.4.1 - Implement: Enhanced execution engine
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- lib/execution_engine.py created with ExecutionEngine class:
  - `__init__(anthropic_client, project_path)` - initialize
  - `execute_session(session, stream_callback=None)` - executes session
    - Loads all managers (tool, skill, agent)
    - Builds tool list including Task tool
    - Iterative loop for tool calling
    - Calls Anthropic API with streaming
    - Handles tool_use blocks:
      - For Task tool: calls TaskTool.execute_task()
      - For other tools: calls ToolExecutor.execute_tool()
    - Appends assistant response and tool results to messages
    - Continues until no more tool_use blocks
    - Returns final response
  - `_handle_tool_use(tool_name, parameters, context)` - dispatches tool execution
  - Max turns limit (prevent infinite loops)
- Supports streaming via callback
- Handles errors gracefully

**Files to Create**:
- `lib/execution_engine.py`

#### 5.4.2 - Test: Execution engine tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for ExecutionEngine:
  - Executing simple session (no tools)
  - Executing session with tool calls
  - Executing session with Task tool (agent spawning)
  - Streaming callback
  - Max turns limit
  - Error handling
- Mock Anthropic API responses
- Tests pass with >90% coverage

**Files to Create**:
- `tests/test_execution_engine.py`

#### 5.4.3 - Validate: Execution engine review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Execution flow is correct
- Tool calling loop is robust
- Agent spawning works
- Streaming works
- Error handling is comprehensive
- No infinite loops

---

### Task 5.5: Agent API Endpoints

#### 5.5.1 - Implement: Agent management API endpoints
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `GET /api/projects/<name>/agents` - list all agents
  - `GET /api/projects/<name>/agents/<agent_name>` - get agent content
  - `POST /api/projects/<name>/agents` - create new agent
  - `PUT /api/projects/<name>/agents/<agent_name>` - update agent
  - `DELETE /api/projects/<name>/agents/<agent_name>` - delete agent
- Uses AgentManager for operations
- Returns agent YAML + markdown content
- Validates agent structure before saving
- Error handling

**Files to Modify**:
- `app.py`

#### 5.5.2 - Test: Agent API endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for agent endpoints:
  - Listing agents
  - Getting agent content
  - Creating agent
  - Updating agent
  - Deleting agent
  - Error cases (invalid agent, missing agent, invalid references)
- Use pytest with Bottle test client
- Tests pass with good coverage

**Files to Create**:
- `tests/test_api_agents.py`

#### 5.5.3 - Validate: Agent API review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- All endpoints work correctly
- Validation prevents broken agents
- Error handling is comprehensive
- File operations are safe

---

### Task 5.6: Skill API Endpoints

#### 5.6.1 - Implement: Skill management API endpoints
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `GET /api/projects/<name>/skills` - list all skills
  - `GET /api/projects/<name>/skills/<skill_name>` - get skill content
  - `POST /api/projects/<name>/skills` - create new skill
  - `PUT /api/projects/<name>/skills/<skill_name>` - update skill
  - `DELETE /api/projects/<name>/skills/<skill_name>` - delete skill
- Uses SkillManager for operations
- Returns skill metadata + markdown content
- Validates skill structure before saving

**Files to Modify**:
- `app.py`

#### 5.6.2 - Test: Skill API endpoint tests
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for skill endpoints:
  - Listing skills
  - Getting skill content
  - Creating skill
  - Updating skill
  - Deleting skill
  - Error cases
- Tests pass with good coverage

**Files to Create**:
- `tests/test_api_skills.py`

#### 5.6.3 - Validate: Skill API review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- All endpoints work correctly
- Validation is appropriate
- Error handling is comprehensive

---

### Task 5.7: Execution API Endpoint

#### 5.7.1 - Implement: Session execution endpoint
**Agent**: backend-python-implementer
**Acceptance Criteria**:
- Add to app.py:
  - `POST /api/projects/<name>/execute` - execute current session
  - Request body: `{"stream": true/false}`
  - Uses ExecutionEngine to execute session
  - If stream=true: returns Server-Sent Events stream
  - If stream=false: returns complete response as JSON
  - Requires ANTHROPIC_API_KEY environment variable
  - Error handling:
    - Missing API key
    - Invalid session
    - Execution errors
    - Tool errors
- SSE stream format:
  - `data: {"type": "text", "text": "..."}`
  - `data: {"type": "tool_use", "name": "Read", "id": "..."}`
  - `data: {"type": "tool_result", "result": "..."}`
  - `data: {"type": "done"}`

**Files to Modify**:
- `app.py`

#### 5.7.2 - Test: Execution endpoint test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration tests for execution endpoint:
  - Executing simple session
  - Executing with streaming
  - Executing with tools
  - Error cases (missing API key, invalid session)
- Mock Anthropic API
- Tests pass

**Files to Create**:
- `tests/test_api_execute.py`

#### 5.7.3 - Validate: Execution endpoint review
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Execution endpoint works correctly
- Streaming is properly formatted
- Error handling is comprehensive
- API key handling is secure

---

### Task 5.8: Agent Editor UI

#### 5.8.1 - Implement: Agent editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/agents.js with:
  - `loadAgents()` - fetches agents from API
  - `showAgentEditor(agentName)` - opens editor modal
  - Modal layout:
    - YAML fields form (name, description, model, tools, skills, color)
    - CodeMirror editor for markdown prompt content
    - Preview pane showing rendered markdown
  - Multi-select for tools (populated from project tools)
  - Multi-select for skills (populated from project skills)
  - Model dropdown (inherit, or model list)
  - Color picker or dropdown
  - Save/Delete/Cancel buttons
- Agents tab in main UI shows list of agents with edit/delete buttons

**Files to Create**:
- `static/js/agents.js`

#### 5.8.2 - Test: Agent editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Agent editor modal works
- YAML fields populate correctly
- Multi-select for tools/skills works
- CodeMirror editor works
- Preview updates correctly
- Save/delete operations work
- Validation prevents invalid agents

#### 5.8.3 - Validate: Agent editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Editor is functional and intuitive
- Validation is helpful
- Tool/skill selection is clear
- API calls are correct

---

### Task 5.9: Skill Editor UI

#### 5.9.1 - Implement: Skill editor modal
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Create static/js/skills.js with:
  - `loadSkills()` - fetches skills from API
  - `showSkillEditor(skillName)` - opens editor modal
  - Modal layout:
    - Left panel: Metadata form (name, description, version, author)
    - Top right: CodeMirror editor for markdown
    - Bottom right: Preview pane
  - Live preview (debounced 300ms)
  - Save/Delete/Cancel buttons
- Skills tab in main UI shows list of skills with edit/delete buttons

**Files to Create**:
- `static/js/skills.js`

#### 5.9.2 - Test: Skill editor functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Skill editor modal works
- Metadata form works
- CodeMirror editor works
- Preview updates correctly
- Save/delete operations work
- API calls are correct

#### 5.9.3 - Validate: Skill editor review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Editor is functional
- Layout is clear
- Preview is accurate
- Validation works

---

### Task 5.10: Execute Button and Results Display

#### 5.10.1 - Implement: Execute button and streaming results
**Agent**: frontend-js-implementer
**Acceptance Criteria**:
- Add to static/js/session.js:
  - Execute button in session editor
  - `executeSession()` - calls execute endpoint with streaming
  - Results display area below messages:
    - Shows execution progress
    - Displays streamed text
    - Shows tool calls with parameters
    - Shows tool results
    - Shows agent spawning events
  - Stop button to cancel execution
  - Clear results button
  - EventSource for SSE streaming
  - Error handling for execution failures

**Files to Modify**:
- `static/js/session.js`

#### 5.10.2 - Test: Execute functionality
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Execute button works
- Streaming results display correctly
- Tool calls are shown
- Agent spawning is visible
- Stop button works
- Error messages display correctly

#### 5.10.3 - Validate: Execute feature review
**Agent**: frontend-js-validator
**Acceptance Criteria**:
- Execution is smooth
- Results are clearly formatted
- Streaming performance is good
- Error handling is comprehensive

---

## Integration Tests

### Task 5.11: Agents and Skills Integration Test

#### 5.11.1 - Implement: End-to-end agents/skills test
**Agent**: backend-python-tester
**Acceptance Criteria**:
- Integration test that verifies:
  1. Create project
  2. Create skill via API
  3. Create tool via API
  4. Create agent via API (references skill and tool)
  5. Create session with message
  6. Execute session that spawns agent via Task tool
  7. Verify agent executes with correct tools/skills
  8. Verify agent returns result
  9. Verify parent conversation continues
  10. Test recursive agent spawning (agent spawns sub-agent)
- Uses mock Anthropic API responses
- Verifies complete workflow

**Files to Create**:
- `tests/integration/test_agents_skills_workflow.py`

#### 5.11.2 - Validate: Agents and skills system validation
**Agent**: backend-python-validator
**Acceptance Criteria**:
- Complete agent workflow works
- Agent spawning is reliable
- Skills are loaded correctly
- Tool filtering works
- Recursive spawning works
- Error handling is comprehensive

---

## Deliverables

1. SkillManager class (lib/skill_manager.py)
2. AgentManager class (lib/agent_manager.py)
3. TaskTool implementation (lib/task_tool.py)
4. ExecutionEngine class (lib/execution_engine.py)
5. Agent API endpoints in app.py
6. Skill API endpoints in app.py
7. Execute API endpoint in app.py
8. Agent editor UI (static/js/agents.js)
9. Skill editor UI (static/js/skills.js)
10. Execute button and results display
11. All unit tests with >90% coverage
12. Integration test for complete agent/skill workflow

## Success Criteria

- All tests pass
- Agents and skills can be created, edited, deleted
- Task tool spawns agents correctly
- Agents execute with correct tools/skills
- Recursive agent spawning works
- Execution engine handles tool calling correctly
- UI components are functional
- API endpoints work correctly
- Code follows best practices

## Notes

- Agent system prompt includes agent's markdown content + loaded skills
- Skills are cached in system prompt (use cache_control)
- Agent tool filtering: only specified tools are available
- Model inheritance: "inherit" uses parent's model
- Stack depth limit: 5 levels of agent nesting (configurable)
- Task tool is always included in tool list (can't be removed)
- Agent spawning is synchronous (parent waits for agent to complete)
- Future: Consider async agent spawning for parallelism
