# How Agent Spawning Works in Claude Code

This document explains the technical implementation of how Claude Code spawns agents when using the Claude API.

## Key Concept

**The model decides to spawn agents, not the CLI.** The CLI provides a "Task" tool that the model can invoke like any other tool. There is no special API syntax - agents use the standard Anthropic Messages API.

---

## Agent Architecture Overview

The "agent pattern" is implemented through:
- **Specialized system prompts** (defined in `.claude/agents/*.md` files)
- **Independent conversation threads** (each agent is a separate API call)
- **Tool definitions** (the model learns about agents through the Task tool description)

```
Main Claude Code Session
    ↓ (model decides agent is needed)
Task Tool Invocation
    ↓
New API Call with Agent's System Prompt
    ↓
Independent Conversation Thread
    ↓
Agent Returns Final Report
    ↓
Result Returned to Main Thread
```

---

## Step-by-Step Example: Creating Tests

### Step 1: User Request to Main Claude Instance

The user makes a request, and the CLI sends it to the API with all available tools, including the Task tool.

**Request from CLI → Anthropic API:**
```json
POST https://api.anthropic.com/v1/messages
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are Claude Code, an AI assistant that helps with coding...",
  "tools": [
    {
      "name": "Task",
      "description": "Launch a new agent to handle complex tasks...\n\nAvailable agent types:\n\n- backend-python-tester: Use this agent when you need to create, review, or improve unit tests and integration tests for Python backend code. Call this agent after implementing new features...\n\n- backend-python-implementer: Use this agent when you need to implement backend Python code, CLI tools, API endpoints...\n\n[... descriptions for ALL available agents ...]",
      "input_schema": {
        "type": "object",
        "properties": {
          "subagent_type": {
            "type": "string",
            "description": "The type of agent (e.g., backend-python-tester)"
          },
          "prompt": {
            "type": "string",
            "description": "The task for the agent"
          }
        },
        "required": ["subagent_type", "prompt"]
      }
    },
    {
      "name": "Read",
      "description": "Reads a file...",
      "input_schema": { "..." }
    }
    // ... other tools
  ],
  "messages": [
    {
      "role": "user",
      "content": "I just wrote a new API endpoint. Can you create tests for it?"
    }
  ]
}
```

### Step 2: Claude Decides to Use Agent

The model reads the Task tool description, recognizes that "backend-python-tester" is appropriate, and invokes it.

