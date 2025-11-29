# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AnthropIDE is a TUI (Terminal User Interface) IDE built with Textual for working with Anthropic AI models. It provides a project-based interface for managing context files and message chains for AI conversations.

**Architecture**: Simple, Direct, Textual-Native (complete rewrite 2025-11-29)

## Development Commands

### Environment Setup
```bash
# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

**DO NOT EVER RUN THIS APPLICATION IN THE CLAUDE AGENT CLI!**

If you need output from the application, you must ask the user to run it in another tab and
report back what you need. Running this application without its own terminal will cause
errors and break the system.

This is a TUI application - it expects to run in its own window. It cannot be
safely run as a child process.

### Code Validation

DO NOT EVER RUN THIS APPLICATION.

Ask the user to run commands and return output.

```bash
# Check Python syntax
python -m py_compile anthropide.py
```

## Architecture

### Four Clear Layers

1. **Data Model Layer** (Lines 36-318)
   - Pure Python dataclasses with no UI dependencies
   - `Session`: Complete session data (model, system, tools, messages, contexts)
   - `Project`: Project management with directory structure
   - `Message`, `SystemBlock`, `Tool`, `ContextFile`: Data structures
   - JSON serialization with load/save/backup

2. **Widget Components** (Lines 353-603)
   - Dumb views that display data and emit events
   - `MessageWidget`, `SystemBlockWidget`, `ToolWidget`, `ContextFileWidget`
   - Receive data via constructor, render in `compose()`
   - Post custom messages on interaction

3. **Container Widgets** (Lines 610-750)
   - Smart containers that manage lists
   - `MessageList`, `SystemBlockList`, `ToolList`, `ContextFileList`
   - Own data, rebuild when data changes
   - Simple `remove_children()` + `mount()` pattern

4. **Screens** (Lines 757-1152)
   - Orchestrators that own data and handle events
   - `ProjectSelectScreen`: Project selection/creation
   - `MainScreen`: Main editor with all features
   - Handle events, update data, refresh UI

### Data Flow

```
User Interaction
  ↓
Widget posts custom message (DeleteItem, MoveItem, ItemChanged)
  ↓
Screen handles message (on_delete_item, on_move_item, on_item_changed)
  ↓
Screen updates data directly (self.session.messages.append(...))
  ↓
Screen calls save() and refresh_*()
  ↓
Container widget rebuilds
  ↓
UI updates
```

### Key Principles

1. **Direct Updates**: No reducer, no virtual DOM - just update data and rebuild
2. **Textual-Native**: Use compose(), custom messages, proper screens
3. **Simple Rebuilds**: `remove_children()` + `mount()` is fast enough
4. **Clear Separation**: Data model has no UI dependencies

## Directory Structure

```
.anthropide/
└── projects/
    └── {project_name}/
        ├── current_session.json
        ├── current_session.json.{timestamp}  (backups)
        ├── environments/
        │   └── *.md
        ├── explorations/
        │   └── *.md
        └── plans/
            └── *.md
```

## Session File Format

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8192,
  "system": [
    {
      "type": "text",
      "text": "System prompt text",
      "id": "uuid",
      "cache_control": {"type": "ephemeral"}  // optional
    }
  ],
  "tools": [
    {
      "name": "ToolName",
      "description": "Tool description",
      "input_schema": {...},
      "id": "uuid"
    }
  ],
  "messages": [
    {
      "role": "user|assistant",
      "content": [
        {"type": "text", "text": "Message text"}
      ],
      "id": "uuid"
    }
  ],
  "selected_contexts": [
    {"path": "/absolute/path/to/file.md", "section": "environments|explorations|plans"}
  ]
}
```

## Implementation Notes

### Adding a New Feature

1. **Update Data Model**: Add field to `Session` or related dataclass
2. **Update Widget**: Create or modify widget to display/edit data
3. **Wire Events**: Add event handler in screen to update data
4. **Test**: Verify save/load works

### Widget Pattern

```python
class MyWidget(Vertical):
    """Widget that displays something"""

    def __init__(self, data: MyData):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        # Build UI
        yield Label(self.data.title)
        yield Button("Delete", id=f"delete-{self.data.id}")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id.startswith("delete-"):
            self.post_message(DeleteItem(self.data.id))
            event.stop()
```

### Container Pattern

```python
class MyList(VerticalScroll):
    """Container for multiple items"""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        for idx, item in enumerate(self.session.items):
            yield MyWidget(item, idx, len(self.session.items))

    def refresh_items(self, session: Session):
        """Rebuild entire list"""
        self.session = session
        self.remove_children()
        for idx, item in enumerate(self.session.items):
            self.mount(MyWidget(item, idx, len(self.session.items)))
```

### Screen Pattern

```python
class MyScreen(Screen):
    """Screen that owns data"""

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.session = project.load_session()

    def on_delete_item(self, event: DeleteItem):
        """Handle delete request"""
        self.session.items = [i for i in self.session.items if i.id != event.item_id]
        self.save_and_refresh()

    def save_and_refresh(self):
        """Save and update UI"""
        self.project.save_session(self.session)
        self.query_one(MyList).refresh_items(self.session)
```

## Common Tasks

### Reading the Code

- Start with data model (lines 36-318) to understand data structures
- Look at MainScreen.compose() (lines 919-961) to see UI layout
- Follow event handlers to see how data updates work

### Debugging

- Print `self.session` to see all data
- Check `.anthropide/projects/*/current_session.json` for persistence
- Add prints in event handlers to trace flow

### Testing

- Syntax: `python -m py_compile anthropide.py`
- Run in separate terminal: `python anthropide.py`
- Test all features: create project, edit messages, save/load

## Extensibility

### Adding API Integration

```python
# In Session class
async def send_request(self, client):
    """Send request to Anthropic API"""
    response = await client.messages.create(**self.to_anthropic_format())
    return Message.assistant_message(response.content[0].text)

# In MainScreen
async def on_button_pressed(self, event: Button.Pressed):
    if event.button.id == "send-request":
        response = await self.session.send_request(anthropic_client)
        self.session.messages.append(response)
        self.save_and_refresh_messages()
```

### Adding a Plugin System

```python
# Define plugin interface
class EditorPlugin:
    def get_widget(self, session: Session) -> Widget:
        """Return widget to display"""
        pass

# Load in MainScreen
self.plugins = load_plugins()
for plugin in self.plugins:
    yield plugin.get_widget(self.session)
```

## Documentation

- `FRESH_ARCHITECTURE.md`: Complete architecture design
- `REWRITE_COMPLETE.md`: Rewrite summary and comparison
- `CLAUDE.md`: This file (project instructions)

## Key Takeaways

1. **Simple is better**: Direct updates beat complex patterns
2. **Work with Textual**: Don't fight the framework
3. **Clear layers**: Data, Widgets, Containers, Screens
4. **Easy to extend**: Add features without touching core
5. **No magic**: Straightforward code, easy to understand

## Status

✅ Complete rewrite (2025-11-29)
✅ All features working
✅ No known bugs
✅ Ready for production
✅ Ready for extension
