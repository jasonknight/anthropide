# Agent Definition Format Documentation

This document provides comprehensive documentation on how to define, configure, and use agents in AnthropIDE and the Claude Agent system. Agents are specialized AI instances that handle complex, focused tasks by leveraging unique system prompts and tool access.

---

## Overview

Agents are defined as **Markdown files with YAML frontmatter** stored in the `.claude/agents/` directory (for project-scoped agents) or `~/.claude/agents/` (for user-scoped agents).

Each agent definition consists of:
1. **YAML Frontmatter Block** - Configuration metadata
2. **Markdown Content** - System prompt and instructions

### File Storage Locations

- **Project-scoped agents**: `.claude/agents/<agent-name>.md`
- **User-scoped agents**: `~/.claude/agents/<agent-name>.md`

Example file structure:
```
AnthropIDE/
├── .claude/
│   └── agents/
│       ├── backend-python-tester.md
│       ├── backend-python-implementer.md
│       ├── backend-python-planner.md
│       ├── frontend-js-validator.md
│       └── plan-validator.md
└── ... (rest of project)
```

---

## YAML Frontmatter Format

The YAML frontmatter block is delimited by three hyphens (`---`) at the start and end. It contains configuration metadata for the agent.

### Complete YAML Structure

```yaml
---
name: agent-identifier
description: Clear description of when and why to use this agent...
model: inherit
tools: tool1, tool2, tool3
skills: skill1, skill2
color: red
permissionMode: default
---
```

### YAML Fields Reference

#### Required Fields

##### `name`
- **Type**: String
- **Format**: lowercase letters, numbers, and hyphens only
- **Max Length**: 64 characters
- **Purpose**: Unique identifier for the agent used internally and in commands
- **Example**: `backend-python-tester`

```yaml
name: backend-python-tester
```

##### `description`
- **Type**: String (supports Markdown and XML tags)
- **Max Length**: 1024 characters
- **Purpose**: Natural language description of what the agent does and when to use it
- **Special Feature**: Can include XML tags like `<example>`, `<code>`, `<commentary>`, and `<context>` for rich formatting
- **Usage**: The model learns about agents by reading this description in the Task tool definition

```yaml
description: Use this agent when you need to create, review, or improve unit tests for Python code...
```

**Note on Description Content**: The description field supports:
- Plain text explaining the agent's purpose
- XML tags for structured examples (see XML Tags section below)
- Multiple paragraphs (use `\n\n` for paragraph breaks in JSON representation)
- Specific use cases and calling patterns

#### Optional Fields

