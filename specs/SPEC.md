# AnthropIDE - Technical Specification

## 1. Overview & Goals

### 1.1 Purpose
AnthropIDE is a web-based context/prompt engineering platform that enables users to design, test, and package sophisticated AI prompts (and therefore their "contexts") as distributable products. The application provides fine-grained control over Anthropic API requests, allowing prompt engineers to create general-purpose or domain-specific AI workflows complete with custom tools, skills, and agents.

### 1.2 Core Value Proposition
- **Prompts as Products**: Package prompts with tools and skills for distribution
- **Maximum Control**: Edit every aspect of Anthropic API requests
- **Test Before Deploy**: Simulate model responses for workflow validation
- **Portable**: Export projects as standalone CLI applications

### 1.3 Target Users
- Prompt engineers building reusable AI workflows
- Companies creating internal AI tooling
- Developers packaging AI agents for customers
- Teams testing and validating complex prompts

### 1.4 Key Technologies
- **Backend**: Python 3.x with Bottle framework
- **Frontend**: jQuery with jQuery UI components
- **Text Editor**: CodeMirror with markdown mode
- **Data Storage**: File-based JSON storage
- **API**: Anthropic SDK for Python

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Web Browser                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │   jQuery UI   │  │  CodeMirror  │  │  Markdown │ │
│  │   Widgets     │  │   Editor     │  │  Preview  │ │
│  └──────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
                         │ AJAX/JSON
                         ▼
┌─────────────────────────────────────────────────────┐
│              Bottle Web Application                  │
│  ┌──────────────────────────────────────────────┐  │
│  │              REST API Endpoints               │  │
│  │  /api/projects  /api/session  /api/execute   │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │           Business Logic Layer               │  │
│  │  Project Manager | Session Manager | Validator│  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │              Data Access Layer               │  │
│  │  File I/O | JSON Serialization | Validation  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│           File System (app/projects/)                │
│  ┌─────────────────────────────────────────────┐   │
│  │  project_name/                              │   │
│  │    ├── current_session.json                 │   │
│  │    ├── current_session.json.202511301430    │   │
│  │    ├── project.json                         │   │
│  │    ├── requirements.txt                     │   │
│  │    ├── agents/*.md                          │   │
│  │    ├── skills/*.md                          │   │
│  │    ├── tools/*.{json,py}                    │   │
│  │    ├── snippets/**/*.md                     │   │
│  │    └── tests/config.json                    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│            Anthropic API (when executing)            │
└─────────────────────────────────────────────────────┘
```

### 2.2 Standalone CLI Runner Architecture

```
┌─────────────────────────────────────────────────────┐
│              CLI Application (Python)                │
│  ┌──────────────────────────────────────────────┐  │
│  │         Command Line Interface (argparse)     │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │           Project Loader & Validator         │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │        Tool Plugin System (auto-load)        │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │      Execution Engine (streaming to stdout)  │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │      History Manager (conversation logs)     │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│    Packaged Project (extracted from .zip)            │
└─────────────────────────────────────────────────────┘
```

### 2.3 Application Structure

```
anthropide/
├── app.py                          # Main Bottle application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
│
├── lib/                            # Core library modules
│   ├── __init__.py
│   ├── project_manager.py          # Project CRUD operations
│   ├── session_manager.py          # Session persistence
│   ├── agent_manager.py            # Agent CRUD operations
│   ├── skill_manager.py            # Skill CRUD operations
│   ├── tool_manager.py             # Tool loading and execution
│   ├── snippet_manager.py          # Snippet CRUD operations
│   ├── test_simulator.py           # Test simulation engine
│   ├── validator.py                # JSON schema validation
│   ├── packager.py                 # Project packaging to zip
│   └── data_models.py              # Pydantic data models
│
├── cli/                            # Standalone CLI runner
│   ├── __init__.py
│   ├── main.py                     # CLI entry point
│   ├── runner.py                   # Execution engine
│   ├── plugin_loader.py            # Tool plugin system
│   └── history.py                  # Conversation history
│
├── static/                         # Frontend assets
│   ├── css/
│   │   ├── main.css
│   │   ├── widgets.css
│   │   └── themes/
│   ├── js/
│   │   ├── app.js                  # Main application logic
│   │   ├── project.js              # Project management
│   │   ├── session.js              # Session editor
│   │   ├── agents.js               # Agent editor
│   │   ├── skills.js               # Skill editor
│   │   ├── tools.js                # Tool editor
│   │   ├── snippets.js             # Snippet browser
│   │   ├── modal.js                # Modal dialog system
│   │   └── utils.js                # Utility functions
│   └── lib/                        # Third-party libraries
│       ├── jquery/
│       ├── jquery-ui/
│       ├── codemirror/
│       └── marked/                 # Markdown rendering
│
├── templates/                      # Jinja2 templates
│   ├── base.html                   # Base template
│   ├── index.html                  # Main application view
│   └── partials/
│       ├── project_selector.html
│       ├── session_editor.html
│       ├── snippet_browser.html
│       └── modals.html
│
├── projects/                   # User projects
│   └── example_project/
│       ├── agents/             # Agent definitions (*.md)
│       ├── skills/             # Skill definitions (*.md, flat structure)
│       ├── tools/              # Tool definitions (*.json, *.py)
│       ├── snippets/           # Reusable snippets (**/*.md, nested categories)
│       ├── tests/              # Test configuration
│       │   └── config.json
│       ├── current_session.json        # Current API request state
│       ├── current_session.json.*      # Timestamped backups
│       ├── project.json                # Project metadata
│       └── requirements.txt            # Python dependencies for tools
│
└── state.json                  # Global UI state (at app root level)
```

---

## 3. Data Models

### 3.1 Project Metadata (project.json)

This file is stored at `projects/<project_name>/project.json` and contains project metadata:

```json
{
  "name": "example_project",
  "description": "Optional project description",
  "created": "2025-11-30T14:30:00Z",
  "modified": "2025-11-30T15:45:00Z",
  "settings": {
    "max_session_backups": 20,
    "auto_save": true,
    "default_model": "claude-sonnet-4-5-20250929"
  },
  "package_config": {
    "api_key_strategy": "cli_argument",
    "dependencies_checked": false
  }
}
```

**Package Config Fields**:
- `api_key_strategy`: How the packaged CLI should handle API keys
  - `"cli_argument"`: Require `--api-key` flag or ANTHROPIC_API_KEY env var (default, most secure)
  - `"env_file"`: Look for `.env` file in project directory
  - `"embedded"`: API key embedded in package (creates `.api_key` file, user should be warned)
  - `"prompt"`: Prompt user on first run and optionally save
- `dependencies_checked`: Whether dependency check should be enforced on CLI startup (default: true)

### 3.2 Session (current_session.json)

The session file is a complete Anthropic API request structure:

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8192,
  "temperature": 1.0,
  "system": [
    {
      "type": "text",
      "text": "You are an AI assistant...",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file from the filesystem...",
      "input_schema": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "Absolute path to file"
          }
        },
        "required": ["file_path"]
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Fix the typo in src/app.py"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "I'll fix that typo for you."
        },
        {
          "type": "tool_use",
          "id": "toolu_123",
          "name": "Edit",
          "input": {
            "file_path": "src/app.py",
            "old_string": "conection",
            "new_string": "connection"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_123",
          "content": "File edited successfully"
        }
      ]
    }
  ]
}
```

### 3.3 Agent Definition (agents/*.md)

**Execution Model**: Agents work like Claude Code's Task tool. During execution, the model can spawn agents using a special `Task` tool. When an agent is spawned:
1. A new Anthropic API request is created with the agent's configuration
2. The agent's system prompt replaces/augments the parent system prompt
3. The agent has access only to its specified tools and skills
4. The agent's model setting can override the parent model
5. The agent executes autonomously and returns results to the parent conversation

Agents are **not** selected upfront - they're spawned dynamically by the model during execution.

```yaml
---
name: code-reviewer
description: |
  Use this agent to review code for bugs, security issues, and best practices.
  Invoke after completing a significant piece of code.
model: inherit
tools: Read, Grep, Glob
skills: code-analysis, security-scan
color: blue
---

You are an expert code reviewer. Your task is to analyze code for:

1. **Bugs**: Logic errors, edge cases, potential crashes
2. **Security**: SQL injection, XSS, authentication issues
3. **Best Practices**: Code style, patterns, maintainability

Review the code thoroughly and provide actionable feedback.
```