**Response from Anthropic API → CLI:**
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
        "description": "Create API endpoint tests",
        "prompt": "Create comprehensive tests for the new /api/users endpoint that was just implemented. The endpoint accepts POST requests and creates new users..."
      }
    }
  ],
  "stop_reason": "tool_use"
}
```

### Step 3: CLI Spawns Agent in New Thread

The CLI sees the `tool_use` request and spawns a **completely separate API call** with the agent's specialized system prompt.

**Request from CLI → Anthropic API (NEW THREAD):**
```json
POST https://api.anthropic.com/v1/messages
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are an elite Python backend testing specialist...\n[Full system prompt from .claude/agents/backend-python-tester.md]",
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file...",
      "input_schema": { "..." }
    },
    {
      "name": "Write",
      "description": "Writes a file...",
      "input_schema": { "..." }
    }
    // Same tools, but NO "Task" tool (agent can't spawn sub-agents)
  ],
  "messages": [
    {
      "role": "user",
      "content": "Create comprehensive tests for the new /api/users endpoint that was just implemented. The endpoint accepts POST requests and creates new users..."
    }
  ]
}
```

### Step 4: Agent Works and Returns Result

The agent uses tools to complete its task across multiple API request/response cycles.

**Response from Anthropic API → CLI (from agent thread):**
```json
{
  "id": "msg_789",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll read the endpoint implementation first."
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

*(Multiple request/response cycles as agent reads files, writes tests, etc.)*

**Final response from agent:**
```json
{
  "id": "msg_xyz",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I've created comprehensive tests for the /api/users endpoint in test_users.py. The test suite covers:\n\n1. Successful user creation\n2. Validation errors\n3. Duplicate email handling\n4. Database integration\n\nAll tests are passing."
    }
  ],
  "stop_reason": "end_turn"
}
```

### Step 5: CLI Returns Result to Main Thread

The CLI takes the agent's final response and returns it as a tool_result to the main conversation thread.

**Request from CLI → Anthropic API (BACK TO MAIN THREAD):**
```json
POST https://api.anthropic.com/v1/messages
{
  "model": "claude-sonnet-4-5-20250929",
  "system": "You are Claude Code...",
  "tools": [ "..." ],
  "messages": [
    {
      "role": "user",
      "content": "I just wrote a new API endpoint. Can you create tests for it?"
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "I'll use the backend-python-tester agent..."
        },
        {
          "type": "tool_use",
          "id": "toolu_456",
          "name": "Task",
          "input": { "..." }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_456",
          "content": "I've created comprehensive tests for the /api/users endpoint in test_users.py..."
        }
      ]
    }
  ]
}
```

**Final Response to User:**
```json
{
  "id": "msg_final",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "The tests have been created! The backend-python-tester agent has written comprehensive tests covering all the important scenarios for your new endpoint."
    }
  ],
  "stop_reason": "end_turn"
}
```

---

## How Agents Are Discovered

The CLI tells the model about available agents by dynamically building the Task tool's description at startup.

### Agent Definition Format

Agents are defined in `.claude/agents/*.md` files with YAML frontmatter:

```markdown
---
name: backend-python-tester
description: Use this agent when you need to create tests...
model: inherit
color: red
---

You are an elite Python backend testing specialist...
[Detailed system prompt instructions]
```

### Dynamic Tool Description Building

The CLI:
1. **Scans** `.claude/agents/` directory for all `.md` files
2. **Reads** each agent file and extracts name and description
3. **Concatenates** all descriptions into the Task tool's description field
4. **Sends** the complete tool definition to the API

### Example Implementation

```python
import os
import yaml

def build_task_tool_description():
    agents_dir = ".claude/agents"
    descriptions = ["Launch a new agent...\n\nAvailable agents:\n"]

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
                        f"- {agent_config['name']}: {agent_config['description']}\n"
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
                "subagent_type": {"type": "string"},
                "prompt": {"type": "string"}
            }
        }
    }
]
```

---

## Key Insights

### No Special API Syntax
Agents use the standard Anthropic Messages API. The only difference is:
- **System prompt** is agent-specific
- **Conversation thread** is independent
- **Tool access** is the same as the main session

### Model Has Full Control
The model decides when to spawn agents based on:
- Task complexity
- Agent descriptions in the Task tool
- Context of the user's request

### Agent Discovery via Tool Description
The model learns about available agents by reading the Task tool's description field, which contains all agent names and their usage guidelines.

### Independent Execution
Each agent runs in its own API conversation thread:
- Separate message history
- Same tool access (Read, Write, Bash, etc.)
- Cannot spawn sub-agents (no Task tool)
- Returns final result to main thread

---

## Implementation Checklist

To build your own agent system:

1. ✅ **Define agents** in configuration files (markdown with YAML frontmatter)
2. ✅ **Create specialized system prompts** for each agent type
3. ✅ **Build Task tool description** dynamically from agent configs
4. ✅ **Detect Task tool invocations** in API responses
5. ✅ **Spawn new API calls** with agent system prompts
6. ✅ **Execute agent conversation** until completion
7. ✅ **Return results** as tool_result to main thread
8. ✅ **Continue main conversation** with agent's output

---

## Summary

The agent pattern is an elegant architecture that combines:
- **Specialized expertise** (via detailed system prompts)
- **Tool-based invocation** (model chooses when to use agents)
- **Thread isolation** (independent conversations per agent)
- **Dynamic discovery** (agents described in tool definitions)

No special API features required - just good system prompts and conversation management!