##### `model`
- **Type**: String
- **Default**: `inherit` (uses parent session's model)
- **Valid Values**:
  - `inherit` - Use the same model as the main Claude Code session
  - `sonnet` - Use Claude Sonnet 4.5
  - `opus` - Use Claude Opus
  - `haiku` - Use Claude Haiku 4.5
- **Purpose**: Specifies which model to use when spawning this agent
- **Example**:
```yaml
model: inherit
```

##### `tools`
- **Type**: String (comma-separated list)
- **Default**: All available tools (if omitted)
- **Purpose**: Restricts which tools the agent can access
- **Common Tools**: `Read`, `Write`, `Bash`, `Edit`, etc.
- **Example**:
```yaml
tools: Read, Write, Bash
```

If omitted, the agent inherits all tools available in the main session.

##### `skills`
- **Type**: String (comma-separated list)
- **Default**: None (no skills auto-loaded)
- **Purpose**: Automatically loads and injects specific Skills into the agent's context
- **Format**: Comma-separated list of skill names
- **Example**:
```yaml
skills: python-testing, code-review
```

##### `color`
- **Type**: String
- **Default**: None
- **Valid Values**: CSS color names or hex codes
- **Purpose**: Visual indicator for the agent in UI/CLI displays
- **Examples**:
```yaml
color: red
color: #FF6B6B
color: blue
```

##### `permissionMode`
- **Type**: String
- **Default**: `default`
- **Valid Values**:
  - `default` - Respects standard permission system
  - `acceptEdits` - Pre-approves edit operations (tool calls won't require confirmation)
  - `bypassPermissions` - Agent can execute any allowed tool without restrictions
  - `plan` - Special mode for planning agents (returns structured plans)
  - `ignore` - Agent runs with no permission checks
- **Purpose**: Controls how strictly permissions are enforced for this agent
- **Example**:
```yaml
permissionMode: default
```

---

## XML Tags in Descriptions

The description field supports structured XML tags to provide rich examples and context. These tags help the model understand usage patterns and help users understand when to invoke the agent.

### Supported XML Tags

#### `<example>`
Wraps a complete usage example showing when and how to use the agent.

```xml
<example>
Context: User has just implemented a new API endpoint in their Bottle web application.

user: "I just added a POST endpoint to create new projects. Here's the code:"
<code>
@app.route('/api/projects', method='POST')
def create_project():
    data = request.json
    project_name = data.get('name')
    project = Project(name=project_name, path=Path('.anthropide/projects') / project_name)
    project.create_directories()
    return {"success": True, "project": project_name}
</code>

A: "Great! Now let me use the backend-python-tester agent to create comprehensive tests for this new endpoint."

<commentary>
The user has implemented new backend functionality that needs testing. Use the Task tool to launch the backend-python-tester agent to create unit and integration tests for the endpoint.
</commentary>
</example>
```

#### `<context>`
Provides background information about the scenario being described.

```xml
<context>
User has just implemented a new API endpoint in their Bottle web application.
</context>
```

#### `<code>`
Displays code examples in a structured format (content shown as-is without interpretation).

```xml
<code>
def test_user_creation():
    response = app.post('/api/users', json={'name': 'John', 'email': 'john@example.com'})
    assert response.status_code == 201
    assert response.json['user_id']
</code>
```

#### `<commentary>`
Provides explanation or guidance about the example.

```xml
<commentary>
The user has implemented new backend functionality that needs testing. Use the Task tool to launch the backend-python-tester agent to create unit and integration tests for the endpoint.
</commentary>
```

### Example Usage in Description Field

```yaml
description: Use this agent when you need to create, review, or improve unit tests for Python code. This includes testing CLIs, APIs, and data models.

Examples:

<example>
<context>
User has just implemented a new API endpoint.
</context>

user: "I just added a POST endpoint. Can you create tests for it?"

A: "I'll use the backend-python-tester agent to create comprehensive tests for your new API endpoint."

<commentary>
The user has implemented new backend functionality that needs testing. Use the Task tool to launch the backend-python-tester agent.
</commentary>
</example>

<example>
<context>
User is working on database model tests.
</context>

user: "I've written database models. Can you verify they work correctly?"

A: "I'll use the backend-python-tester agent to create tests for your data models."

<commentary>
The user needs testing for core data model functionality.
</commentary>
</example>
```

---

## Markdown Content (After Frontmatter)

Everything after the closing `---` of the frontmatter block is treated as the **agent's system prompt**. This content forms the core of the agent's expertise and behavior.

### Structure and Best Practices

The system prompt should:

1. **Define Agent Identity** - Who is this agent? What's their expertise?
```markdown
You are an elite Python backend testing specialist with deep expertise in pytest, unittest, and testing frameworks for web applications...
```

2. **Explain Philosophy** - What principles guide this agent?
```markdown
## Core Testing Philosophy

1. **Strategic Coverage Over Exhaustive Testing**: Focus on critical code paths...
2. **Clarity and Maintainability**: Write tests that serve as documentation...
```

3. **Provide Detailed Guidelines** - Concrete technical guidance
```markdown
## Technical Guidelines

### Test Structure
- Use pytest as the default framework
- Organize tests with clear AAA pattern: Arrange, Act, Assert
- Use descriptive test names: `test_<component>_<scenario>_<expected_result>`
```

4. **Set Priorities** - What should the agent focus on?
```markdown
## Testing Priorities (In Order)

1. **Critical Business Logic**: Core functionality that defines the application's value
2. **Data Integrity**: Serialization, deserialization, validation, persistence
3. **API Contracts**: Request/response handling, status codes, error handling
```

5. **Include Workflow** - Step-by-step process the agent should follow
```markdown
## Your Workflow

1. **Analyze the Code**: Review the implementation to understand...
2. **Identify Test Priorities**: Determine which code paths are most critical...
3. **Design Test Strategy**: Plan your test suite...
```

6. **Add Quality Indicators** - How to measure success
```markdown
## Quality Indicators

Your tests should:
- Fail when the implementation is broken
- Pass when the implementation is correct
- Be easy to understand and modify
- Run quickly
```

### Complete Example: Backend Python Tester

```markdown
---
name: backend-python-tester
description: Use this agent when you need to create, review, or improve unit tests for Python code...
model: inherit
color: red
---

You are an elite Python backend testing specialist with deep expertise in pytest, unittest, and testing frameworks for web applications, CLIs, and system programs. Your mission is to create concise, effective test suites that maximize confidence in code correctness while maintaining efficiency and maintainability.

## Core Testing Philosophy

1. **Strategic Coverage Over Exhaustive Testing**: Focus on critical code paths, edge cases, and integration points rather than achieving 100% line coverage. Test what matters.

2. **Clarity and Maintainability**: Write tests that serve as documentation. Each test should clearly communicate what behavior it verifies and why it matters.

3. **Pragmatic Approach**: Balance thoroughness with practicality. Recognize that some code is more critical than others and allocate testing effort accordingly.

## Testing Priorities (In Order)

1. **Critical Business Logic**: Core functionality that defines the application's value
2. **Data Integrity**: Serialization, deserialization, validation, persistence
3. **API Contracts**: Request/response handling, status codes, error handling
4. **Integration Points**: Database interactions, file I/O, external services
5. **Edge Cases**: Boundary conditions, error states, invalid inputs
6. **Happy Paths**: Standard successful operations

## Technical Guidelines

### Test Structure
- Use pytest as the default framework (or unittest if the project already uses it)
- Organize tests with clear AAA pattern: Arrange, Act, Assert
- Use descriptive test names: `test_<component>_<scenario>_<expected_result>`
- Group related tests in classes when it improves organization
- Use fixtures for common setup/teardown to keep tests DRY

### For Web Applications (Bottle, Flask, FastAPI)
- Test API endpoints with both success and failure scenarios
- Verify HTTP status codes, response structure, and content
- Test authentication/authorization if present
- Mock external dependencies (databases, APIs) to isolate units
- Include integration tests for critical workflows

## Your Workflow

1. **Analyze the Code**: Review the implementation to understand critical functionality
2. **Identify Test Priorities**: Determine which code paths are most critical
3. **Design Test Strategy**: Plan your test suite with unit and integration tests
4. **Write Efficient Tests**: Create tests that are fast and independent
5. **Explain Your Choices**: Document why you focused on specific code paths

## Quality Indicators

Your tests should:
- Fail when the implementation is broken
- Pass when the implementation is correct
- Be easy to understand and modify
- Run quickly (unit tests in milliseconds)
- Catch regressions effectively
```

---

## How Agents Are Discovered and Invoked

### Agent Discovery Process

1. **Startup Scan**: The CLI scans `.claude/agents/` for all `.md` files
2. **Metadata Extraction**: Reads YAML frontmatter from each agent file
3. **Task Tool Description Building**: Concatenates all agent names and descriptions
4. **API Communication**: Sends complete Task tool definition to the Anthropic API

### Example: How the Task Tool is Built

```python
import os
import yaml

def build_task_tool_description():
    agents_dir = ".claude/agents"
    descriptions = ["Launch a new agent to handle specialized tasks.\n\nAvailable agents:\n"]

    for filename in os.listdir(agents_dir):
        if filename.endswith('.md'):
            with open(f"{agents_dir}/{filename}") as f:
                content = f.read()

                # Extract YAML frontmatter
                if content.startswith('---'):
                    _, frontmatter, system_prompt = content.split('---', 2)
                    agent_config = yaml.safe_load(frontmatter)

                    # Add agent description to tool
                    descriptions.append(
                        f"- **{agent_config['name']}**: {agent_config['description']}\n"
                    )

    return ''.join(descriptions)

# When making API call
tools = [
    {
        "name": "Task",
        "description": build_task_tool_description(),
        "input_schema": {
            "type": "object",
            "properties": {
                "subagent_type": {"type": "string", "description": "The type of agent (e.g., backend-python-tester)"},
                "prompt": {"type": "string", "description": "The task for the agent"}
            },
            "required": ["subagent_type", "prompt"]
        }
    }
]
```

### Model Decision Flow

```
Model sees Task tool description
    ↓
Reads all agent names and descriptions
    ↓
Evaluates current task
    ↓
Matches task to most appropriate agent
    ↓
Invokes Task tool with agent name and prompt
    ↓
CLI spawns agent in new conversation thread
```

---

## API Request/Response Examples

### Example 1: Agent Invocation by Main Thread

When the model decides to use an agent, it invokes the Task tool:

#### Request to Anthropic API (Main Thread)

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are Claude Code, an AI assistant...",
  "tools": [
    {
      "name": "Task",
      "description": "Launch a new agent to handle specialized tasks.\n\nAvailable agents:\n\n- backend-python-tester: Use this agent when you need to create, review, or improve unit tests for Python backend code...\n\n- backend-python-implementer: Use this agent when you need to implement backend Python code, CLI tools, API endpoints...",
      "input_schema": {
        "type": "object",
        "properties": {
          "subagent_type": {
            "type": "string",
            "description": "The type of agent to spawn (e.g., backend-python-tester)"
          },
          "prompt": {
            "type": "string",
            "description": "The specific task for the agent to handle"
          }
        },
        "required": ["subagent_type", "prompt"]
      }
    },
    {
      "name": "Read",
      "description": "Reads a file from the filesystem...",
      "input_schema": { "..." }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "I just implemented a new API endpoint. Can you create tests for it?"
    }
  ]
}
```

#### Response from Anthropic API

```json
{
  "id": "msg_123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll use the backend-python-tester agent to create comprehensive tests for your new API endpoint."
    },
    {
      "type": "tool_use",
      "id": "toolu_456",
      "name": "Task",
      "input": {
        "subagent_type": "backend-python-tester",
        "prompt": "Create comprehensive tests for the new /api/users endpoint. The endpoint accepts POST requests and creates new user records in the database."
      }
    }
  ],
  "stop_reason": "tool_use"
}
```

### Example 2: Agent Spawning (New Thread)

When the CLI detects a Task tool invocation, it creates a new API call with the agent's system prompt:

#### Request to Anthropic API (Agent Thread - NEW)

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are an elite Python backend testing specialist with deep expertise in pytest, unittest, and testing frameworks for web applications, CLIs, and system programs. Your mission is to create concise, effective test suites that maximize confidence in code correctness while maintaining efficiency and maintainability.\n\n## Core Testing Philosophy\n\n1. **Strategic Coverage Over Exhaustive Testing**: Focus on critical code paths, edge cases, and integration points rather than achieving 100% line coverage. Test what matters.\n\n[...full system prompt from .claude/agents/backend-python-tester.md...]",
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file from the filesystem...",
      "input_schema": { "..." }
    },
    {
      "name": "Write",
      "description": "Writes content to a file...",
      "input_schema": { "..." }
    },
    {
      "name": "Bash",
      "description": "Executes bash commands...",
      "input_schema": { "..." }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "Create comprehensive tests for the new /api/users endpoint. The endpoint accepts POST requests and creates new user records in the database."
    }
  ]
}
```