**Field Descriptions:**
- `name`: Unique identifier for the agent (alphanumeric with hyphens)
- `description`: When and why to use this agent (shown to parent model in Task tool description)
- `model`: Model to use (`inherit` uses parent's model, or specify like `claude-sonnet-4-5-20250929`)
- `tools`: Comma-separated list of tool names available to this agent (subset of project tools)
- `skills`: Comma-separated list of skill names available to this agent (loaded into agent's system prompt)
- `color`: UI color for visual identification in logs/UI (red, blue, green, yellow, purple, etc.)

**Note**: `permissionMode` removed - all agents have full tool execution permissions (no sandboxing)

### 3.4 Skill Definition (skills/*.md)

**Execution Model**: Skills are markdown files containing role/context descriptions that get added to the system prompt (with caching) when an agent uses them. They explain how to accomplish tasks using available tools.

Skills are **instructional, not executable** - they teach the model how to use tools to accomplish complex workflows.

**File Structure**: `skills/web-search.md` (flat structure, not subdirectories)

```yaml
---
name: web-search
description: Search the web for current information using available tools
version: 1.0.0
author: Your Name
---

# Web Search Skill

This skill explains how to search the web for current information.

## Available Tools

You have access to:
- `WebFetch`: Fetch and parse web pages
- `Read`: Read local files
- `Write`: Save results to files

## Workflow

To search the web for information:

1. **Identify search query** - Extract key terms from user request
2. **Use WebFetch** - Fetch search engine results page (e.g., `https://duckduckgo.com/?q=search+terms`)
3. **Parse results** - Extract relevant URLs from the HTML
4. **Fetch top results** - Use WebFetch on the top 3-5 result URLs
5. **Synthesize** - Combine information and cite sources
6. **Save if needed** - Use Write to save detailed results

## Example

User asks: "What are the latest developments in quantum computing?"

1. WebFetch(`https://duckduckgo.com/?q=latest+quantum+computing+developments`)
2. Parse result URLs
3. WebFetch each top result
4. Summarize findings with citations
```

**Field Descriptions:**
- `name`: Unique identifier (used when agents reference skills)
- `description`: Brief explanation of what the skill teaches
- `version`: Semantic version for tracking changes
- `author`: Optional attribution

**Note**: Skills do not contain executable code (Python/shell scripts). They are purely instructional context that gets cached in the system prompt.

### 3.5 Built-in Task Tool (Agent Spawning)

**Purpose**: The `Task` tool is automatically included in every session and enables the model to spawn agents dynamically.

**How It Works**:
1. The model calls `Task` tool with `agent_name` and `prompt` parameters
2. The system loads the agent definition from `agents/<agent_name>.md`
3. A new Anthropic API request is created with:
   - Agent's system prompt (with referenced skills loaded and cached)
   - Agent's specified tools only
   - Agent's model override (if not "inherit")
   - The provided prompt as first user message
4. Agent executes autonomously (potentially spawning sub-agents)
5. Agent's final response is returned as the `Task` tool result
6. Parent conversation continues with the tool result

**Tool Schema** (automatically generated from available agents):

```json
{
  "name": "Task",
  "description": "Spawn a specialized agent to handle complex sub-tasks autonomously. Each agent has specific tools, skills, and expertise.",
  "input_schema": {
    "type": "object",
    "properties": {
      "agent_name": {
        "type": "string",
        "enum": ["code-reviewer", "test-writer", "documentation-generator"],
        "description": "The agent to spawn. Available agents:\n- code-reviewer: Use this agent to review code for bugs, security issues...\n- test-writer: Use this agent to write comprehensive tests...\n- documentation-generator: Use this agent to create documentation..."
      },
      "prompt": {
        "type": "string",
        "description": "The task prompt to send to the agent. Be specific and provide context."
      }
    },
    "required": ["agent_name", "prompt"]
  }
}
```

**Note**: The enum values and descriptions are dynamically populated from the project's `agents/` directory. The description concatenates all agent descriptions to help the model choose appropriately.

**Example Usage in Conversation**:

```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll spawn the code-reviewer agent to analyze the authentication system."
    },
    {
      "type": "tool_use",
      "id": "toolu_123",
      "name": "Task",
      "input": {
        "agent_name": "code-reviewer",
        "prompt": "Review the authentication system in src/auth.py for security vulnerabilities, focusing on session handling and password storage."
      }
    }
  ]
}
```

### 3.6 Tool Definition

**JSON-based tool (tools/edit.json):**

```json
{
  "name": "Edit",
  "description": "Performs exact string replacements in files",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Absolute path to the file"
      },
      "old_string": {
        "type": "string",
        "description": "Text to find and replace"
      },
      "new_string": {
        "type": "string",
        "description": "Replacement text"
      }
    },
    "required": ["file_path", "old_string", "new_string"]
  }
}
```

**Python custom tool (tools/custom_search.py):**

```python
"""
Custom tool implementation following Anthropic SDK conventions.
"""

