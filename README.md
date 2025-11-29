# AnthropIDE - TUI IDE for Anthropic Models

A Terminal User Interface IDE built with Textual for managing AI conversation sessions with Anthropic's Claude models.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [UI Architecture](#ui-architecture)
- [UI Layout Diagrams](#ui-layout-diagrams)
- [Code Structure](#code-structure)
- [Common Customizations](#common-customizations)
- [Data Flow](#data-flow)
- [File Format](#file-format)

## Overview

AnthropIDE provides a project-based interface for:
- Managing system prompts with caching control
- Defining and configuring tools
- Building message chains for AI conversations
- Organizing context files (environments, explorations, plans, snippets)
- Configuring API settings (model, max tokens)

**Key Features:**
- Pure Textual-native architecture (no React-style patterns)
- Direct data updates with simple rebuilds
- Clean separation of data, widgets, and screens
- JSON-based session persistence with automatic backups

## Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application (DO NOT run in Claude Code CLI!)
python anthropide.py
```

**Important:** This is a TUI application that requires its own terminal window. Do not run it as a child process or in the Claude Code CLI.

## UI Architecture

### Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DATA MODEL LAYER (Lines 36-318)                         │
│    Pure Python dataclasses, no UI dependencies             │
│    - Session, Project, Message, SystemBlock, Tool, etc.    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. WIDGET COMPONENTS (Lines 365-579)                       │
│    Dumb views that display data and emit events            │
│    - MessageWidget, SystemBlockWidget, ToolWidget, etc.    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CONTAINER WIDGETS (Lines 584-732)                       │
│    Smart containers that manage lists of widgets           │
│    - MessageList, SystemBlockList, ToolList, etc.          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. SCREENS (Lines 749-1173)                                │
│    Orchestrators that own data and handle events           │
│    - ProjectSelectScreen, MainScreen, CreateFileModal      │
└─────────────────────────────────────────────────────────────┘
```

## UI Layout Diagrams

### Main Screen Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header (Textual built-in)                                                   │
├──────────────────────────┬──────────────────────────────────────────────────┤
│                          │                                                  │
│  ContextFileList         │  #editor (VerticalScroll) ← MAIN SCROLLABLE     │
│  (30% width)             │  (70% width)                                     │
│  ├─ "Context Files"      │  ├─ #api-config (Container)                     │
│  ├─ "+ New File" button  │  │  ├─ "API Configuration" header               │
│  │                       │  │  ├─ Model: [Select dropdown]                 │
│  ├─ "Snippets"           │  │  └─ Max Tokens: [Input field]                │
│  │  └─ [Checkboxes...]   │  │                                               │
│  ├─ "Environments"       │  ├─ SystemBlockList (VerticalScroll)            │
│  │  └─ [Checkboxes...]   │  │  ├─ "System Prompt" + "+ Add Block"          │
│  ├─ "Explorations"       │  │  └─ SystemBlockWidget (foreach block)        │
│  │  └─ [Checkboxes...]   │  │     ├─ Collapsible(title, collapsed=False)   │
│  └─ "Plans"              │  │     ├─ [↑] [↓] [Delete] buttons              │
│     └─ [Checkboxes...]   │  │     ├─ "Enable caching" checkbox             │
│                          │  │     └─ TextArea (markdown)                   │
│                          │  │                                               │
│  ContextFileWidget:      │  ├─ ToolList (VerticalScroll)                   │
│  └─ Checkbox with        │  │  ├─ "Tools" + "+ Add Tool"                   │
│     file name and        │  │  └─ ToolWidget (foreach tool)                │
│     token count          │  │     ├─ Collapsible("Tool: {name}")           │
│                          │  │     ├─ [Delete] button                       │
│                          │  │     ├─ Name: [Input]                         │
│                          │  │     ├─ Description: [Input]                  │
│                          │  │     └─ Input Schema: [TextArea(json)]        │
│                          │  │                                               │
│                          │  ├─ SelectedContextsList (Vertical)             │
│                          │  │  ├─ "Selected Context Files" header          │
│                          │  │  └─ SelectedContextWidget (foreach context)  │
│                          │  │     └─ [section] filename (tokens) [✕]       │
│                          │  │                                               │
│                          │  └─ #messages-section (Vertical)                │
│                          │     ├─ "Messages" + [New Session] + [+ Add]     │
│                          │     └─ MessageList (VerticalScroll)             │
│                          │        └─ MessageWidget (foreach message)       │
│                          │           ├─ Collapsible(role + preview)        │
│                          │           ├─ Role: [Select] [↑] [↓] [Delete]    │
│                          │           └─ TextArea (markdown)                │
│                          │                                                  │
├──────────────────────────┴──────────────────────────────────────────────────┤
│ Footer (Textual built-in) - Shows key bindings                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Widget Hierarchy Tree

```
MainScreen
├─ Header
├─ Horizontal#main-container
│  ├─ ContextFileList (VerticalScroll, 30%)
│  │  ├─ Vertical.header-row
│  │  │  ├─ Label "Context Files"
│  │  │  └─ Button "+ New File"
│  │  └─ For each section:
│  │     ├─ Label (section name)
│  │     └─ ContextFileWidget * n
│  │        └─ Checkbox (file + token count)
│  │
│  └─ VerticalScroll#editor (70%)  ← MAIN SCROLLABLE AREA
│     ├─ Container#api-config
│     │  ├─ Label "API Configuration"
│     │  ├─ Horizontal.api-config-row
│     │  │  ├─ Label "Model:"
│     │  │  └─ Select#model-select
│     │  └─ Horizontal.api-config-row
│     │     ├─ Label "Max Tokens:"
│     │     └─ Input#max-tokens-input
│     │
│     ├─ SystemBlockList (VerticalScroll)
│     │  ├─ Horizontal.section-header-row
│     │  │  ├─ Label "System Prompt"
│     │  │  └─ Button "+ Add Block"
│     │  └─ SystemBlockWidget * n
│     │     └─ Collapsible
│     │        ├─ Horizontal.block-header
│     │        │  ├─ Label "System Block N"
│     │        │  ├─ Checkbox "Enable caching"
│     │        │  ├─ Button "↑"
│     │        │  ├─ Button "↓"
│     │        │  └─ Button "Delete"
│     │        └─ TextArea (markdown)
│     │
│     ├─ ToolList (VerticalScroll)
│     │  ├─ Horizontal.section-header-row
│     │  │  ├─ Label "Tools"
│     │  │  └─ Button "+ Add Tool"
│     │  └─ ToolWidget * n
│     │     └─ Collapsible
│     │        ├─ Horizontal.tool-header
│     │        │  ├─ Label "Tool: {name}"
│     │        │  └─ Button "Delete"
│     │        ├─ Label "Name:"
│     │        ├─ Input (tool name)
│     │        ├─ Label "Description:"
│     │        ├─ Input (description)
│     │        ├─ Label "Input Schema (JSON):"
│     │        └─ TextArea (json)
│     │
│     ├─ SelectedContextsList (Vertical)
│     │  ├─ Horizontal.contexts-header-row
│     │  │  └─ Label "Selected Context Files"
│     │  └─ SelectedContextWidget * n
│     │     └─ Horizontal
│     │        ├─ Label "[section] file (tokens)"
│     │        └─ Button "✕"
│     │
│     └─ Vertical#messages-section
│        ├─ Horizontal.messages-header
│        │  ├─ Label "Messages"
│        │  ├─ Button "New Session"
│        │  └─ Button "+ Add Message"
│        └─ MessageList (VerticalScroll)
│           └─ MessageWidget * n
│              └─ Collapsible
│                 ├─ Horizontal.message-header
│                 │  ├─ Select (role)
│                 │  ├─ Button "↑"
│                 │  ├─ Button "↓"
│                 │  └─ Button "Delete"
│                 └─ TextArea (markdown)
│
└─ Footer
```

### Data Model Structure

```
Session (anthropide.py:84-276)
├─ model: str
├─ max_tokens: int
├─ system_blocks: List[SystemBlock]
│  └─ SystemBlock
│     ├─ text: str
│     ├─ cache_control: Optional[Dict]
│     └─ id: str
├─ tools: List[Tool]
│  └─ Tool
│     ├─ name: str
│     ├─ description: str
│     ├─ input_schema: Dict
│     └─ id: str
├─ messages: List[Message]
│  └─ Message
│     ├─ role: str (user|assistant)
│     ├─ content: List[ContentBlock]
│     │  └─ ContentBlock
│     │     ├─ type: str
│     │     └─ text: str
│     └─ id: str
└─ selected_contexts: List[ContextFile]
   └─ ContextFile
      ├─ path: str
      └─ section: str
```

## Code Structure

### File Organization

```
anthropide.py (1,196 lines)
├─ Lines 36-318:   Data Model Layer (dataclasses)
├─ Lines 329-360:  Custom Messages (events)
├─ Lines 365-579:  Widget Components (views)
├─ Lines 584-732:  Container Widgets (lists)
├─ Lines 738-742:  Constants
├─ Lines 749-1173: Screens (orchestrators)
└─ Lines 1179-1196: App & Main

style.css (384 lines)
├─ Lines 1-43:    Base Button Styles
├─ Lines 45-73:   Base Heading Styles
├─ Lines 75-92:   Widget Container Styles
├─ Lines 94-382:  Component-specific Styles
└─ Organized by widget type
```

### Key Classes Reference

| Class | Type | Location | Purpose |
|-------|------|----------|---------|
| `Session` | Data Model | Line 84 | Complete session state |
| `Project` | Data Model | Line 278 | Project management |
| `Message` | Data Model | Line 44 | Single message |
| `SystemBlock` | Data Model | Line 60 | System prompt block |
| `Tool` | Data Model | Line 68 | Tool definition |
| `ContextFile` | Data Model | Line 77 | Context file reference |
| `MessageWidget` | Widget | Line 365 | Displays one message |
| `SystemBlockWidget` | Widget | Line 420 | Displays one system block |
| `ToolWidget` | Widget | Line 473 | Displays one tool |
| `ContextFileWidget` | Widget | Line 524 | Checkbox for context file |
| `SelectedContextWidget` | Widget | Line 551 | Shows selected context |
| `MessageList` | Container | Line 611 | Scrollable message list |
| `SystemBlockList` | Container | Line 632 | Scrollable system blocks |
| `ToolList` | Container | Line 661 | Scrollable tools list |
| `ContextFileList` | Container | Line 690 | Sidebar file browser |
| `SelectedContextsList` | Container | Line 584 | Selected contexts area |
| `MainScreen` | Screen | Line 897 | Main editor screen |
| `ProjectSelectScreen` | Screen | Line 840 | Project selection |
| `CreateFileModal` | Screen | Line 749 | File creation modal |

## Common Customizations

### Changing Widget Styles

#### If you want to change the style of the delete button on the message widget:

**Location:** `style.css` lines 29-35

```css
/* Delete buttons */
.btn-delete {
    height: 1;
    min-height: 1;
    padding: 0 1;
    margin-left: 1;
}
```

**Example modifications:**
```css
/* Make delete button wider */
.btn-delete {
    width: 10;  /* Add fixed width */
    height: 1;
    min-height: 1;
    padding: 0 1;
    margin-left: 1;
}

/* Change delete button color */
/* Use Textual's variant system in Python instead: */
/* Button("Delete", variant="error", ...) */
```

#### If you want to change the message widget border color:

**Location:** `style.css` line 97

```css
MessageWidget {
    border: solid $primary;  /* Change $primary to $warning, $error, etc. */
    padding: 0 1;
    margin: 0;
    height: auto;
}
```

#### If you want to change the TextArea height in messages:

**Location:** `style.css` line 114-117

```css
MessageWidget TextArea {
    height: 10;  /* Change from 10 to desired height */
    margin: 0;
}
```

#### If you want to change the sidebar width:

**Location:** `style.css` line 238

```css
ContextFileList {
    width: 30%;  /* Change percentage (e.g., 40%, 25%) */
    height: 100%;
    border-right: solid $primary;
    padding: 1;
}
```

**And update editor width accordingly:**
**Location:** `style.css` line 347

```css
#editor {
    width: 70%;  /* Must sum to 100% with sidebar */
    height: 100%;
    padding: 1;
    overflow-y: auto;
    scrollbar-size-vertical: 2;
}
```

### Changing Widget Layout

#### If you want to add a new button to the message header:

**Location:** `anthropide.py` lines 381-394 (MessageWidget.compose)

```python
with Horizontal(classes="message-header"):
    yield Select(
        [("user", "user"), ("assistant", "assistant")],
        value=valid_role,
        id=f"role-{self.message.id}",
        classes="role-select",
    )
    if self.index > 0:
        yield Button("↑", id=f"up-{self.message.id}", classes="btn btn-tiny")
    if self.index < self.total - 1:
        yield Button("↓", id=f"down-{self.message.id}", classes="btn btn-tiny")

    # ADD YOUR NEW BUTTON HERE:
    yield Button("Copy", id=f"copy-{self.message.id}", classes="btn btn-small")

    yield Button("Delete", variant="error", id=f"delete-{self.message.id}", classes="btn btn-delete")
```

**Then add handler:**

```python
def on_button_pressed(self, event: Button.Pressed):
    if event.button.id.startswith("delete-"):
        self.post_message(DeleteItem(self.message.id))
        event.stop()
    elif event.button.id.startswith("copy-"):
        # Add copy logic here
        self.post_message(CopyMessage(self.message.id))
        event.stop()
    # ... rest of handlers
```

#### If you want to change the order of sections in the main editor:

**Location:** `anthropide.py` lines 916-951 (MainScreen.compose)

```python
with VerticalScroll(id="editor"):
    # Rearrange these yields to change order:
    yield Container#api-config        # 1. API settings
    yield SystemBlockList             # 2. System prompts
    yield ToolList                    # 3. Tools
    yield SelectedContextsList        # 4. Selected contexts
    yield Vertical#messages-section   # 5. Messages

    # Example: Move messages to top:
    yield Vertical#messages-section   # Now first!
    yield Container#api-config
    # ... etc
```

### Adding New Data Fields

#### If you want to add a "temperature" field to the Session:

**Step 1:** Add to data model (`anthropide.py` line 84)

```python
@dataclass
class Session:
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192
    temperature: float = 1.0  # ADD THIS
    system_blocks: List[SystemBlock] = field(default_factory=list)
    # ... rest of fields
```

**Step 2:** Add to serialization (`anthropide.py` line 94)

```python
def to_anthropic_format(self) -> Dict:
    return {
        "model": self.model,
        "max_tokens": self.max_tokens,
        "temperature": self.temperature,  # ADD THIS
        # ... rest of dict
    }
```

**Step 3:** Add to `from_dict` (`anthropide.py` line 127)

```python
@classmethod
def from_dict(cls, data: Dict) -> 'Session':
    return cls(
        model=data.get("model", "claude-sonnet-4-5-20250929"),
        max_tokens=data.get("max_tokens", 8192),
        temperature=data.get("temperature", 1.0),  # ADD THIS
        # ... rest of fields
    )
```

**Step 4:** Add to `to_dict` (`anthropide.py` line 171)

```python
def to_dict(self) -> Dict:
    return {
        "model": self.model,
        "max_tokens": self.max_tokens,
        "temperature": self.temperature,  # ADD THIS
        # ... rest of dict
    }
```

**Step 5:** Add UI control (`anthropide.py` lines 917-938)

```python
with Horizontal(classes="api-config-row"):
    yield Label("Max Tokens:", classes="api-config-label")
    yield Input(
        value=str(self.session.max_tokens),
        id="max-tokens-input",
        classes="api-config-input",
    )

# ADD THIS:
with Horizontal(classes="api-config-row"):
    yield Label("Temperature:", classes="api-config-label")
    yield Input(
        value=str(self.session.temperature),
        id="temperature-input",
        classes="api-config-input",
    )
```

**Step 6:** Add event handler (`anthropide.py` lines 1076-1083)

```python
def on_input_changed(self, event: Input.Changed):
    if event.input.id == "max-tokens-input":
        try:
            self.session.max_tokens = int(event.value)
            self.save()
        except ValueError:
            pass
    # ADD THIS:
    elif event.input.id == "temperature-input":
        try:
            self.session.temperature = float(event.value)
            self.save()
        except ValueError:
            pass
```

### Changing Colors and Themes

Textual uses CSS variables for theming. Common variables:

```css
/* In your custom CSS or inline in widgets */
$primary    /* Main accent color (blue) */
$secondary  /* Secondary color */
$success    /* Success color (green) */
$warning    /* Warning color (yellow) */
$error      /* Error color (red) */
$accent     /* Accent color */
$text       /* Default text color */
$surface    /* Surface/background color */
$panel      /* Panel background color */
```

**Example:** Change all message widgets to use warning color:

```css
MessageWidget {
    border: solid $warning;  /* Changed from $primary */
    padding: 0 1;
    margin: 0;
    height: auto;
}
```

### Customizing Button Appearance

#### Button Classes

| Class | Purpose | Example |
|-------|---------|---------|
| `.btn` | Base button style | All buttons |
| `.btn-small` | Compact buttons | "+ Add Tool" |
| `.btn-tiny` | Very small buttons | "↑" "↓" arrows |
| `.btn-delete` | Delete buttons | "Delete" buttons |
| `.btn-action` | Action buttons | "✕" remove buttons |

#### Button Variants (in Python)

```python
Button("Label", variant="primary")   # Blue
Button("Label", variant="success")   # Green
Button("Label", variant="warning")   # Yellow
Button("Label", variant="error")     # Red
Button("Label", variant="default")   # Default style
```

## Data Flow

### User Interaction Flow

```
1. User clicks button or edits field
   ↓
2. Widget receives event (on_button_pressed, on_input_changed, etc.)
   ↓
3. Widget posts custom message (DeleteItem, MoveItem, ItemChanged)
   ↓
4. Screen receives custom message (on_delete_item, on_move_item, etc.)
   ↓
5. Screen updates data model directly
   self.session.messages.append(...)
   ↓
6. Screen calls save() and refresh_*()
   self.save_and_refresh_messages()
   ↓
7. Container widget rebuilds
   remove_children() + mount() new widgets
   ↓
8. UI updates automatically
```

### Example: Adding a Message

```python
# User clicks "+ Add Message" button
MainScreen.on_button_pressed()
  ↓
MainScreen.add_message()
  ↓
self.session.messages.append(Message.user_message())
  ↓
self.save_and_refresh_messages()
  ↓
  ├─ self.save()
  │    └─ self.project.save_session(self.session)
  │         └─ session.save(path)  # Write JSON
  │
  └─ self.query_one(MessageList).refresh_messages(self.session)
       ↓
       MessageList.refresh_messages()
         ├─ self.remove_children()
         └─ for message in session.messages:
              self.mount(MessageWidget(message, ...))
                ↓
                UI updates with new message
```

### Custom Message Types

| Message Class | Emitted By | Handled By | Purpose |
|--------------|------------|------------|---------|
| `DeleteItem` | Any widget | MainScreen | Delete item by ID |
| `MoveItem` | MessageWidget, SystemBlockWidget | MainScreen | Move item up/down |
| `ItemChanged` | Any widget | MainScreen | Field value changed |
| `FileCreated` | CreateFileModal | MainScreen | New file created |

## File Format

### Session File Structure

Location: `.anthropide/projects/{project_name}/current_session.json`

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8192,
  "system": [
    {
      "type": "text",
      "text": "You are a helpful AI assistant...",
      "id": "uuid-string",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file from the filesystem",
      "input_schema": {
        "type": "object",
        "properties": { "file_path": { "type": "string" } },
        "required": ["file_path"]
      },
      "id": "uuid-string"
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Hello!"}
      ],
      "id": "uuid-string"
    }
  ],
  "selected_contexts": [
    {
      "path": "/absolute/path/to/file.md",
      "section": "environments"
    }
  ]
}
```

### Directory Structure

```
.anthropide/
└── projects/
    └── {project_name}/
        ├── current_session.json
        ├── current_session.json.20250929_143022  (backups)
        ├── snippets/
        │   └── *.md
        ├── environments/
        │   └── *.md
        ├── explorations/
        │   └── *.md
        └── plans/
            └── *.md
```

## Key Principles

1. **Simple is Better**: Direct data updates beat complex state management patterns
2. **Work with Textual**: Use `compose()`, custom messages, and proper screens
3. **Clear Layers**: Data model → Widgets → Containers → Screens
4. **Easy to Extend**: Add features without touching core architecture
5. **No Magic**: Straightforward code, easy to understand and modify

## Debugging Tips

### Print Current State

```python
# In any screen method:
print(f"Messages: {len(self.session.messages)}")
print(f"System blocks: {len(self.session.system_blocks)}")
print(f"Selected contexts: {self.session.selected_contexts}")
```

### Check Session File

```bash
cat .anthropide/projects/your_project/current_session.json | jq
```

### Add Debug Prints to Event Handlers

```python
def on_button_pressed(self, event: Button.Pressed):
    print(f"Button pressed: {event.button.id}")  # ADD THIS
    if event.button.id == "add-message":
        self.add_message()
```

### Verify Widget Mounting

```python
def refresh_messages(self, session: Session):
    print(f"Refreshing {len(session.messages)} messages")  # ADD THIS
    self.session = session
    self.remove_children()
    for idx, message in enumerate(self.session.messages):
        print(f"Mounting message {idx}: {message.id}")  # ADD THIS
        self.mount(MessageWidget(message, idx, len(self.session.messages)))
```

## Development Commands

```bash
# Activate environment
source .venv/bin/activate

# Check syntax
python -m py_compile anthropide.py

# Run (in separate terminal!)
python anthropide.py

# Format JSON session files
cat .anthropide/projects/*/current_session.json | jq '.' > temp.json
mv temp.json .anthropide/projects/project_name/current_session.json
```

## Contributing

When adding features:

1. **Update Data Model**: Add fields to appropriate dataclass
2. **Update Serialization**: Add to `to_dict()`, `from_dict()`, `to_anthropic_format()`
3. **Create/Update Widget**: Display and edit the new data
4. **Wire Events**: Add event handlers in screen
5. **Style**: Add CSS rules in `style.css`
6. **Test**: Verify save/load works correctly

## Architecture Documentation

For detailed architecture information, see:
- `CLAUDE.md` - Project instructions and architecture overview
- `FRESH_ARCHITECTURE.md` - Complete architecture design document
- `REWRITE_COMPLETE.md` - Rewrite summary and comparison

## License

[Your License Here]

## Status

✅ Complete rewrite (2025-11-29)
✅ All features working
✅ No known bugs
✅ Scrollbar issue fixed
✅ Ready for production
✅ Ready for extension