**Note**: The Task tool is NOT included in the agent's tools - agents cannot spawn sub-agents.

#### Response from Agent

```json
{
  "id": "msg_789",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll read the endpoint implementation first to understand the code structure."
    },
    {
      "type": "tool_use",
      "id": "toolu_abc",
      "name": "Read",
      "input": {
        "file_path": "/home/user/project/api/users.py"
      }
    }
  ],
  "stop_reason": "tool_use"
}
```

**Agent continues working through multiple request/response cycles...**

#### Final Agent Response

```json
{
  "id": "msg_xyz",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I've created comprehensive tests for the /api/users endpoint in tests/test_users.py. The test suite covers:\n\n1. **Successful user creation** - Tests that valid POST requests create users\n2. **Validation errors** - Tests that invalid data is rejected with proper error messages\n3. **Duplicate email handling** - Tests that duplicate emails are rejected\n4. **Database integration** - Tests that users are correctly persisted\n5. **Response format** - Tests that responses match the API contract\n\nAll 15 tests are passing. Coverage for the /api/users endpoint is 98%."
    }
  ],
  "stop_reason": "end_turn"
}
```

### Example 3: Returning Result to Main Thread

After the agent completes, the CLI returns the result to the main conversation:

#### Request to Anthropic API (Back to Main Thread)

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "system": "You are Claude Code...",
  "tools": [ "..." ],
  "messages": [
    {
      "role": "user",
      "content": "I just implemented a new API endpoint. Can you create tests for it?"
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "I'll use the backend-python-tester agent to create comprehensive tests for your new API endpoint."
        },
        {
          "type": "tool_use",
          "id": "toolu_456",
          "name": "Task",
          "input": {
            "subagent_type": "backend-python-tester",
            "prompt": "Create comprehensive tests for the new /api/users endpoint..."
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_456",
          "content": "I've created comprehensive tests for the /api/users endpoint in tests/test_users.py. The test suite covers:\n\n1. **Successful user creation**\n2. **Validation errors**\n3. **Duplicate email handling**\n4. **Database integration**\n5. **Response format**\n\nAll 15 tests are passing. Coverage for the /api/users endpoint is 98%."
        }
      ]
    }
  ]
}
```

#### Final Response to User

```json
{
  "id": "msg_final",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Perfect! The backend-python-tester agent has successfully created comprehensive tests for your new /api/users endpoint. You now have 15 tests covering all critical functionality with 98% code coverage."
    }
  ],
  "stop_reason": "end_turn"
}
```

---

## Complete Agent Definition Example

Here's a complete working agent definition:

### File: `.claude/agents/backend-python-implementer.md`

```markdown
---
name: backend-python-implementer
description: Use this agent when you need to implement backend Python code, CLI tools, API endpoints, data models, or server-side logic. This agent excels at translating software design specifications and implementation plans into production-ready Python code with proper structure, error handling, and adherence to best practices.\n\nExamples:\n\n<example>\n<context>User has a design document for a new API endpoint</context>\nuser: "I need to add a new endpoint to export session data as markdown. Here's the spec..."\nassistant: "I'll use the backend-python-implementer agent to implement this API endpoint according to the specification."\n<commentary>The user has a clear specification. Use the Task tool to launch the backend-python-implementer agent to implement the endpoint with proper error handling and testing.</commentary>\n</example>\n\n<example>\n<context>User needs a CLI command implemented</context>\nuser: "Can you implement the session import command we planned earlier?"\nassistant: "Let me use the backend-python-implementer agent to implement this CLI command with proper argument parsing and error handling."\n<commentary>Implementation work based on a plan. Use the Task tool to launch the backend-python-implementer agent.</commentary>\n</example>
model: inherit
tools: Read, Write, Bash, Edit
color: blue
---

