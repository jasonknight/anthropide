# Skills in the Claude Agent SDK

## Table of Contents
1. [What Are Skills?](#what-are-skills)
2. [How Skills Are Stored and Defined](#how-skills-are-stored-and-defined)
3. [Skill Lifecycle](#skill-lifecycle)
4. [How Skills Are Exposed to the Model](#how-skills-are-exposed-to-the-model)
5. [How the Model Calls Skills](#how-the-model-calls-skills)
6. [How Python Code in Skills Works](#how-python-code-in-skills-works)
7. [API Request/Response Examples](#api-requestresponse-examples)
8. [Best Practices](#best-practices)

---

## What Are Skills?

**Skills are modular capabilities that extend Claude's functionality in Claude Code.** Each skill consists of a `SKILL.md` file containing instructions that Claude autonomously reads when relevant, plus optional supporting resources.

### Key Characteristics

- **Model-Invoked**: Claude decides when to use skills based on context (unlike slash commands which are explicitly triggered by users)
- **Autonomous**: Claude automatically evaluates relevance and loads skills as needed
- **Procedural Guidance**: Skills provide instructions and guidance rather than being explicitly callable functions
- **Context-Aware**: Activated dynamically based on task requirements

### Purpose

Skills enable:
- Extension of Claude's capabilities with specialized knowledge
- Reusable, organized functionality across projects
- Dynamic discovery and activation based on task relevance
- Complex logic requiring tool permissions and multi-file organization

### Skills vs Tools vs Slash Commands

| Aspect | Skills | Tools | Slash Commands |
|--------|--------|-------|----------------|
| **Invocation** | Auto-activated by relevance | Explicitly called with `tool_use` | Explicitly triggered by user |
| **Nature** | Procedural guidance | Executable functions | Text expansion |
| **Complexity** | Can be multi-file, complex | Single function | Single file, simple |
| **Discovery** | Description-based matching | Always available in tools array | User-typed command |
| **Examples** | PDF processing, commit formatting | Read, Write, Bash | /help, /clear |

---

## How Skills Are Stored and Defined

### Storage Locations

Skills live in three possible locations with different scopes:

```
1. Personal Skills
   Location: ~/.claude/skills/
   Scope: Available across all projects for individual workflows
   Usage: Private skills for personal use

2. Project Skills
   Location: .claude/skills/
   Scope: Team-shared skills checked into version control
   Usage: Team-accessible skills for specific projects

3. Plugin Skills
   Location: Bundled with installed Claude Code plugins
   Scope: Distributed with plugins
   Usage: Plugin-provided capabilities
```

### Directory Structure

#### Simple Skill (Single File)

```
project/
└── .claude/
    └── skills/
        └── commit-formatter/
            └── SKILL.md
```

#### Complex Skill (Multi-File)

```
project/
└── .claude/
    └── skills/
        └── pdf-processing/
            ├── SKILL.md                # Main skill file
            ├── FORMS.md                # Detailed guidance
            ├── REFERENCE.md            # Reference materials
            └── scripts/                # Helper utilities
                ├── extract_text.py
                └── process_images.py
```

### SKILL.md File Structure

Each skill requires a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: lowercase-with-hyphens
description: what it does and when to use it (max 1024 characters)
---

Your skill instructions go here...
```

### Frontmatter Fields

| Field | Type | Max Length | Required | Purpose |
|-------|------|-----------|----------|---------|
| `name` | String | 64 characters | Yes | Unique identifier for the skill |
| `description` | String | 1024 characters | Yes | Describes functionality and activation triggers |
| `allowed-tools` | String | - | No | Restricts available tools (comma-separated) |

### Example: Simple Skill

**File: `.claude/skills/commit-formatter/SKILL.md`**

```yaml
---
name: commit-message-formatter
description: Helps write clear, well-structured git commit messages following conventional commits format. Use this skill whenever you're preparing commits.
---

You are an expert at crafting clear, descriptive git commit messages that follow conventional commits standards.

## Guidelines

1. **Format**: `<type>(<scope>): <subject>`
2. **Types**: feat, fix, docs, style, refactor, test, chore
3. **Subject**: Imperative mood, lowercase, no period
4. **Body**: Explain what and why, not how

## Examples

### Good Commit
```
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh to improve session continuity.
Users will now receive new tokens before expiration, reducing
re-authentication requirements.
```

### Bad Commit
```
fixed stuff
```

## Process

When asked to write a commit message:
1. Use Bash to run `git status` and `git diff` to understand changes
2. Identify the primary change type (feat, fix, etc.)
3. Determine the affected scope
4. Write a clear subject line
5. Add a body explaining the "why" if the change is non-trivial
```

### Example: Restricted Tool Access

**File: `.claude/skills/readonly-auditor/SKILL.md`**

```yaml
---
name: readonly-auditor
description: Performs read-only security audits of codebases without making modifications
allowed-tools: Read, Bash(find:*), Bash(grep:*), Grep, Glob
---

You are a security auditor performing read-only analysis of code.

## Constraints

- You CANNOT modify any files (Write tool is not available)
- You CANNOT execute potentially harmful commands
- Focus on identifying security issues through reading and analysis

## Process

1. Use Glob and Grep to find potentially vulnerable code patterns
2. Use Read to examine suspicious files in detail
3. Document findings with specific file paths and line numbers
4. Provide remediation recommendations
```

---

## Skill Lifecycle

### Phase 1: Discovery

```
1. Startup Scan
   → CLI scans .claude/skills/, ~/.claude/skills/, and plugin directories
   → Finds all SKILL.md files

2. Metadata Extraction
   → Reads YAML frontmatter from each skill
   → Extracts name and description

3. Indexing
   → Builds internal skill registry
   → Makes skills available for activation
```

### Phase 2: Activation

```
1. Context Evaluation
   → Model reads user request and project context
   → Considers available skills based on descriptions

2. Relevance Matching
   → Model determines if any skill's description matches the task
   → Skill description is the primary discovery mechanism

3. Auto-Activation
   → If relevant, Claude autonomously reads the full SKILL.md
   → Skill instructions are incorporated into Claude's context
```

**Example:**
```
User: "Write a commit message for my authentication changes"
     ↓
Claude evaluates available skills
     ↓
Skill "commit-message-formatter" description matches
     ↓
Full SKILL.md content is loaded into system context
     ↓
Claude follows skill's guidelines
```

### Phase 3: Execution

```
1. Instruction Integration
   → Full SKILL.md content is added to Claude's system context
   → Supporting files are made available if referenced

2. Tool Execution
   → Claude uses available tools within skill's constraints
   → If allowed-tools specified, only those tools are accessible

3. Completion
   → Skill-guided work proceeds until task is complete
```

### Discovery Verification

You can query available skills:

```bash
# Ask Claude directly
user: "What skills are available?"
claude: [Lists all discovered skills with their descriptions]
```

---

## How Skills Are Exposed to the Model

**Skills are not directly included in API requests as separate entities.** Instead, they're discovered and loaded dynamically by Claude Code during runtime.

### The Loading Mechanism

1. **CLI Startup**: Skill metadata is cached in memory
2. **User Request**: Sent to Claude in a standard messages API call
3. **Model Processing**: Claude evaluates if any skill is relevant
4. **Dynamic Loading**: Relevant skills' full SKILL.md content is incorporated
5. **API Call with Context**: Skills become part of the system prompt

### System Context Integration

When a skill is relevant, its content is injected into the system message:

```json
{
  "system": "You are Claude Code...\n\n## Active Skills\n\n[Full SKILL.md content]\n\n..."
}
```

**Key Insight**: Skills are not special API constructs—they're simply text added to the system context that guides Claude's behavior.

### Agent-Loaded Skills

Agents can explicitly load skills via frontmatter:

**File: `.claude/agents/backend-python-tester.md`**
```yaml
---
name: backend-python-tester
description: Creates tests for Python backend code
model: inherit
skills: python-testing, code-review
---

You are an elite Python testing specialist...
```

When this agent is spawned, the specified skills are automatically loaded into its system context.

---

## How the Model Calls Skills

**The model does NOT explicitly "call" skills.** This is a crucial distinction.

### Skills Are Not Tools

- **Tools**: Explicitly invoked with `tool_use` blocks (e.g., Read, Write, Bash)
- **Skills**: Implicitly guide behavior through system context

### How It Works

```
┌─────────────────────────────────────────┐
│ User Request                            │
│ "Format a commit message"               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Claude Evaluates Available Skills       │
│ - Reads skill descriptions              │
│ - Matches against user request          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Skill Context Loaded                    │
│ - Full SKILL.md added to system message │
│ - Instructions guide Claude's behavior  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Claude Follows Skill Instructions       │
│ - Uses tools as skill directs           │
│ - Applies skill guidelines              │
│ - Produces skill-guided output          │
└─────────────────────────────────────────┘
```

### Example Flow

**User Input:**
```
"Review this Python code for security issues"
```

**Internal Process:**
1. Claude sees "security issues" + "Python code"
2. Skill description matches: "security-auditor: Reviews code for security vulnerabilities"
3. SKILL.md content is loaded into system context
4. Claude follows skill's checklist and methodology
5. Claude uses tools (Read, Grep) as skill directs
6. Output is formatted per skill's guidance

**No explicit skill invocation occurs**—it's all instruction following.

---

## How Python Code in Skills Works

A common question: **How does Claude actually use Python scripts in complex skills?** The answer is simpler than you might think.

### The Critical Truth: No Special API

**There is NO special execution API or context for Python code in skills.** Python scripts in skill directories are just regular files that Claude executes using the standard **Bash tool**.

### The Execution Model

```
┌─────────────────────────────────────────┐
│ User: "Extract text from report.pdf"    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Skill Description Matches               │
│ "pdf-processor: Extracts text from PDFs"│
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ SKILL.md Loaded into System Context     │
│ Contains: "Run python scripts/extract..." │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Claude Reads SKILL.md Instructions      │
│ "I need to run that Python script"     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Claude Uses Bash Tool                   │
│ tool_use: Bash                          │
│ command: "python scripts/extract..."    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Script Executes in Your Environment     │
│ Just like running from terminal         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Claude Captures Output                  │
│ Continues per SKILL.md guidance         │
└─────────────────────────────────────────┘
```

### Complete Example: PDF Text Extractor

Let's walk through a complete example to see exactly how this works.

#### File Structure

```
.claude/skills/pdf-processor/
├── SKILL.md
└── scripts/
    └── extract_text.py
```

#### SKILL.md

```yaml
---
name: pdf-processor
description: Extracts text from PDF files using Python utilities. Use when working with PDF documents that need text extraction.
---

## Requirements

This skill requires the pdfplumber package:
```bash
pip install pdfplumber
```

## Process

When extracting text from a PDF:

1. First check if pdfplumber is installed
2. Run: `python .claude/skills/pdf-processor/scripts/extract_text.py <pdf_file>`
3. The script outputs extracted text to stdout
4. Use that output for analysis, or save it to a file with Write tool

## Usage Example

```bash
python scripts/extract_text.py report.pdf
```

## Error Handling

If you get "ModuleNotFoundError: No module named 'pdfplumber'":
- Ask user for permission to install: `pip install pdfplumber`
- Retry after installation
```

#### scripts/extract_text.py

```python
#!/usr/bin/env python3
"""
Simple PDF text extraction utility for the pdf-processor skill.
"""
import sys
import pdfplumber

def extract_text(pdf_path):
    """Extract all text from a PDF file."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    return text.strip()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: extract_text.py <pdf_file>", file=sys.stderr)
        sys.exit(1)

    try:
        result = extract_text(sys.argv[1])
        print(result)
    except FileNotFoundError:
        print(f"Error: File '{sys.argv[1]}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error extracting text: {e}", file=sys.stderr)
        sys.exit(1)
```

### What Happens When User Asks: "Extract text from report.pdf"

#### Step 1: Skill Discovery
Claude evaluates available skill descriptions and matches "pdf-processor" because the description says "Extracts text from PDF files".

#### Step 2: SKILL.md Loaded
The full SKILL.md content is added to Claude's system context:

```json
{
  "system": "You are Claude Code...\n\n## Active Skills\n\n### pdf-processor\n\n[Full SKILL.md content here]\n\n..."
}
```

#### Step 3: Claude Reads Instructions
Claude processes the SKILL.md and understands:
- Need to run `python .claude/skills/pdf-processor/scripts/extract_text.py <pdf_file>`
- Check if dependencies are installed first
- Capture stdout output for the extracted text

#### Step 4: Claude Makes API Call with Bash Tool

```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll extract text from the PDF using the pdf-processor skill."
    },
    {
      "type": "tool_use",
      "id": "toolu_01",
      "name": "Bash",
      "input": {
        "command": "python .claude/skills/pdf-processor/scripts/extract_text.py report.pdf",
        "description": "Extract text from PDF file"
      }
    }
  ]
}
```

#### Step 5: Script Execution
The Python script runs in your normal environment:
- Uses your Python interpreter
- Accesses your installed packages
- Reads files from your filesystem
- Outputs to stdout/stderr like any command-line tool

#### Step 6: Output Processing
Claude receives the script output and continues according to SKILL.md guidance:
```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01",
      "content": "Chapter 1: Introduction\n\nThis report covers...\n\n[extracted text]"
    }
  ]
}
```

Claude then processes this output (analyze it, save to file, etc.) based on what the user requested.

### Key Insights

1. **Scripts Are Just Normal Executables**
   - They run in your environment with your Python, packages, and filesystem
   - No special runtime or sandbox
   - Same as typing `python scripts/extract_text.py` in your terminal

2. **SKILL.md Provides Instructions, Not Magic**
   - It tells Claude *how* to use the scripts
   - It doesn't provide special execution powers
   - It's documentation that Claude follows

3. **Bash Tool Is the Bridge**
   - Claude can't directly execute Python
   - Claude uses the Bash tool to run commands
   - The skill just organizes and documents this pattern

4. **Dependencies Must Pre-Exist**
   - Python packages must be installed in your environment
   - Claude may ask permission to run `pip install`
   - No automatic dependency resolution

5. **Standard Input/Output**
   - Scripts communicate via stdout/stderr
   - Exit codes indicate success/failure
   - Command-line arguments pass parameters

### Why Include Python Scripts in Skills?

The benefit is **organization and automatic discovery**:

| Benefit | Explanation |
|---------|-------------|
| **Co-location** | Keep utilities with their documentation |
| **Context** | SKILL.md explains when/how to use scripts |
| **Discovery** | Claude finds them automatically when relevant |
| **Reusability** | Share complete workflows with teams |
| **Guidance** | Instructions ensure correct usage patterns |

### Comparison: With vs Without Skills

#### Without Skills (Manual Approach)
```
user: "Extract text from report.pdf using Python"
claude: "I'll need to write a script..."
[Writes extract_text.py from scratch every time]
[User must explain requirements each time]
```

#### With Skills (Organized Approach)
```
user: "Extract text from report.pdf"
claude: [Automatically discovers pdf-processor skill]
claude: [Reads SKILL.md instructions]
claude: [Uses pre-written, tested script]
claude: [Follows documented best practices]
```

### Environment Considerations

#### Local Development
- Scripts run with your local Python interpreter
- Use your local packages and environment variables
- Access your local filesystem

#### Claude Code on the Web (Cloud)
- Scripts run in a cloud sandbox environment
- Python 3.x with pip and poetry pre-installed
- Use SessionStart hooks in `.claude/settings.json` to install dependencies:
  ```json
  {
    "hooks": {
      "SessionStart": "pip install -r requirements.txt"
    }
  }
  ```

### Best Practices for Skill Python Scripts

1. **Make Scripts Standalone**
   ```python
   # Good: Clear usage, proper error handling
   if __name__ == "__main__":
       if len(sys.argv) < 2:
           print("Usage: script.py <input>", file=sys.stderr)
           sys.exit(1)
   ```

2. **Document Dependencies in SKILL.md**
   ```yaml
   ## Requirements
   - pdfplumber: `pip install pdfplumber`
   - pypdf: `pip install pypdf`
   ```

3. **Use Command-Line Arguments**
   ```python
   # Good: Configurable via CLI
   import argparse
   parser = argparse.ArgumentParser()
   parser.add_argument('--input', required=True)
   ```

4. **Provide Clear Output**
   ```python
   # Output results to stdout
   print(result)

   # Errors to stderr
   print(f"Error: {message}", file=sys.stderr)
   ```

5. **Include Error Handling**
   ```python
   try:
       result = process_file(path)
   except FileNotFoundError:
       print(f"File not found: {path}", file=sys.stderr)
       sys.exit(1)
   ```

6. **Make Scripts Executable**
   ```bash
   chmod +x .claude/skills/my-skill/scripts/*.py
   ```

### Summary: The Execution Model

| Question | Answer |
|----------|--------|
| Is there a special API? | No - uses standard Bash tool |
| How are scripts executed? | Via `Bash` tool, like terminal commands |
| Where do scripts run? | In your normal environment (local or cloud) |
| How does Claude know to use them? | SKILL.md provides instructions |
| Are dependencies auto-installed? | No - must exist or be installed via pip |
| Can scripts use any Python package? | Yes, if installed in your environment |

**Bottom line**: Python scripts in skills are just regular command-line utilities. The skill framework provides organization, documentation, and automatic discovery—but execution happens through standard tool invocation, not special magic.

---

## API Request/Response Examples

### Example 1: Without Active Skills

**Request:**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are Claude Code, an AI assistant helping with coding tasks.",
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file from the filesystem",
      "input_schema": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "Absolute path to the file"
          }
        },
        "required": ["file_path"]
      }
    },
    {
      "name": "Write",
      "description": "Writes content to a file",
      "input_schema": {
        "type": "object",
        "properties": {
          "file_path": { "type": "string" },
          "content": { "type": "string" }
        },
        "required": ["file_path", "content"]
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "Create a Python function to sort a list"
    }
  ]
}
```

**Response:**
```json
{
  "id": "msg_123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Here's a Python function to sort a list:\n\n```python\ndef sort_list(items):\n    return sorted(items)\n```\n\nThis function uses Python's built-in sorted() function."
    }
  ],
  "stop_reason": "end_turn"
}
```

---

### Example 2: With Active Skills

When the commit-message-formatter skill is relevant:

**Request:**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are Claude Code, an AI assistant helping with coding tasks.\n\n## Active Skills\n\n### commit-message-formatter\n\n---\nname: commit-message-formatter\ndescription: Helps write clear, well-structured git commit messages\n---\n\nYou are an expert at crafting clear, descriptive git commit messages that follow conventional commits standards.\n\nGuidelines:\n1. Use format: <type>(<scope>): <subject>\n2. Types: feat, fix, docs, style, refactor, test, chore\n3. Subject: imperative mood, lowercase, no period\n4. Body: explain what and why, not how\n5. Example:\n   \n   feat(auth): add JWT token refresh mechanism\n   \n   Implement automatic token refresh to improve session continuity.\n   Users will now receive new tokens before expiration, reducing\n   re-authentication requirements.",
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file from the filesystem",
      "input_schema": { "type": "object", "properties": { "..." } }
    },
    {
      "name": "Write",
      "description": "Writes content to a file",
      "input_schema": { "type": "object", "properties": { "..." } }
    },
    {
      "name": "Bash",
      "description": "Executes bash commands",
      "input_schema": { "type": "object", "properties": { "..." } }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "I've added JWT token refresh support to the auth system. Write me a commit message for this change."
    }
  ]
}
```

**Response:**
```json
{
  "id": "msg_456",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Based on the commit-message-formatter skill, here's your commit message:\n\n```\nfeat(auth): add JWT token refresh mechanism\n\nImplement automatic token refresh to improve session continuity.\nUsers will now receive new tokens before expiration, reducing\nre-authentication requirements and improving overall UX.\n```\n\nThis follows conventional commits format with:\n- **Type**: feat (new feature)\n- **Scope**: auth (affected system)\n- **Subject**: Clear, imperative mood, lowercase\n- **Body**: Explains the 'why' behind the change"
    }
  ],
  "stop_reason": "end_turn"
}
```

**Notice**: The skill's content is in the `system` field, and Claude follows it naturally without explicit invocation.

---

### Example 3: Skill Guides Tool Usage

A skill that directs Claude to use tools:

**Request:**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are Claude Code...\n\n## Active Skills\n\n### security-auditor\n\n---\nname: security-auditor\ndescription: Performs comprehensive security audits\n---\n\nWhen performing a security audit:\n\n1. Use Grep to search for common vulnerabilities:\n   - SQL injection: grep for raw SQL queries\n   - XSS: grep for innerHTML, dangerouslySetInnerHTML\n   - Command injection: grep for exec, shell_exec, system\n\n2. Use Read to examine suspicious files\n\n3. Document findings with:\n   - File path and line number\n   - Vulnerability type\n   - Severity (Critical, High, Medium, Low)\n   - Remediation recommendation",
  "tools": [
    { "name": "Read", "..." },
    { "name": "Grep", "..." },
    { "name": "Bash", "..." }
  ],
  "messages": [
    {
      "role": "user",
      "content": "Audit the authentication module for security issues"
    }
  ]
}
```

**Response:**
```json
{
  "id": "msg_789",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll perform a security audit of the authentication module following the security-auditor skill's methodology."
    },
    {
      "type": "tool_use",
      "id": "toolu_01",
      "name": "Grep",
      "input": {
        "pattern": "exec\\(|shell_exec|system\\(",
        "path": "src/auth",
        "output_mode": "content"
      }
    },
    {
      "type": "tool_use",
      "id": "toolu_02",
      "name": "Grep",
      "input": {
        "pattern": "SELECT.*\\+|query\\(.*\\+",
        "path": "src/auth",
        "output_mode": "content"
      }
    }
  ],
  "stop_reason": "tool_use"
}
```

**Notice**: Claude uses tools (Grep) as directed by the skill's instructions. The skill guides the process, but Claude uses standard tool invocation.

---

### Example 4: Agent with Pre-Loaded Skills

When spawning an agent with skills specified in frontmatter:

**Agent Definition:**
```yaml
---
name: backend-python-tester
description: Creates tests for Python backend code
model: inherit
skills: python-testing, pytest-patterns
---

You are an elite Python testing specialist...
```

**Request (when agent is spawned):**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8000,
  "system": "You are an elite Python testing specialist...\n\n## Loaded Skills\n\n### python-testing\n\n[Full content of .claude/skills/python-testing/SKILL.md]\n\n### pytest-patterns\n\n[Full content of .claude/skills/pytest-patterns/SKILL.md]",
  "tools": [
    { "name": "Read", "..." },
    { "name": "Write", "..." },
    { "name": "Bash", "..." }
  ],
  "messages": [
    {
      "role": "user",
      "content": "Create comprehensive tests for src/api/users.py"
    }
  ]
}
```

**Key Point**: The agent's specified skills are automatically loaded into the system context when the agent is spawned.

---

## Best Practices

### 1. Write Clear, Specific Descriptions

The description is the **primary discovery mechanism**. Make it:
- Clear about what the skill does
- Explicit about when to use it
- Keyword-rich for matching

**Good:**
```yaml
description: Helps write clear, well-structured git commit messages following conventional commits format. Use this skill whenever you're preparing commits or reviewing commit history.
```

**Bad:**
```yaml
description: Commit helper
```

### 2. Keep Skills Focused

Each skill should handle a specific domain:

**Good Structure:**
- `commit-formatter/` - Formats commit messages
- `code-reviewer/` - Reviews code for quality
- `security-auditor/` - Audits for vulnerabilities

**Bad Structure:**
- `general-helper/` - Does everything (too broad)

### 3. Use Supporting Files for Complex Skills

For complex domains, organize into multiple files:

```
.claude/skills/pdf-processor/
├── SKILL.md              # Main entry point
├── extraction.md         # Text extraction guidance
├── forms.md              # Form processing
└── scripts/
    └── helpers.py        # Utility scripts
```

Reference supporting files in SKILL.md:
```markdown
For detailed form processing guidance, see FORMS.md.
For text extraction, see EXTRACTION.md.
```

### 4. Include Concrete Examples

Provide examples in your SKILL.md:

```yaml
---
name: api-endpoint-designer
description: Designs RESTful API endpoints following best practices
---

## Example Endpoint Design

### Good Design
```
GET /api/v1/users/{id}
POST /api/v1/users
PUT /api/v1/users/{id}
DELETE /api/v1/users/{id}
```

### Bad Design
```
GET /api/getUser?id=123
POST /api/createUser
```
```

### 5. Use Tool Restrictions When Appropriate

For security-sensitive or read-only skills:

```yaml
---
name: readonly-auditor
description: Performs read-only security audits
allowed-tools: Read, Grep, Glob, Bash(find:*), Bash(grep:*)
---
```

This prevents accidental modifications during audits.

### 6. Version Control Project Skills

Keep team-shared skills in `.claude/skills/` and commit to git:

```bash
# .gitignore
# Don't ignore project skills
!.claude/skills/

# Do ignore personal skills
.claude/local/
```

### 7. Document the Process

Include step-by-step processes in your skills:

```markdown
## Process

When designing a new API endpoint:
1. Use Grep to find similar existing endpoints
2. Use Read to examine their implementation
3. Identify the resource and operations needed
4. Design URL structure following RESTful conventions
5. Define request/response schemas
6. Document with OpenAPI/Swagger format
```

### 8. Test Your Skills

After creating a skill:
1. Ask Claude: "What skills are available?" (verify it's discovered)
2. Create a test scenario that should trigger it
3. Verify the skill is loaded and followed
4. Iterate on the description if matching fails

### 9. Namespace Personal vs Project Skills

**Personal** (`~/.claude/skills/`): Your personal workflow preferences
**Project** (`.claude/skills/`): Team-shared, project-specific practices

Example:
```
~/.claude/skills/my-commit-style/     # Your personal commit style
.claude/skills/team-commit-style/     # Team's agreed conventions
```

### 10. Keep Skills Maintainable

- Update skills as practices evolve
- Remove obsolete skills
- Document the purpose and last update in comments
- Review skills during code reviews

---

## Summary

### Key Takeaways

1. **Skills are procedural guidance**, not callable functions
2. **Discovery happens through descriptions** - make them clear and keyword-rich
3. **Loading is automatic** - Claude evaluates relevance and loads as needed
4. **Skills guide tool usage** - they don't replace tools, they direct how to use them
5. **Skills live in system context** - they're text added to the system message
6. **Agents can pre-load skills** - via frontmatter `skills` field
7. **Tool restrictions are optional** - use `allowed-tools` for security

### Quick Reference

```yaml
# Basic SKILL.md template
---
name: my-skill-name
description: Clear description of what it does and when to use it
---

Detailed instructions here...

## Process
1. Step one
2. Step two

## Examples
[Concrete examples]
```

### File Paths

```
# Personal skills
~/.claude/skills/skill-name/SKILL.md

# Project skills
.claude/skills/skill-name/SKILL.md

# Agent definitions
.claude/agents/agent-name.md
```

---

For more information, see the [Claude Code documentation](https://docs.claudecode.com).