def describe():
    """Return tool definition matching Anthropic SDK format."""
    return {
        "name": "WebSearch",
        "description": "Search the web for current information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }

def run(query, max_results=5):
    """
    Execute the tool with parameters from model's tool call.

    Args:
        query: Search query string
        max_results: Maximum results to return

    Returns:
        String result to send back to the model.

    Raises:
        Exception: Errors are formatted per Anthropic SDK conventions
    """
    # Implementation here
    # Working directory:
    #   - Web app: Tool runs in the project's root directory (projects/<project_name>/)
    #   - CLI: Tool runs in the directory where the CLI was invoked
    # No sandboxing - full system access
    results = perform_search(query, max_results)
    return format_results(results)
```

### 3.7 Snippet (snippets/**/*.md)

Snippets are plain markdown files with optional frontmatter:

```markdown
---
name: "Git Status Context"
category: "development"
tags: ["git", "context"]
---

Current git repository status:

\`\`\`
git status output here
\`\`\`

Recent commits:
\`\`\`
git log output here
\`\`\`
```

### 3.8 Test Configuration (tests/config.json)

```json
{
  "tests": [
    {
      "name": "Handle file read request",
      "sequence": [
        {
          "match": {
            "type": "regex",
            "path": "messages.-1.content.0.text",
            "pattern": "read.*app\\.py"
          },
          "response": {
            "role": "assistant",
            "content": [
              {
                "type": "tool_use",
                "id": "toolu_001",
                "name": "Read",
                "input": {
                  "file_path": "/path/to/app.py"
                }
              }
            ]
          },
          "tool_behavior": "mock",
          "tool_results": {
            "Read": {
              "file_path": "/path/to/app.py",
              "result": "# app.py\nprint('Hello World')"
            }
          }
        },
        {
          "match": {
            "type": "contains",
            "path": "messages.-1.content.0.type",
            "value": "tool_result"
          },
          "response": {
            "role": "assistant",
            "content": [
              {
                "type": "text",
                "text": "I've read the file. It's a simple Hello World script."
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Field Descriptions:**
- `tests`: Array of test scenarios
- `sequence`: Ordered array of request-response pairs
- `match.type`: `regex` or `contains`
- `match.path`: Dot-notation JSON path (e.g., `messages.-1.content.0.text` for last message's first content item)
- `match.pattern`: Regex pattern (when type is `regex`)
- `match.value`: Exact value or substring (when type is `contains`)
- `response`: Canned model response to return
- `tool_behavior`: `mock` (return canned results), `execute` (run real tools), or `skip` (no tools)
- `tool_results`: Mock results for specific tools

### 3.9 Global UI State (state.json)

**Location**: `state.json` (at application root, NOT per-project)

This file stores global UI state including the currently selected project and UI preferences:

```json
{
  "version": "1.0",
  "selected_project": "example_project",
  "ui": {
    "active_tabs": {
      "main": "session",
      "sidebar": "snippets"
    },
    "scroll_positions": {
      "session_editor": 450,
      "snippet_browser": 120
    },
    "expanded_widgets": {
      "system_prompt": true,
      "tools_section": false,
      "messages": true,
      "message_0": true,
      "message_1": false
    },
    "panel_sizes": {
      "sidebar_width": 320,
      "editor_height": 600
    },
    "snippet_categories_expanded": {
      "development": true,
      "documentation": false
    }
  },
  "last_modified": "2025-11-30T15:45:00Z"
}
```

**Note**: This is a **global** state file that persists across all projects. It remembers which project was last open and UI preferences. Per-project state (like which files are in the project) is stored in `project.json` within each project directory.

---

## 4. API Endpoints

### 4.1 Project Management

#### GET /api/projects
List all available projects.

**Response:**
```json
{
  "projects": [
    {
      "name": "example_project",
      "description": "Example project description",
      "created": "2025-11-30T14:30:00Z",
      "modified": "2025-11-30T15:45:00Z"
    }
  ]
}
```

#### POST /api/projects
Create a new project.

**Request:**
```json
{
  "name": "my_new_project",
  "description": "Optional description"
}
```

**Response:**
```json
{
  "success": true,
  "project": {
    "name": "my_new_project",
    "path": "app/projects/my_new_project"
  }
}
```

#### GET /api/projects/<name>
Load a project and verify structure.

**Response:**
```json
{
  "name": "example_project",
  "structure_valid": true,
  "missing_files": [],
  "agents": ["code-reviewer", "test-writer"],
  "skills": ["web-search", "code-analysis"],
  "tools": ["Read", "Edit", "Bash", "CustomTool"],
  "snippet_categories": ["development", "documentation"]
}
```

#### DELETE /api/projects/<name>
Delete a project (with confirmation).

**Response:**
```json
{
  "success": true,
  "message": "Project deleted"
}
```

#### POST /api/projects/<name>/export
Export project as zip file.

**Response:**
Binary zip file download.

#### POST /api/projects/import
Import a project from zip file.

**Request:**
Multipart form data with zip file.

**Response:**
```json
{
  "success": true,
  "project_name": "imported_project"
}
```

### 4.2 Session Management

#### GET /api/projects/<name>/session
Load current session.

**Response:**
Complete current_session.json content.

#### POST /api/projects/<name>/session
Save session (auto-save on every change).

**Request:**
Complete session JSON structure.

**Response:**
```json
{
  "success": true,
  "saved_at": "2025-11-30T15:45:00Z"
}
```

#### POST /api/projects/<name>/session/new
Create new session (backs up current).

**Response:**
```json
{
  "success": true,
  "backup_file": "current_session.json.202511301545",
  "new_session": {}
}
```

#### GET /api/projects/<name>/session/backups
List available session backups.

**Response:**
```json
{
  "backups": [
    {
      "filename": "current_session.json.202511301545",
      "timestamp": "2025-11-30T15:45:00Z",
      "size": 12345
    }
  ]
}
```

#### POST /api/projects/<name>/session/restore
Restore a session backup.

**Request:**
```json
{
  "backup_filename": "current_session.json.202511301545"
}
```

**Response:**
```json
{
  "success": true,
  "session": {}
}
```

### 4.3 Agent Management

#### GET /api/projects/<name>/agents
List all agents in project.

**Response:**
```json
{
  "agents": [
    {
      "name": "code-reviewer",
      "description": "Reviews code for bugs...",
      "model": "inherit",
      "tools": ["Read", "Grep"],
      "skills": ["code-analysis"]
    }
  ]
}
```

#### GET /api/projects/<name>/agents/<agent_name>
Get agent definition.

**Response:**
Agent YAML + markdown content.

#### POST /api/projects/<name>/agents
Create new agent.

**Request:**
Agent YAML + markdown content.

#### PUT /api/projects/<name>/agents/<agent_name>
Update agent.

#### DELETE /api/projects/<name>/agents/<agent_name>
Delete agent.

### 4.4 Skill Management

#### GET /api/projects/<name>/skills
List all skills.

**Response:**
```json
{
  "skills": [
    {
      "name": "web-search",
      "description": "Search the web for current information using available tools",
      "version": "1.0.0",
      "author": "Your Name"
    }
  ]
}
```

#### GET /api/projects/<name>/skills/<skill_name>
Get skill definition (markdown content with YAML frontmatter).

**Response:**
```json
{
  "name": "web-search",
  "description": "Search the web...",
  "version": "1.0.0",
  "author": "Your Name",
  "content": "# Web Search Skill\n\nThis skill explains..."
}
```

#### POST /api/projects/<name>/skills
Create new skill.

**Request:**
```json
{
  "name": "web-search",
  "description": "Search the web...",
  "version": "1.0.0",
  "author": "Your Name",
  "content": "# Web Search Skill\n\nThis skill explains..."
}
```

#### PUT /api/projects/<name>/skills/<skill_name>
Update skill.

#### DELETE /api/projects/<name>/skills/<skill_name>
Delete skill.

### 4.5 Tool Management

#### GET /api/projects/<name>/tools
List all tools.

#### GET /api/projects/<name>/tools/<tool_name>
Get tool definition.

#### POST /api/projects/<name>/tools
Create new tool (JSON or Python).

#### PUT /api/projects/<name>/tools/<tool_name>
Update tool.

#### DELETE /api/projects/<name>/tools/<tool_name>
Delete tool.

### 4.6 Snippet Management

#### GET /api/projects/<name>/snippets
List all snippets with categories.

**Response:**
```json
{
  "snippets": [
    {
      "name": "git-status",
      "category": "development",
      "path": "development/git-status.md"
    },
    {
      "name": "readme-template",
      "category": null,
      "path": "readme-template.md"
    }
  ],
  "categories": ["development", "documentation"]
}
```

#### GET /api/projects/<name>/snippets/<path:path>
Get snippet content.

#### POST /api/projects/<name>/snippets
Create new snippet.

**Request:**
```json
{
  "name": "my-snippet",
  "category": "development",
  "content": "Snippet markdown content..."
}
```

#### PUT /api/projects/<name>/snippets/<path:path>
Update snippet.

#### DELETE /api/projects/<name>/snippets/<path:path>
Delete snippet.

#### POST /api/projects/<name>/snippets/categories
Create new category.

#### DELETE /api/projects/<name>/snippets/categories/<category>
Delete category (moves snippets to root).

### 4.7 Execution

#### POST /api/projects/<name>/execute
Execute current session (send to Anthropic API).

**Request:**
```json
{
  "stream": true
}
```

**Response:**
Server-Sent Events stream with model response, or complete JSON response.

### 4.8 Testing/Simulation

#### POST /api/simulate
Simulate an Anthropic API request using test configuration.

**Request:**
Standard Anthropic API request JSON.

**Response:**
Simulated response based on test/config.json rules.

### 4.9 State Management

#### GET /api/projects/<name>/state
Get UI state.

#### POST /api/projects/<name>/state
Save UI state.

**Request:**
Complete state.json content.

---

## 5. UI Components

### 5.1 Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      Header Bar                              │
│  [AnthropIDE Logo]  [Project Selector ▼]  [New] [Export]   │
└─────────────────────────────────────────────────────────────┘
┌──────────────┬──────────────────────────────────────────────┐
│              │                                               │
│   Snippet    │          Main Content Area                   │
│   Browser    │                                               │
│              │  ┌─────────────────────────────────────────┐ │
│  📁 Category │  │  [Session] [Agents] [Skills] [Tools]    │ │
│   └─ snippet │  └─────────────────────────────────────────┘ │
│  📁 Dev      │                                               │
│   ├─ git     │  Session Editor:                             │
│   └─ docker  │  ┌───────────────────────────────────────┐  │
│  📄 Readme   │  │ Model: [claude-sonnet-4-5... ▼]       │  │
│              │  │ Max Tokens: [8192          ]          │  │
│              │  ├───────────────────────────────────────┤  │
│  [+ New]     │  │ ▼ System Prompts (2)                  │  │
│  [+ Category]│  │   📝 Main system prompt               │  │
│              │  │   📝 CLAUDE.md (cached)               │  │
│              │  ├───────────────────────────────────────┤  │
│              │  │ ▼ Tools (3)                           │  │
│              │  │   🔧 Read                             │  │
│              │  │   🔧 Edit                             │  │
│              │  │   🔧 Bash                             │  │
│              │  ├───────────────────────────────────────┤  │
│              │  │ ▼ Messages (1)                        │  │
│              │  │   👤 User: Fix the typo...            │  │
│              │  │      [Edit] [Delete] [↕]              │  │
│              │  │   [+ Add Message]                     │  │
│              │  └───────────────────────────────────────┘  │
│              │                                               │
└──────────────┴──────────────────────────────────────────────┘
```

### 5.2 Project Selector

**Component:** Dropdown in header bar

**Features:**
- Lists all projects
- Shows project name and description
- Create new project button
- Import project option
- Export current project button

**Behavior:**
- On selection: Load project, verify structure, load session and state
- Auto-save current project before switching

### 5.3 Session Editor

**Component:** Main content area with collapsible sections

#### Model Configuration
- Model dropdown (populated from available models)
- Max tokens input (number)
- Temperature slider (0-1)
- Other API parameters as needed

#### System Prompts Section
- Collapsible section header: "▼ System Prompts (count)"
- List of system prompt blocks
- Each block shows:
  - Type indicator (text/image)
  - Preview of content (first 100 chars)
  - Cache control indicator if present
  - Edit button (opens modal)
  - Delete button
  - Drag handle for reordering
- Add system prompt button

#### Tools Section
- Collapsible section header: "▼ Tools (count)"
- List of enabled tools
- Each tool shows:
  - Tool name
  - Brief description
  - Remove button
- Add tool dropdown (from project tools)
- Edit tool button (opens tool editor modal)

#### Messages Section
- Collapsible section header: "▼ Messages (count)"
- List of messages in conversation order
- Each message shows:
  - Role (user/assistant) with icon
  - Preview of content
  - Edit button (opens message editor modal)
  - Delete button
  - Drag handle for reordering (jQuery UI Sortable)
- Add message button

**Auto-save:**
Changes trigger debounced auto-save to `current_session.json` via AJAX (500ms delay after last change). This prevents excessive file I/O while typing and reduces risk of concurrent write conflicts.

### 5.4 Snippet Browser (Sidebar)

**Component:** Left sidebar panel

**Features:**
- Hierarchical tree view of snippets
- Two levels: categories and snippets
- Each category is collapsible/expandable
- **Drag-and-drop snippet to main editor to insert**:
  - **Target**: Drop zones in Session Editor for system prompts and messages
  - **System Prompt**: Drop on "System Prompts" section → creates new system block with snippet content
  - **Messages**: Drop on "Messages" section → creates new user message with snippet content
  - **Existing Message**: Drop on a message widget → appends snippet to that message's text content
  - Visual drop zone highlights appear on hover
- Right-click context menu:
  - Edit snippet
  - Delete snippet
  - Create category
  - Rename category
- Buttons:
  - [+ New Snippet]
  - [+ New Category]

**State Persistence:**
- Expanded/collapsed state saved to state.json
- Scroll position saved

### 5.5 Snippet Editor Modal

**Component:** Large modal dialog with CodeMirror

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Edit Snippet: [git-status          ] [Save] [Cancel] │
├──────────────────┬──────────────────────────────────┤
│                  │                                   │
│   CodeMirror     │     Markdown Preview             │
│   Editor         │     (live update)                │
│                  │                                   │
│  1 # Git Status  │  Git Status                      │
│  2               │                                   │
│  3 ```           │  ```                              │
│  4 git status    │  git status                       │
│  5 ```           │  ```                              │
│                  │                                   │
└──────────────────┴──────────────────────────────────┘
```

**Features:**
- Name input field at top
- Category dropdown (optional)
- Split view: CodeMirror on left, rendered markdown on right
- Live preview updates as you type (debounced)
- Syntax highlighting for code blocks
- Save button writes to disk via AJAX
- Cancel button discards changes

### 5.6 Agent Editor Modal

**Component:** Modal with tabs

**Main Tab - YAML Configuration:**
Form fields for YAML frontmatter:
- Name (text input, readonly for existing agents)
- Description (textarea)
- Model (dropdown: inherit, or model list)
- Tools (multi-select dropdown from project tools)
- Skills (multi-select dropdown from project skills)
- Color (color picker or dropdown)
- Permission Mode (dropdown: default, auto, prompt)

**Main Tab - Prompt Content:**
- CodeMirror editor for markdown content below YAML
- Preview pane on right

**Buttons:**
- [Save] - Save entire agent (YAML + content)
- [Delete] - Delete agent (confirm dialog)
- [Cancel] - Close without saving

### 5.7 Skill Editor Modal

**Component:** Modal with split view (similar to Snippet Editor)

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Edit Skill                           [Save] [Cancel] │
├──────────────────┬──────────────────────────────────┤
│  Metadata Form   │                                   │
│  Name: [____]    │     CodeMirror Editor             │
│  Desc: [____]    │     (Markdown)                    │
│  Ver:  [____]    │                                   │
│  Auth: [____]    │  # Web Search Skill               │
│                  │                                   │
│                  │  This skill explains...           │
│                  │                                   │
├──────────────────┴──────────────────────────────────┤
│                Markdown Preview                      │
│                (Rendered output)                     │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Left panel: YAML metadata form fields
  - Name (text input, readonly for existing skills)
  - Description (textarea)
  - Version (text input, e.g., "1.0.0")
  - Author (text input, optional)
- Top right: CodeMirror editor for markdown content
- Bottom right: Live markdown preview (debounced)
- [Save] button writes YAML frontmatter + content to `skills/<name>.md`
- [Delete] button (for existing skills) - confirm dialog
- [Cancel] button discards changes

**Note**: Skills are single markdown files with YAML frontmatter, no additional files or tabs needed.

### 5.8 Tool Editor Modal

**Component:** Modal with conditional layout based on tool type

**For JSON Tools:**
Form with fields:
- Name (text input)
- Description (textarea)
- Input Schema (JSON editor with validation)

**For Python Tools:**
- Name (readonly, derived from filename)
- File upload/edit:
  - CodeMirror Python editor
  - Syntax highlighting
  - Shows describe() and run() function signatures
  - Validation that required functions exist

**Buttons:**
- [Save]
- [Test] (optional: run describe() and validate schema)
- [Delete]
- [Cancel]

### 5.9 Message Editor Modal

**Component:** Modal for editing individual message content

**Fields:**
- Role (dropdown: user, assistant)
- Content blocks (array):
  - Type selector (text, image, tool_use, tool_result)
  - Content editor (CodeMirror for text, form for structured types)
  - Add/remove content blocks
  - Reorder content blocks

**For tool_use blocks:**
- Tool name (dropdown)
- Tool ID (auto-generated)
- Input parameters (JSON editor matching tool schema)

**For tool_result blocks:**
- Tool use ID dropdown - populated from all tool_use IDs in previous messages
  - Shows: "toolu_123 (Read - src/app.py)" for context
  - If no tool_use found in conversation, shows warning: "No tool_use blocks found. Add a tool_use first."
- Result content (text editor or JSON editor for structured results)
- is_error checkbox (marks result as error)

### 5.10 Session Browser Modal

**Component:** Modal for browsing session backups

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Session History                      [Close]        │
├─────────────────────────────────────────────────────┤
│  📄 2025-11-30 15:45  [Restore] [Preview] [Delete]  │
│     5 messages, 3 tools                             │
│                                                      │
│  📄 2025-11-30 14:30  [Restore] [Preview] [Delete]  │
│     3 messages, 2 tools                             │
│                                                      │
│  📄 2025-11-30 12:00  [Restore] [Preview] [Delete]  │
│     1 message, 0 tools                              │
└─────────────────────────────────────────────────────┘
```

**Features:**
- List of session backups with timestamps
- Preview button shows session content in readonly view
- Restore button loads backup as current session
- Delete button removes backup file
- Sorted by timestamp (newest first)

### 5.11 Package Config Modal

**Component:** Modal for configuring project packaging options

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Package Configuration                [Save] [Cancel] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  API Key Strategy:                                   │
│  ○ CLI Argument (--api-key or env var) [Recommended]│
│  ○ Environment File (.env in project directory)     │
│  ○ Embedded (⚠️ Key stored in package)              │
│  ○ Prompt User (ask on first run)                   │
│                                                      │
│  ─────────────────────────────────────────────────  │
│                                                      │
│  Dependencies:                                       │
│  ☑ Check dependencies on CLI startup                │
│                                                      │
│  requirements.txt:                                   │
│  ┌────────────────────────────────────────────────┐ │
│  │ anthropic>=0.18.0                              │ │
│  │ requests>=2.31.0                               │ │
│  │ beautifulsoup4>=4.12.0                         │ │
│  │                                                │ │
│  └────────────────────────────────────────────────┘ │
│                      [Edit in Full Editor]          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Radio buttons for API key strategy selection
- Warning icon (⚠️) for embedded option with explanation tooltip
- Checkbox for dependency checking enforcement
- Preview of requirements.txt content (first 10 lines)
- Button to open full requirements.txt editor (CodeMirror modal)
- Save writes to project.json (package_config) and requirements.txt
- Accessible from Project menu: "Package Settings..."

**Validation**:
- Embedded strategy shows warning dialog: "API keys will be stored in plain text in the exported package. Only use this for trusted/internal distribution."
- requirements.txt syntax validation (basic: check for package_name==version format)

### 5.12 Raw JSON Editor (Error Recovery)

**Component:** Full-screen modal shown when current_session.json fails to load

**Trigger**: When `SessionManager.load_session()` raises `JSONDecodeError` or validation fails

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  ⚠️ Session File Error                              │
│                                       [Save] [Cancel] │
├─────────────────────────────────────────────────────┤
│  Error: Expecting property name enclosed in double   │
│  quotes: line 15 column 5 (char 342)                │
│                                                      │
│  The session file contains invalid JSON. You can    │
│  edit it directly below to fix the issue.           │
│                                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ 1  {                                           │ │
│  │ 2    "model": "claude-sonnet-4-5-20250929",   │ │
│  │ 3    "max_tokens": 8192,                      │ │
│  │ 4    "system": [],                            │ │
│  │ 5    "tools": [],                             │ │
│  │ 6    "messages": [                            │ │
│  │ 7      {                                      │ │
│  │ 8        "role": "user"                       │ │
│  │ 9        "content": [...]     <-- Error here  │ │
│  │ 10     }                                       │ │
│  │                                                │ │
│  │  (CodeMirror with JSON syntax highlighting     │ │
│  │   and error squiggles)                         │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  [Validate JSON] button shows parse result          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Shows full JSON decode error message at top
- CodeMirror editor with JSON mode and syntax highlighting
- Line numbers
- Error highlighting at the problematic line
- [Validate JSON] button - tries to parse JSON and shows result (success/error)
- [Save] button - writes raw content back to file (even if invalid)
  - Shows confirmation if still invalid: "JSON is still invalid. Save anyway?"
- [Cancel] button - discards changes, tries to load from backup or creates new session

**Behavior:**
- Auto-shown when project loads and session fails to parse
- User can fix JSON manually and save
- If user cancels, offer to restore from most recent backup
- If no backups, create fresh default session

### 5.13 Collapsible Widgets

**Behavior:**
All major sections (System, Tools, Messages) and individual items can be collapsed:

**Collapsed State:**
```
▶ System Prompts (2) — You are Claude Code, Anthropic's official...
```

**Expanded State:**
```
▼ System Prompts (2)
  📝 Main system prompt
     You are Claude Code, Anthropic's official CLI...
     [Edit] [Delete]
  📝 CLAUDE.md (cached)
     Contents of /home/user/.claude/CLAUDE.md...
     [Edit] [Delete]
```

**Implementation:**
- Click on header to toggle
- jQuery slideUp/slideDown animation
- State saved to state.json
- Shows preview text when collapsed

### 5.12 Drag and Drop

**jQuery UI Sortable** for:
- Reordering messages
- Reordering system prompt blocks
- Reordering tool blocks
- Reordering content within a message

**Configuration:**
```javascript
$('.messages-list').sortable({
  handle: '.drag-handle',
  axis: 'y',
  update: function(event, ui) {
    // Auto-save new order
    saveSession();
  }
});
```

**Visual Feedback:**
- Drag handle icon (⋮⋮) on hover
- Placeholder while dragging
- Cursor changes to move pointer

---

## 6. Implementation Details

### 6.1 Backend Components

#### 6.1.1 Configuration (config.py)

```python
import os
from pathlib import Path

# Application settings
APP_ROOT = Path(__file__).parent
PROJECT_ROOT = APP_ROOT / 'projects'  # Fixed: was 'app/projects', inconsistent with architecture
STATIC_ROOT = APP_ROOT / 'static'
TEMPLATE_ROOT = APP_ROOT / 'templates'

# API settings
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DEFAULT_MODEL = 'claude-sonnet-4-5-20250929'

# Project settings
MAX_SESSION_BACKUPS = 20  # Default, user-configurable per project
AUTO_SAVE = True
SESSION_BACKUP_FORMAT = 'current_session.json.%Y%m%d%H%M%S%f'  # Added %f (microseconds) to prevent collisions

# File extensions
AGENT_EXT = '.md'
SKILL_MAIN = 'main.md'
TOOL_JSON_EXT = '.json'
TOOL_PY_EXT = '.py'
SNIPPET_EXT = '.md'

# Validation
MAX_PROJECT_NAME_LENGTH = 50
ALLOWED_PROJECT_NAME_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
MAX_SNIPPET_CATEGORIES = 2  # Only two levels of nesting

# Server settings
HOST = '0.0.0.0'
PORT = 8080
DEBUG = True
RELOADER = True
```

#### 6.1.2 Data Models (lib/data_models.py)

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class ProjectSettings(BaseModel):
    max_session_backups: int = 20
    auto_save: bool = True
    default_model: str = "claude-sonnet-4-5-20250929"

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    created: datetime
    modified: datetime
    settings: ProjectSettings = ProjectSettings()

    @validator('name')
    def validate_name(cls, v):
        # Validation logic
        return v

class SystemBlock(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    cache_control: Optional[Dict[str, str]] = None

class ToolSchema(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class ContentBlock(BaseModel):
    type: Literal["text", "image", "tool_use", "tool_result"]
    # Additional fields based on type

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: List[ContentBlock]

class Session(BaseModel):
    model: str
    max_tokens: int = 8192
    temperature: Optional[float] = 1.0
    system: List[SystemBlock] = []
    tools: List[ToolSchema] = []
    messages: List[Message] = []

    def validate(self):
        """
        Validate session can be sent to Anthropic API.

        Raises:
            ValueError: If session has validation errors

        Validates:
        - Model name is valid
        - max_tokens is positive and within limits (0 < max_tokens <= 200000)
        - temperature is within range (0 <= temp <= 1)
        - Messages alternate between user/assistant roles
        - tool_use_id references in tool_result blocks match existing tool_use blocks
        - Tool names in messages exist in the tools list
        - System blocks have required fields
        """
        if self.max_tokens <= 0 or self.max_tokens > 200000:
            raise ValueError(f"max_tokens must be between 1 and 200000, got {self.max_tokens}")

        if self.temperature is not None and (self.temperature < 0 or self.temperature > 1):
            raise ValueError(f"temperature must be between 0 and 1, got {self.temperature}")

        # Validate message role alternation
        prev_role = None
        for i, msg in enumerate(self.messages):
            if prev_role == msg.role and prev_role is not None:
                # Allow consecutive user messages (tool results), but warn for consecutive assistant messages
                if msg.role == 'assistant':
                    raise ValueError(f"Message {i}: consecutive assistant messages not allowed")
            prev_role = msg.role

        # Collect tool_use IDs and validate tool_result references
        tool_use_ids = set()
        tool_names_in_session = {tool.name for tool in self.tools}

        for i, msg in enumerate(self.messages):
            for j, block in enumerate(msg.content):
                if block.type == 'tool_use':
                    tool_use_ids.add(block.id)
                    if block.name not in tool_names_in_session:
                        raise ValueError(
                            f"Message {i}, block {j}: tool_use references unknown tool '{block.name}'"
                        )
                elif block.type == 'tool_result':
                    if block.tool_use_id not in tool_use_ids:
                        raise ValueError(
                            f"Message {i}, block {j}: tool_result references unknown tool_use_id '{block.tool_use_id}'"
                        )

class AgentConfig(BaseModel):
    name: str
    description: str
    model: str = "inherit"
    tools: List[str] = []
    skills: List[str] = []
    color: str = "blue"
    prompt: str  # The markdown content after YAML frontmatter

class SkillConfig(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    content: str  # The markdown content after YAML frontmatter (instructional)

class TestMatch(BaseModel):
    type: Literal["regex", "contains"]
    path: str  # Dot notation JSON path
    pattern: Optional[str] = None  # For regex
    value: Optional[Any] = None  # For contains

class TestResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: List[ContentBlock]

class TestSequenceItem(BaseModel):
    match: TestMatch
    response: TestResponse
    tool_behavior: Literal["mock", "execute", "skip"] = "mock"
    tool_results: Optional[Dict[str, Any]] = None

class TestCase(BaseModel):
    name: str
    sequence: List[TestSequenceItem]

class TestConfig(BaseModel):
    tests: List[TestCase]

class UIState(BaseModel):
    version: str = "1.0"
    selected_project: Optional[str] = None
    ui: Dict[str, Any] = {}
    last_modified: datetime
```

#### 6.1.3 Project Manager (lib/project_manager.py)

```python
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json
import shutil

from .data_models import Project, ProjectSettings
from .validator import validate_project_structure

class ProjectManager:
    def __init__(self, projects_root: Path):
        self.projects_root = projects_root
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> List[Project]:
        """List all projects."""
        projects = []
        for project_dir in self.projects_root.iterdir():
            if project_dir.is_dir():
                try:
                    project = self.load_project_metadata(project_dir.name)
                    projects.append(project)
                except Exception as e:
                    # Log error, skip invalid project
                    continue
        return projects

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Create new project with full directory structure."""
        # Validate name
        # Create directory structure
        # Create default files
        # Return Project object
        pass

    def load_project(self, name: str) -> Dict:
        """Load project and verify structure."""
        project_path = self.projects_root / name

        # Verify structure
        structure_valid, missing = validate_project_structure(project_path)

        # Create missing files/dirs from defaults
        if missing:
            self._create_missing_files(project_path, missing)

        # Load metadata
        project = self.load_project_metadata(name)

        # Return project info with assets
        return {
            'name': name,
            'structure_valid': structure_valid,
            'missing_files': missing,
            'agents': self._list_agents(project_path),
            'skills': self._list_skills(project_path),
            'tools': self._list_tools(project_path),
            'snippet_categories': self._list_snippet_categories(project_path),
        }

    def delete_project(self, name: str) -> bool:
        """Delete a project."""
        project_path = self.projects_root / name
        if project_path.exists():
            shutil.rmtree(project_path)
            return True
        return False

    def export_project(self, name: str, output_path: Path) -> Path:
        """Export project as zip file."""
        # Create zip archive
        pass

    def import_project(self, zip_path: Path) -> str:
        """Import project from zip file."""
        # Extract and validate
        pass
```

#### 6.1.4 Session Manager (lib/session_manager.py)

```python
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json
import shutil

from .data_models import Session

class SessionManager:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.session_file = project_path / 'current_session.json'

    def load_session(self) -> Session:
        """
        Load current session.

        Returns:
            Session object if successfully loaded and parsed
            None if JSON decode fails (caller should show raw JSON editor)

        Raises:
            JSONDecodeError: If file contains invalid JSON (caller handles)
        """
        if not self.session_file.exists():
            return Session(model="claude-sonnet-4-5-20250929", max_tokens=8192)

        with open(self.session_file, 'r') as f:
            data = json.load(f)  # May raise JSONDecodeError

        return Session(**data)  # May raise ValidationError

    def save_session(self, session: Session) -> bool:
        """
        Save session (auto-save on every change).

        Note: Does NOT validate before saving - saving should never fail.
        Validation is for informational purposes only (warnings in UI).
        """
        # Use the file locking mechanism from Section 7.1
        save_json(self.session_file, session.dict())

        return True

    def create_backup(self) -> str:
        """Create timestamped backup of current session."""
        if not self.session_file.exists():
            return None

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')  # Includes microseconds to prevent collisions
        backup_file = self.project_path / f'current_session.json.{timestamp}'

        shutil.copy2(self.session_file, backup_file)

        # Clean old backups if needed
        self._cleanup_old_backups()

        return backup_file.name

    def list_backups(self) -> List[Dict]:
        """List all session backups."""
        backups = []
        for file in self.project_path.glob('current_session.json.*'):
            backups.append({
                'filename': file.name,
                'timestamp': self._parse_timestamp(file.name),
                'size': file.stat().st_size,
            })

        # Sort by timestamp descending
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups

    def restore_backup(self, backup_filename: str) -> Session:
        """Restore session from backup."""
        backup_file = self.project_path / backup_filename

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup not found: {backup_filename}")

        # Create backup of current before restoring
        self.create_backup()

        # Copy backup to current
        shutil.copy2(backup_file, self.session_file)

        return self.load_session()

    def delete_backup(self, backup_filename: str) -> bool:
        """Delete a backup file."""
        backup_file = self.project_path / backup_filename
        if backup_file.exists():
            backup_file.unlink()
            return True
        return False

    def _cleanup_old_backups(self):
        """Keep only MAX_SESSION_BACKUPS most recent backups."""
        # Load project settings for max_backups
        # Delete oldest backups if over limit
        pass
```

#### 6.1.5 Tool Manager (lib/tool_manager.py)

```python
from pathlib import Path
from typing import List, Dict, Any, Callable
import json
import importlib.util
import sys

from .data_models import ToolSchema

class ToolManager:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.tools_path = project_path / 'tools'
        self.tools_path.mkdir(exist_ok=True)
        self._loaded_tools: Dict[str, Callable] = {}

    def list_tools(self) -> List[str]:
        """List all available tools."""
        tools = []

        # JSON tools
        for json_file in self.tools_path.glob('*.json'):
            tools.append(json_file.stem)

        # Python tools
        for py_file in self.tools_path.glob('*.py'):
            if not py_file.name.startswith('_'):
                tools.append(py_file.stem)

        return sorted(tools)

    def load_tool_schema(self, tool_name: str) -> ToolSchema:
        """Load tool schema for Anthropic API."""
        json_tool = self.tools_path / f'{tool_name}.json'
        py_tool = self.tools_path / f'{tool_name}.py'

        if json_tool.exists():
            with open(json_tool, 'r') as f:
                data = json.load(f)
            return ToolSchema(**data)

        elif py_tool.exists():
            # Import module and call describe()
            module = self._load_python_module(tool_name, py_tool)
            if hasattr(module, 'describe'):
                schema_dict = module.describe()
                return ToolSchema(**schema_dict)
            else:
                raise ValueError(f"Python tool {tool_name} missing describe() function")

        else:
            raise FileNotFoundError(f"Tool not found: {tool_name}")

    def load_all_tools(self) -> List[ToolSchema]:
        """Load all tool schemas for session."""
        schemas = []
        for tool_name in self.list_tools():
            try:
                schema = self.load_tool_schema(tool_name)
                schemas.append(schema)
            except Exception as e:
                # Log error, skip invalid tool
                continue
        return schemas

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters."""
        py_tool = self.tools_path / f'{tool_name}.py'

        if not py_tool.exists():
            raise ValueError(f"Tool {tool_name} is not executable (JSON tools cannot be executed)")

        # Load module
        module = self._load_python_module(tool_name, py_tool)

        if not hasattr(module, 'run'):
            raise ValueError(f"Python tool {tool_name} missing run() function")

        # Execute tool
        try:
            result = module.run(**parameters)
            return str(result)
        except Exception as e:
            # Format error per Anthropic SDK conventions
            return f"Error executing {tool_name}: {str(e)}"

    def save_tool(self, tool_name: str, content: Dict[str, Any], tool_type: str = 'json'):
        """Save tool definition."""
        if tool_type == 'json':
            tool_file = self.tools_path / f'{tool_name}.json'
            with open(tool_file, 'w') as f:
                json.dump(content, f, indent=2)

        elif tool_type == 'python':
            tool_file = self.tools_path / f'{tool_name}.py'
            with open(tool_file, 'w') as f:
                f.write(content['code'])

    def delete_tool(self, tool_name: str):
        """Delete a tool."""
        json_tool = self.tools_path / f'{tool_name}.json'
        py_tool = self.tools_path / f'{tool_name}.py'

        if json_tool.exists():
            json_tool.unlink()
        if py_tool.exists():
            py_tool.unlink()

    def _load_python_module(self, tool_name: str, tool_path: Path):
        """Dynamically load Python module."""
        # Use unique module name with path hash to avoid conflicts with built-in modules
        # and allow reloading when tool files are modified
        import hashlib
        module_name = f"anthropide_tool_{tool_name}_{hashlib.md5(str(tool_path).encode()).hexdigest()[:8]}"

        # Remove from cache if already loaded (allows hot-reloading)
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
```

#### 6.1.6 Test Simulator (lib/test_simulator.py)

```python
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import re

from .data_models import TestConfig, TestCase, Message

class TestSimulator:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.test_config_file = project_path / 'tests' / 'config.json'
        self.test_config: Optional[TestConfig] = None
        self.conversation_state: List[Message] = []

    def load_test_config(self):
        """Load test configuration."""
        if not self.test_config_file.exists():
            self.test_config = TestConfig(tests=[])
            return

        with open(self.test_config_file, 'r') as f:
            data = json.load(f)

        self.test_config = TestConfig(**data)

    def simulate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Anthropic API response based on test configuration.

        Args:
            request: Standard Anthropic API request

        Returns:
            Simulated API response
        """
        if not self.test_config:
            self.load_test_config()

        # Find matching test case
        for test in self.test_config.tests:
            response = self._try_match_test(test, request)
            if response:
                return response

        # No match found, return default error
        return {
            'error': {
                'type': 'no_test_match',
                'message': 'No matching test case found for request'
            }
        }

    def _try_match_test(self, test: TestCase, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try to match request against test sequence."""
        # Track position in sequence
        for seq_item in test.sequence:
            if self._matches(seq_item.match, request):
                # Handle tool behavior
                if seq_item.tool_behavior == 'mock' and seq_item.tool_results:
                    # Inject mock tool results if needed
                    pass
                elif seq_item.tool_behavior == 'execute':
                    # Set flag to execute real tools
                    pass

                # Return canned response
                return {
                    'role': seq_item.response.role,
                    'content': [block.dict() for block in seq_item.response.content]
                }

        return None

    def _matches(self, match, request: Dict[str, Any]) -> bool:
        """Check if request matches the match criteria."""
        # Extract value from request using dot-notation path
        value = self._get_by_path(request, match.path)

        if match.type == 'regex':
            pattern = re.compile(match.pattern)
            return bool(pattern.search(str(value)))

        elif match.type == 'contains':
            return match.value in str(value)

        return False

    def _get_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """
        Extract value from nested dict using dot notation.

        Examples:
            messages.-1.content.0.text
            system.0.type
        """
        parts = path.split('.')
        current = data

        for part in parts:
            if part.lstrip('-').isdigit():
                # Array index
                idx = int(part)
                current = current[idx]
            else:
                # Object key
                current = current.get(part)

            if current is None:
                return None

        return current
```

### 6.2 Frontend Components

#### 6.2.1 Main Application (static/js/app.js)

```javascript
// Main application initialization
$(document).ready(function() {
    // Initialize application
    AnthropIDE.init();
});

const AnthropIDE = {
    currentProject: null,

    init: function() {
        this.loadState();
        this.initializeUI();
        this.bindEvents();
        this.loadProjects();
    },

    loadState: function() {
        // Load UI state from localStorage or server
        $.get('/api/state', (data) => {
            this.state = data;
            this.applyState();
        });
    },

    initializeUI: function() {
        // Initialize jQuery UI components
        this.initializeSortable();
        this.initializeModals();
        this.initializeTooltips();
    },

    initializeSortable: function() {
        // Messages sortable
        $('.messages-list').sortable({
            handle: '.drag-handle',
            axis: 'y',
            placeholder: 'message-placeholder',
            update: function(event, ui) {
                AnthropIDE.session.reorderMessages();
                AnthropIDE.session.save();
            }
        });

        // Similar for system blocks, tools, etc.
    },

    bindEvents: function() {
        // Global event handlers
        $(document).on('click', '.collapsible-header', this.toggleCollapse);
        $(document).on('change', 'input, textarea, select', this.handleInputChange);
    },

    toggleCollapse: function(e) {
        const $header = $(e.currentTarget);
        const $content = $header.next('.collapsible-content');
        const $icon = $header.find('.collapse-icon');

        $content.slideToggle(200, function() {
            const isExpanded = $content.is(':visible');
            $icon.text(isExpanded ? '▼' : '▶');

            // Save state
            AnthropIDE.saveWidgetState($header.data('widget-id'), isExpanded);
        });
    },

    handleInputChange: function(e) {
        // Debounce and auto-save
        clearTimeout(AnthropIDE.saveTimer);
        AnthropIDE.saveTimer = setTimeout(() => {
            AnthropIDE.session.save();
        }, 500);
    }
};
```

#### 6.2.2 Session Editor (static/js/session.js)

```javascript
const SessionEditor = {
    session: null,

    load: function(projectName) {
        $.get(`/api/projects/${projectName}/session`, (data) => {
            this.session = data;
            this.render();
        });
    },

    render: function() {
        this.renderModelConfig();
        this.renderSystemBlocks();
        this.renderTools();
        this.renderMessages();
    },

    renderMessages: function() {
        const $container = $('#messages-container');
        $container.empty();

        this.session.messages.forEach((msg, idx) => {
            const $message = this.createMessageWidget(msg, idx);
            $container.append($message);
        });

        // Initialize sortable
        $container.sortable('refresh');
    },

    createMessageWidget: function(message, index) {
        const role = message.role;
        const icon = role === 'user' ? '👤' : '🤖';
        const preview = this.getMessagePreview(message);

        const $widget = $(`
            <div class="message-widget" data-index="${index}">
                <div class="message-header collapsible-header">
                    <span class="drag-handle">⋮⋮</span>
                    <span class="collapse-icon">▼</span>
                    <span class="role-icon">${icon}</span>
                    <span class="role-label">${role}</span>
                    <span class="preview">${preview}</span>
                    <div class="message-actions">
                        <button class="edit-btn" data-index="${index}">Edit</button>
                        <button class="delete-btn" data-index="${index}">Delete</button>
                    </div>
                </div>
                <div class="message-content collapsible-content">
                    ${this.renderMessageContent(message)}
                </div>
            </div>
        `);

        return $widget;
    },

    getMessagePreview: function(message) {
        // Get first 100 chars of text content
        for (let block of message.content) {
            if (block.type === 'text') {
                return block.text.substring(0, 100) + '...';
            }
        }
        return '(no text content)';
    },

    addMessage: function() {
        // Open modal to create new message
        MessageModal.open(null, (newMessage) => {
            this.session.messages.push(newMessage);
            this.render();
            this.save();
        });
    },

    editMessage: function(index) {
        const message = this.session.messages[index];
        MessageModal.open(message, (updatedMessage) => {
            this.session.messages[index] = updatedMessage;
            this.render();
            this.save();
        });
    },

    deleteMessage: function(index) {
        if (confirm('Delete this message?')) {
            this.session.messages.splice(index, 1);
            this.render();
            this.save();
        }
    },

    save: function() {
        $.ajax({
            url: `/api/projects/${AnthropIDE.currentProject}/session`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(this.session),
            success: () => {
                console.log('Session saved');
            },
            error: (xhr) => {
                alert('Error saving session: ' + xhr.responseText);
            }
        });
    }
};
```

#### 6.2.3 Snippet Browser (static/js/snippets.js)

```javascript
const SnippetBrowser = {
    snippets: [],
    categories: [],

    load: function(projectName) {
        $.get(`/api/projects/${projectName}/snippets`, (data) => {
            this.snippets = data.snippets;
            this.categories = data.categories;
            this.render();
        });
    },

    render: function() {
        const $container = $('#snippet-browser');
        $container.empty();

        // Render category tree
        const tree = this.buildTree();
        const $tree = this.renderTree(tree);
        $container.append($tree);

        // Restore expanded state
        this.restoreExpandedState();
    },

    buildTree: function() {
        // Group snippets by category
        const tree = {};

        this.snippets.forEach(snippet => {
            const category = snippet.category || '_root';
            if (!tree[category]) {
                tree[category] = [];
            }
            tree[category].push(snippet);
        });

        return tree;
    },

    renderTree: function(tree) {
        const $tree = $('<ul class="snippet-tree"></ul>');

        // Render categories
        for (let category in tree) {
            if (category === '_root') {
                // Root level snippets
                tree[category].forEach(snippet => {
                    $tree.append(this.renderSnippet(snippet));
                });
            } else {
                // Category with snippets
                const $category = this.renderCategory(category, tree[category]);
                $tree.append($category);
            }
        }

        return $tree;
    },

    renderCategory: function(categoryName, snippets) {
        const $category = $(`
            <li class="snippet-category" data-category="${categoryName}">
                <div class="category-header">
                    <span class="collapse-icon">▼</span>
                    <span class="category-icon">📁</span>
                    <span class="category-name">${categoryName}</span>
                </div>
                <ul class="category-snippets"></ul>
            </li>
        `);

        const $snippetList = $category.find('.category-snippets');
        snippets.forEach(snippet => {
            $snippetList.append(this.renderSnippet(snippet));
        });

        // Toggle collapse
        $category.find('.category-header').on('click', function() {
            $snippetList.slideToggle(200);
            const isExpanded = $snippetList.is(':visible');
            $category.find('.collapse-icon').text(isExpanded ? '▼' : '▶');
            SnippetBrowser.saveCategoryState(categoryName, isExpanded);
        });

        return $category;
    },

    renderSnippet: function(snippet) {
        const $snippet = $(`
            <li class="snippet-item" data-path="${snippet.path}">
                <span class="snippet-icon">📄</span>
                <span class="snippet-name">${snippet.name}</span>
            </li>
        `);

        // Make draggable
        $snippet.draggable({
            helper: 'clone',
            cursor: 'move',
            revert: 'invalid'
        });

        // Click to edit
        $snippet.on('click', () => {
            this.editSnippet(snippet);
        });

        // Context menu
        $snippet.on('contextmenu', (e) => {
            e.preventDefault();
            this.showContextMenu(snippet, e.pageX, e.pageY);
        });

        return $snippet;
    },

    editSnippet: function(snippet) {
        SnippetModal.open(snippet, () => {
            this.load(AnthropIDE.currentProject);
        });
    },

    createSnippet: function() {
        SnippetModal.open(null, () => {
            this.load(AnthropIDE.currentProject);
        });
    }
};
```

### 6.3 Standalone CLI Runner

#### 6.3.1 CLI Entry Point (cli/main.py)

```python
#!/usr/bin/env python3
"""
AnthropIDE CLI Runner

Executes packaged AnthropIDE projects as standalone applications.
"""

import argparse
import sys
from pathlib import Path
import anthropic

from .runner import ProjectRunner
from .plugin_loader import ToolPluginLoader
from .history import ConversationHistory

def check_dependencies(requirements_file: Path) -> bool:
    """
    Check if all dependencies in requirements.txt are installed.

    Returns True if all dependencies satisfied, False otherwise.
    Prints detailed error messages for missing packages.
    """
    if not requirements_file.exists():
        return True  # No requirements file, assume OK

    missing = []
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse package name (before ==, >=, <=, etc.)
            import re
            match = re.match(r'^([a-zA-Z0-9_-]+)', line)
            if not match:
                continue

            package = match.group(1)

            # Try to import
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(line)

    if missing:
        print("ERROR: Missing required dependencies:", file=sys.stderr)
        for dep in missing:
            print(f"  - {dep}", file=sys.stderr)
        print("\nInstall with:", file=sys.stderr)
        print(f"  pip install -r {requirements_file}", file=sys.stderr)
        return False

    return True

def main():
    parser = argparse.ArgumentParser(
        description='Run AnthropIDE packaged projects',
    )

    parser.add_argument(
        'project_path',
        type=Path,
        help='Path to project directory or .zip file',
    )

    parser.add_argument(
        '--api-key',
        help='Anthropic API key (or set ANTHROPIC_API_KEY env var)',
    )

    parser.add_argument(
        '--input',
        '-i',
        help='Input message to send (if omitted, enters interactive mode)',
    )

    parser.add_argument(
        '--history',
        type=Path,
        help='Path to conversation history file',
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (use simulation)',
    )

    parser.add_argument(
        '--skip-dependency-check',
        action='store_true',
        help='Skip checking requirements.txt dependencies',
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output',
    )

    args = parser.parse_args()

    # Load project
    runner = ProjectRunner(args.project_path)

    # Check dependencies (unless skipped or project config disables)
    if not args.skip_dependency_check:
        project_metadata = runner.load_project_metadata()
        if project_metadata.get('package_config', {}).get('dependencies_checked', True):
            requirements_file = runner.project_path / 'requirements.txt'
            if not check_dependencies(requirements_file):
                sys.exit(1)

    # Load tool plugins
    tool_loader = ToolPluginLoader(runner.project_path / 'tools')
    tools = tool_loader.load_all_tools()

    # Initialize conversation history
    history = ConversationHistory(args.history or runner.project_path / 'conversation.log')

    # Get API key
    api_key = args.api_key or runner.get_api_key()
    if not api_key:
        print("Error: No API key provided", file=sys.stderr)
        sys.exit(1)

    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Run project
    try:
        if args.test:
            # Use simulation
            runner.run_with_simulation(args.input)
        else:
            # Real execution
            runner.run(
                client=client,
                tools=tools,
                input_message=args.input,
                history=history,
                verbose=args.verbose,
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
```

#### 6.3.2 Execution Engine (cli/runner.py)

```python
"""Project execution engine."""

import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import anthropic

from ..lib.data_models import Session
from ..lib.tool_manager import ToolManager
from .history import ConversationHistory

class ProjectRunner:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.session = self.load_session()
        self.tool_manager = ToolManager(project_path)

    def load_session(self) -> Session:
        """Load current_session.json from project."""
        session_file = self.project_path / 'current_session.json'
        with open(session_file, 'r') as f:
            data = json.load(f)
        return Session(**data)

    def get_api_key(self) -> Optional[str]:
        """Get API key from embedded, env var, or prompt."""
        import os

        # Check for embedded key
        key_file = self.project_path / '.api_key'
        if key_file.exists():
            return key_file.read_text().strip()

        # Check environment
        if 'ANTHROPIC_API_KEY' in os.environ:
            return os.environ['ANTHROPIC_API_KEY']

        # Prompt user
        key = input("Enter Anthropic API key: ").strip()

        # Optionally save for future
        save = input("Save API key for this project? (y/N): ").strip().lower()
        if save == 'y':
            key_file.write_text(key)

        return key

    def run(
        self,
        client: anthropic.Anthropic,
        tools: List[Dict],
        input_message: Optional[str],
        history: ConversationHistory,
        verbose: bool = False,
    ):
        """
        Execute the project with streaming output.

        Agents are spawned automatically when the model calls the Task tool.
        The CLI doesn't need an --agent flag - it loads current_session.json as-is
        and begins execution.
        """

        # Add input message if provided
        if input_message:
            self.session.messages.append({
                'role': 'user',
                'content': [{'type': 'text', 'text': input_message}]
            })

        # Use iterative loop instead of recursion to avoid stack overflow
        # with long multi-turn tool-calling conversations
        max_turns = 100  # Safety limit
        turn_count = 0

        while turn_count < max_turns:
            turn_count += 1

            # Prepare request
            request = {
                'model': self.session.model,
                'max_tokens': self.session.max_tokens,
                'system': [block.dict() for block in self.session.system],
                'tools': tools,
                'messages': [msg.dict() for msg in self.session.messages],
            }

            # Stream response
            if turn_count == 1:
                print("Assistant: ", end='', flush=True)

            with client.messages.stream(**request) as stream:
                response_text = ''
                tool_uses = []

                for event in stream:
                    if event.type == 'content_block_delta':
                        if event.delta.type == 'text_delta':
                            text = event.delta.text
                            print(text, end='', flush=True)
                            response_text += text

                    elif event.type == 'content_block_start':
                        if event.content_block.type == 'tool_use':
                            tool_uses.append(event.content_block)

                print()  # Newline after response

                # Handle tool calls
                if tool_uses:
                    tool_results = self.execute_tools(tool_uses, verbose)

                    # Add assistant message with tool uses
                    self.session.messages.append({
                        'role': 'assistant',
                        'content': [
                            {'type': 'text', 'text': response_text},
                            *[tool.dict() for tool in tool_uses]
                        ]
                    })

                    # Add tool results
                    self.session.messages.append({
                        'role': 'user',
                        'content': tool_results
                    })

                    # Continue loop for next turn

                else:
                    # Conversation complete
                    self.session.messages.append({
                        'role': 'assistant',
                        'content': [{'type': 'text', 'text': response_text}]
                    })

                    # Save to history
                    history.save(self.session)
                    break  # Exit loop

        if turn_count >= max_turns:
            print(f"\nWarning: Reached maximum turn limit ({max_turns})", file=sys.stderr)

    def execute_tools(self, tool_uses: List, verbose: bool) -> List[Dict]:
        """Execute tool calls and return results."""
        results = []

        for tool_use in tool_uses:
            if verbose:
                print(f"\n[Tool: {tool_use.name}]")
                print(f"[Input: {json.dumps(tool_use.input, indent=2)}]")

            try:
                result = self.tool_manager.execute_tool(
                    tool_use.name,
                    tool_use.input,
                )

                if verbose:
                    print(f"[Result: {result[:200]}...]")

                results.append({
                    'type': 'tool_result',
                    'tool_use_id': tool_use.id,
                    'content': result,
                })

            except Exception as e:
                results.append({
                    'type': 'tool_result',
                    'tool_use_id': tool_use.id,
                    'content': f"Error: {str(e)}",
                    'is_error': True,
                })

        return results
```

---

## 7. Security Considerations

### 7.1 File Concurrency & Locking
**Problem**: Multiple operations can write to the same JSON file simultaneously:
- Auto-save from frontend (debounced)
- Manual save operations
- Session backup creation
- External editor modifications

**Solution**: Implement file locking for all JSON write operations:

```python
import fcntl
import json
from pathlib import Path
from typing import Any
from contextlib import contextmanager

@contextmanager
def locked_json_write(file_path: Path):
    """Context manager for locked JSON file writes."""
    # Open file for writing
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a lock file to avoid race conditions
    lock_file = file_path.with_suffix(file_path.suffix + '.lock')

    with open(lock_file, 'w') as lock_fd:
        # Acquire exclusive lock
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

        try:
            # Write to temp file first
            temp_file = file_path.with_suffix(file_path.suffix + '.tmp')

            yield temp_file  # Caller writes to temp_file

            # Atomic rename
            temp_file.rename(file_path)

        finally:
            # Release lock
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_file.unlink(missing_ok=True)

def save_json(file_path: Path, data: Any):
    """Thread-safe JSON save with locking."""
    with locked_json_write(file_path) as temp_file:
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
```

**Usage in SessionManager:**
```python
def save_session(self, session: Session) -> bool:
    """Save session with file locking."""
    session.validate()

    save_json(self.session_file, session.dict())
    return True
```

**Note**: On Windows, use different locking mechanism (msvcrt module).

### 7.2 Custom Tool Execution
- **No sandboxing** - tools run with full system access
- Users are responsible for auditing custom tools
- Clear documentation warning about security implications

### 7.3 API Key Management
- Never commit API keys to version control
- Support multiple key sources (env var, prompt, embedded with caution)
- Embedded keys in packaged projects should be clearly marked as optional

### 7.4 File System Access
- All file operations are scoped to project directories
- No path traversal validation needed (trusted user environment)
- Backup system prevents accidental data loss

### 7.5 Input Validation
- Validate all JSON structures against schemas
- Sanitize project names (alphanumeric + hyphens/underscores only)
- Validate file uploads (zip files only for project import)

---

## 8. Testing Strategy

### 8.1 Backend Unit Tests
Test each manager class in isolation:
- ProjectManager: create, list, load, delete, export, import
- SessionManager: load, save, backup, restore, cleanup
- AgentManager: CRUD operations, YAML parsing
- SkillManager: CRUD, multi-file handling
- ToolManager: loading JSON/Python tools, schema extraction, execution
- TestSimulator: path matching, sequence matching, mock responses

### 8.2 API Integration Tests
Test all endpoints with:
- Valid inputs
- Invalid inputs (error handling)
- Edge cases (empty projects, missing files)
- Concurrent requests (file locking)

### 8.3 Frontend Tests
- jQuery UI interactions (sortable, modals)
- Auto-save functionality
- Drag-and-drop
- State persistence
- CodeMirror integration

### 8.4 End-to-End Tests
- Create project → add agent → add tool → edit session → execute
- Import/export cycle
- Session backup/restore
- Test simulation mode

---

## 9. Deployment & Packaging

### 9.1 Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run development server
.venv/python app.py

# Access at http://localhost:8080
```

### 9.2 Production Deployment

**Option 1: Standalone Server**
```bash
# Use production WSGI server
uv pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### 9.3 CLI Distribution

Package CLI as standalone executable:

```bash
# Install PyInstaller
uv pip install pyinstaller

# Build standalone binary
uv pyinstaller --onefile cli/main.py --name anthropide-cli

# Distribute binary + instructions
```

---

## 10. Future Enhancements

### 10.1 Potential Features
- **Version control integration**: Git commits for session history
- **Collaboration**: Multi-user with WebSocket sync
- **Marketplace**: Share/sell packaged prompts
- **Analytics**: Token usage tracking, cost estimation
- **Template library**: Starter templates for common use cases
- **Agent debugging**: Step-through agent execution
- **Visual prompt builder**: Flowchart-style prompt design

### 10.2 Performance Optimizations
- Cache CodeMirror instances for faster modal loads
- Lazy load snippet content (only load when viewed)
- Virtual scrolling for large message lists
- WebWorker for JSON parsing/validation

### 10.3 Advanced Testing
- Record/replay mode for creating test configurations
- Visual diff for session changes
- Performance benchmarking tools

---

## 11. Appendix

### 11.1 Dependencies (requirements.txt)

```txt
bottle==0.12.25
anthropic==0.18.0
pydantic==2.5.0
jinja2==3.1.2
markdown==3.5.1
pyyaml==6.0.1
```

### 11.2 File Structure Checklist

When creating a new project, ensure these files/directories exist:

- [ ] `agents/` directory
- [ ] `skills/` directory
- [ ] `tools/` directory
- [ ] `snippets/` directory
- [ ] `tests/` directory
- [ ] `tests/config.json` (empty: `{"tests": []}`)
- [ ] `current_session.json` (default session)
- [ ] `project.json` (project metadata)

**Note**: `state.json` is a global file at application root, NOT per-project.

### 11.3 Default Templates

**Default Session (per-project):**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8192,
  "system": [],
  "tools": [],
  "messages": []
}
```

**Default Project Metadata (per-project):**
```json
{
  "name": "project_name",
  "description": "",
  "created": "2025-11-30T00:00:00Z",
  "modified": "2025-11-30T00:00:00Z",
  "settings": {
    "max_session_backups": 20,
    "auto_save": true,
    "default_model": "claude-sonnet-4-5-20250929"
  }
}
```

**Default Global State (application root):**
```json
{
  "version": "1.0",
  "selected_project": null,
  "ui": {
    "active_tabs": {"main": "session", "sidebar": "snippets"},
    "scroll_positions": {},
    "expanded_widgets": {},
    "panel_sizes": {"sidebar_width": 320},
    "snippet_categories_expanded": {}
  },
  "last_modified": "2025-11-30T00:00:00Z"
}
```

---

## 12. Design Clarifications & Resolutions

This section documents design questions that were raised during spec review and their resolutions.

### 12.1 Agent Execution Model - **RESOLVED**

**Clarified**: Agents work like Claude Code's Task tool. They are spawned during execution via a built-in `Task` tool that the model calls. See Section 3.5 for full specification.

### 12.2 Skill Execution Model - **RESOLVED**

**Clarified**: Skills are instructional markdown files (not executable code) that get loaded into the agent's system prompt with caching. They teach the model how to use tools to accomplish complex workflows. See updated Section 3.4.

### 12.3 Permission Mode - **RESOLVED**

**Clarified**: Removed `permissionMode` entirely. All tools execute with full permissions (no sandboxing). This is a power-user tool.

### 12.4 Test Tool Execution - **CLARIFIED**

**Resolution**: `tool_behavior: "execute"` is intentionally for manual testing only. Users are responsible for side effects. This allows verification that tools return reasonable data. Not for automated testing.

### 12.5 Tool Result ID Linking - **RESOLVED**

**Clarified**: Message Editor shows dropdown of available tool_use IDs from previous messages, with context (e.g., "toolu_123 (Read - src/app.py)"). See updated Section 5.9.

### 12.6 Validation Strategy - **RESOLVED**

**Clarified**: Saving never fails. Validation is informational only. If JSON decode fails, show Raw JSON Editor (Section 5.12) where user can fix manually. Invalid sessions can always be saved.

### 12.7 Package Dependencies - **RESOLVED**

**Clarified**: Added `requirements.txt` support and Package Config feature (Section 5.11). CLI checks dependencies on startup and reports missing packages. See updated Section 6.3.1.

### 12.8 CLI Agent Flag - **RESOLVED**

**Clarified**: Removed `--agent` flag entirely. CLI loads `current_session.json` as-is. Agents are spawned dynamically via Task tool during execution.

---

## 13. Glossary

- **Agent**: A specialized AI configuration spawned via the Task tool during execution. Has specific tools, skills, and system prompt. Works like Claude Code's subagents.
- **Skill**: Instructional markdown file loaded into an agent's system prompt (with caching). Teaches the model how to use tools to accomplish complex workflows. Not executable code.
- **Tool**: Functions callable by the AI model following Anthropic SDK conventions. Can be JSON schemas (non-executable) or Python implementations.
- **Task Tool**: Built-in tool (Section 3.5) that enables spawning agents dynamically. Automatically included in every session.
- **Snippet**: Reusable markdown text block that can be dragged into system prompts or messages
- **Session**: Complete Anthropic API request (model, system, tools, messages) stored as current_session.json
- **Project**: Container for all related agents, tools, skills, snippets, sessions, and configuration
- **Package Config**: Settings for how a project behaves when exported/distributed (API key strategy, dependencies)
- **Simulation**: Mock API responses for testing without consuming tokens (based on tests/config.json)

---