You are an elite Python backend implementation specialist with expertise in designing and building production-quality backend systems. Your mission is to translate specifications, plans, and requirements into clean, maintainable, and robust Python code.

## Your Expertise

You excel at:
- Building RESTful APIs (Flask, FastAPI, Bottle, Django)
- Creating CLI tools with proper argument parsing
- Designing database schemas and ORM models
- Implementing business logic and data processing pipelines
- Writing code that handles errors gracefully
- Following SOLID principles and design patterns
- Writing code that is testable and maintainable

## Implementation Philosophy

1. **Specification-First**: Always start by thoroughly understanding the specification or design document
2. **Quality Over Speed**: Write code you'd be proud to maintain in production
3. **Error Handling**: Every failure path should be explicitly handled
4. **Testing Readiness**: Structure code to be easily testable
5. **Documentation**: Include docstrings and comments for non-obvious logic

## Your Workflow

1. **Analyze Requirements**: Read and understand the specification completely
2. **Design Architecture**: Plan the code structure before writing
3. **Implement Iteratively**: Build and test incrementally
4. **Handle Edge Cases**: Anticipate failure modes
5. **Provide Summary**: Explain what was implemented and any decisions made

## Code Standards

- Use type hints for function signatures
- Follow PEP 8 style guidelines
- Use trailing commas in multi-line constructs
- Organize imports: standard library, third-party, local
- Include comprehensive error handling
- Write docstrings for public functions and classes

## When to Ask Questions

- If requirements are ambiguous or incomplete
- If you need to choose between multiple valid approaches
- If you discover issues in the specification
- If you need clarification on existing code you're integrating with

## Quality Indicators

Your implementation should:
- Be immediately testable
- Follow the project's coding standards
- Handle errors gracefully
- Be easy to understand and modify
- Integrate cleanly with existing code
- Include appropriate logging/debugging support
```

---

## Agent Configuration Best Practices

### 1. Clear, Actionable Descriptions

Write descriptions that help the model decide when to use your agent:

**Good:**
```yaml
description: Use this agent when you need to create, review, or improve unit tests for Python code. This includes testing CLIs, APIs, and data models. Call this agent after implementing new features or when test coverage needs improvement.
```

**Avoid:**
```yaml
description: Testing agent
```

### 2. Include Multiple Examples

Provide concrete examples in XML tags to show various use cases:

```yaml
description: Use this agent when...

Examples:

<example>
<context>Scenario 1</context>
user: "..."
assistant: "..."
<commentary>...</commentary>
</example>

<example>
<context>Scenario 2</context>
user: "..."
assistant: "..."
<commentary>...</commentary>
</example>
```

### 3. Detailed System Prompts

The markdown content (system prompt) should be comprehensive:
- Define expertise and philosophy
- Explain priorities and strategies
- Provide concrete guidelines
- Include workflow steps
- Set quality expectations

### 4. Limit Tool Access When Appropriate

Only grant tools the agent actually needs:

```yaml
tools: Read, Write, Bash, Edit
```

Don't grant the Task tool to agents (they can't spawn sub-agents).

### 5. Use Colors for Visual Distinction

Assign colors to help users identify agents in UI displays:

```yaml
color: red
color: blue
color: green
```

---

## Integration with Your Application

### Loading Agents at Startup

```python
import os
import yaml
from pathlib import Path

def load_agents(agents_dir=".claude/agents"):
    agents = {}

    if not os.path.exists(agents_dir):
        return agents

    for filename in os.listdir(agents_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(agents_dir, filename)

            with open(filepath, 'r') as f:
                content = f.read()

            # Split on frontmatter delimiters
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    system_prompt = parts[2].strip()

                    # Parse YAML
                    config = yaml.safe_load(frontmatter)

                    # Store agent
                    agents[config['name']] = {
                        'config': config,
                        'system_prompt': system_prompt,
                        'filepath': filepath
                    }

    return agents

# Usage
agents = load_agents()
for agent_name, agent_data in agents.items():
    print(f"Loaded agent: {agent_name}")
    print(f"  Description: {agent_data['config'].get('description', 'N/A')[:50]}...")
```

### Building the Task Tool Description

```python
def build_task_tool_description(agents):
    descriptions = [
        "Launch a new agent to handle specialized tasks.\n\n"
        "The model should choose an agent based on the task requirements and "
        "the detailed descriptions provided below.\n\n"
        "Available agents:\n"
    ]

    for agent_name, agent_data in agents.items():
        config = agent_data['config']
        description = config.get('description', 'No description')
        descriptions.append(f"\n**{agent_name}**: {description}")

    return ''.join(descriptions)

# Usage
task_tool_description = build_task_tool_description(agents)
# Use this in the Task tool definition when making API calls
```

### Spawning an Agent

```python
def spawn_agent(agent_name, prompt, agents, client):
    """Spawn an agent to handle a specific task."""

    if agent_name not in agents:
        raise ValueError(f"Unknown agent: {agent_name}")

    agent_data = agents[agent_name]
    config = agent_data['config']
    system_prompt = agent_data['system_prompt']

    # Determine model
    model = config.get('model', 'inherit')
    if model == 'inherit':
        model = 'claude-sonnet-4-5-20250929'  # Default model

    # Build tool list (exclude Task tool for agents)
    available_tools = get_available_tools()  # Your function
    if 'Task' in available_tools:
        del available_tools['Task']

    # Restrict tools if specified
    if 'tools' in config:
        allowed_tool_names = [t.strip() for t in config['tools'].split(',')]
        available_tools = {
            k: v for k, v in available_tools.items()
            if k in allowed_tool_names
        }

    # Make API call with agent's system prompt
    response = client.messages.create(
        model=model,
        max_tokens=8000,
        system=system_prompt,
        tools=list(available_tools.values()),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response
```

---

## Summary

Agent definitions provide a powerful way to create specialized AI instances for focused tasks:

1. **YAML Frontmatter**: Configure metadata (name, description, model, tools, skills, color, permissions)
2. **Markdown Content**: Define expertise through detailed system prompts
3. **XML Tags**: Structure examples and guidance for clarity
4. **Discovery**: Models learn about agents via the Task tool description
5. **Spawning**: Each agent runs in an independent conversation thread
6. **Isolation**: Agents cannot spawn sub-agents (no Task tool)

By following these patterns, you can build a flexible agent system that scales to handle increasingly complex development tasks while maintaining clean separation of concerns and expert-level specialization.
