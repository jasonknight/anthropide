# AnthropIDE Deep Codebase Analysis

**Generated:** 2025-11-29
**Purpose:** Guide AI assistants in understanding AnthropIDE's architecture, implementation patterns, and Textual framework usage

---

## Executive Summary

AnthropIDE is a Terminal User Interface (TUI) IDE built with the Textual framework for managing conversations with Anthropic's Claude AI models. The application has been refactored to follow a **unidirectional data flow architecture** inspired by React/Redux, featuring pure state management, event-driven updates, and reactive widget composition.

**Key Stats:**
- Single file implementation: `anthropide.py` (2,506 lines)
- Architecture: Functional state management with object-oriented UI layer
- Framework: Textual v0.47.0+
- Dependencies: anthropic, tiktoken, textual

---

## Architecture Overview

### 1. Unidirectional Data Flow

The application follows a strict data flow pattern:

```
User Interaction → AppEvent → Reducer → New AppState → Widget Update → UI Render
```

This architecture provides:
- **Predictable state changes**: All state transitions go through the reducer
- **Testable logic**: Pure functions can be tested in isolation
- **Debugging**: State changes are traceable through events
- **Time-travel debugging potential**: Event log could enable replay

### 2. Layer Separation

```
┌─────────────────────────────────────────┐
│   UI Layer (Textual Widgets/Screens)   │  ← Object-oriented, imperative
├─────────────────────────────────────────┤
│        Event Layer (AppEvents)          │  ← Intermediate representation
├─────────────────────────────────────────┤
│   Logic Layer (Reducer + AppComponent) │  ← Functional, pure
├─────────────────────────────────────────┤
│      Data Layer (AppState)              │  ← Immutable state container
├─────────────────────────────────────────┤
│   Persistence Layer (FileSystemAPI)     │  ← I/O abstraction
└─────────────────────────────────────────┘
```

---

## Core Data Structures (Lines 39-146)

### ContentBlock (Lines 40-44)
```python
@dataclass
class ContentBlock:
    type: str  # "text", "image", etc.
    text: Optional[str] = None
```
**Purpose:** Represents a single content block within a message. Supports multi-modal messages (future extensibility for images, tool_use, etc.).

**Key Insight:** Even though only text blocks are currently used, the structure anticipates Anthropic's full message API.

### SystemBlock (Lines 48-59)
```python
@dataclass
class SystemBlock:
    type: str  # "text"
    text: str
    cache_control: Optional[Dict[str, str]] = None  # {"type": "ephemeral"}
```
**Purpose:** Represents a system prompt block with optional prompt caching.

**Key Insight:** The `cache_control` field enables Anthropic's prompt caching feature, reducing costs for repeated system prompts.

### Tool (Lines 63-75)
```python
@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
```
**Purpose:** Defines a tool that Claude can use, following Anthropic's tool API format.

**Default Tools:** The default session includes "Read" and "Edit" tools (lines 502-530).

### Message (Lines 79-88)
```python
@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: List[ContentBlock]

    def get_content_hash(self) -> str:
        """Get a stable hash for this message to use as unique ID"""
        content_str = f"{self.role}:{self.content[0].text if self.content else ''}"
        return hashlib.md5(content_str.encode()).hexdigest()[:12]
```
**Purpose:** Represents a conversation message with multi-block content.

**Key Insight:** `get_content_hash()` provides stable IDs for widget reconciliation (line 1722, 1788).

### AppState (Lines 98-146)
```python
@dataclass
class AppState:
    # Project info
    project_name: Optional[str] = None
    project_path: Optional[Path] = None
    available_projects: List[str] = field(default_factory=list)

    # API Configuration
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192

    # System prompt
    system_blocks: List[SystemBlock] = field(default_factory=list)

    # Tools
    tools: List[Tool] = field(default_factory=list)

    # Session data
    messages: List[Message] = field(default_factory=list)
    selected_contexts: List[ContextFile] = field(default_factory=list)

    # Available context files by section
    available_files: Dict[str, List[str]] = field(default_factory=dict)

    # UI state
    screen: str = "project_select"  # "project_select" or "main"
```

**Purpose:** Single source of truth for entire application state.

**Key Methods:**
- `to_session_dict()` (lines 127-145): Converts state to Anthropic API format for persistence

**Design Note:** AppState is designed to be immutable. The reducer creates new instances rather than modifying existing ones.

---

## Event System (Lines 152-290)

### Event Hierarchy

All events inherit from `AppEvent` base class:

```python
class AppEvent:
    """Base class for all application events"""
    pass
```

### Event Categories

1. **Project Events** (lines 158-166):
   - `ProjectSelected(project_name)`
   - `ProjectCreateRequested(project_name)`

2. **Context Events** (lines 169-184):
   - `ContextToggled(file_path, section, checked)`
   - `ContextDeleted(index)`
   - `ContextMoved(index, direction)`

3. **API Configuration Events** (lines 188-196):
   - `ModelChanged(model)`
   - `MaxTokensChanged(max_tokens)`

4. **System Block Events** (lines 199-224):
   - `SystemBlockAdded()`
   - `SystemBlockDeleted(index)`
   - `SystemBlockMoved(index, direction)`
   - `SystemBlockTextChanged(index, text)`
   - `SystemBlockCacheToggled(index, enabled)`

5. **Tool Events** (lines 227-241):
   - `ToolAdded()`
   - `ToolDeleted(index)`
   - `ToolFieldChanged(index, field, value)`

6. **Message Events** (lines 244-282):
   - `MessageAdded(role)`
   - `MessageRoleChanged(index, role)`
   - `MessageContentBlockAdded(msg_index)`
   - `MessageContentBlockDeleted(msg_index, block_index)`
   - `MessageContentBlockChanged(msg_index, block_index, text)`
   - `MessageDeleted(index)`
   - `MessageMoved(index, direction)`

7. **Session Events** (lines 285-290):
   - `NewSessionRequested()`
   - `AppExitRequested()`

**Design Pattern:** Events are **data carriers only** - they contain no logic, only parameters needed for state updates.

---

## State Management (Lines 372-550)

### Loading State

#### load_initial_state(fs: FileSystemAPI) → AppState (Lines 372-387)
**Purpose:** Initialize application with available projects list.

**Flow:**
1. Create `.anthropide/projects/` directory structure
2. List all subdirectories as available projects
3. Return AppState with `screen="project_select"`

**Called:** Once at application startup (line 1148)

#### load_project_state(state: AppState, project_name: str, fs: FileSystemAPI) → AppState (Lines 390-488)
**Purpose:** Load a specific project's session data.

**Flow:**
1. Create project subdirectories: `environments/`, `explorations/`, `plans/`
2. Load `current_session.json` or create default
3. Parse API configuration (model, max_tokens)
4. Parse system blocks with cache control
5. Parse tools
6. Parse messages (handles both old string format and new block format, lines 445-454)
7. Parse selected contexts
8. List available markdown files in each section
9. Return AppState with `screen="main"`

**Backward Compatibility:** Lines 445-454 handle migration from old string-based content to new ContentBlock format.

#### create_default_session() → Dict[str, Any] (Lines 491-533)
**Purpose:** Create default session in Anthropic API format.

**Defaults:**
- Model: `claude-sonnet-4-5-20250929`
- Max tokens: `8192`
- System prompt: "You are a helpful AI assistant..."
- Tools: Read and Edit tools with full JSON schemas
- Empty messages and contexts

**Design Note:** Returns dict (not AppState) because it represents the persistent JSON format.

### Saving State

#### save_session(project_path: Path, session_data: Dict[str, Any], fs: FileSystemAPI) (Lines 536-539)
**Purpose:** Write session to `current_session.json` with pretty-printed JSON.

**Called:** After every state change that should persist (throughout reducer)

#### backup_session(project_path: Path, fs: FileSystemAPI) (Lines 542-549)
**Purpose:** Create timestamped backup of current session.

**Format:** `current_session.json.{YYYYMMDD_HHMMSS}`

**Called:** When creating a new session (line 714)

---

## The Reducer (Lines 556-1111)

### Function Signature

```python
def reduce_state(state: AppState, event: AppEvent, fs: FileSystemAPI) -> AppState:
    """Pure reducer: (state, event) -> new state"""
```

**Purity Constraint:** This function should have no side effects beyond file I/O. It creates new AppState instances rather than mutating the input state.

### Key Reduction Patterns

#### Pattern 1: Create and Return New State
```python
elif isinstance(event, ModelChanged):
    new_state = AppState(
        project_name=state.project_name,
        project_path=state.project_path,
        # ... copy all fields ...
        model=event.model,  # Only this field changes
        # ... copy remaining fields ...
    )
    if new_state.project_path:
        save_session(new_state.project_path, new_state.to_session_dict(), fs)
    return new_state
```

**Issue:** This pattern is verbose and error-prone. Consider using `dataclasses.replace()` for cleaner immutable updates.

#### Pattern 2: List Manipulation
```python
elif isinstance(event, MessageDeleted):
    if 0 <= event.index < len(state.messages):
        new_messages = [m for i, m in enumerate(state.messages) if i != event.index]
        new_state = AppState(...)
        # ...
        return new_state
    return state
```

**Key Insight:** Always validate indices before manipulation. Returns unchanged state if invalid.

#### Pattern 3: Path Normalization
```python
elif isinstance(event, ContextToggled):
    # Normalize path to absolute
    abs_path = str(Path(event.file_path).resolve())

    if event.checked:
        # Add to selected contexts (if not already present)
        if not any(str(Path(c.path).resolve()) == abs_path for c in state.selected_contexts):
            # ...
```

**Key Insight:** Paths are normalized to absolute paths to ensure consistent comparison (lines 584-585, 589, 608).

### Event Handling Coverage

The reducer handles **18 event types** with comprehensive logic:

- **Project Events** (lines 559-581): Create project structure on disk, load project state
- **Context Events** (lines 583-667): Toggle, delete, reorder context files with path normalization
- **Message Events** (lines 669-710): Delete, reorder messages with bounds checking
- **Session Events** (lines 712-721): Backup and reset to default session
- **API Config Events** (lines 724-758): Update model and max_tokens
- **System Block Events** (lines 761-883): Add, delete, move, edit, toggle cache
- **Tool Events** (lines 886-969): Add, delete, edit tools with JSON schema parsing
- **Message Content Events** (lines 972-1109): Add messages, change role, add/delete/edit content blocks

**Error Handling:** JSON parsing errors for tool schemas are caught and ignored (lines 944-947).

---

## AppComponent (Lines 1118-1443)

### Purpose
**Pure application logic layer** that bridges events and rendering. Does not directly interact with Textual.

### Key Attributes

```python
class AppComponent:
    RENDER_EVENTS = {
        ProjectSelected, ProjectCreateRequested,
        ContextToggled, ContextDeleted, ContextMoved,
        # ... 14+ event types ...
    }

    def __init__(self, fs: Optional[FileSystemAPI] = None):
        self.fs = fs or FileSystemAPI()
        self.state = load_initial_state(self.fs)
```

### Core Methods

#### handle_event(event: AppEvent) → bool (Lines 1150-1159)
**Purpose:** Process event and determine if re-render is needed.

**Returns:** `True` if event type is in `RENDER_EVENTS`, `False` otherwise.

**Implementation:**
```python
def handle_event(self, event: AppEvent) -> bool:
    # Update state
    self.state = reduce_state(self.state, event, self.fs)

    # Check if this event type should trigger re-render
    return type(event) in self.RENDER_EVENTS
```

#### render() → RenderNode (Lines 1161-1166)
**Purpose:** Generate virtual render graph from current state.

**Note:** RenderNode system is **conceptual** in current implementation. The actual rendering happens in Textual widgets. This method exists for architectural completeness but isn't actively used.

### Render Methods (Lines 1168-1442)

These methods generate RenderNode virtual DOM:

- `_render_project_select()` (lines 1168-1222): Project selection screen
- `_render_main_screen()` (lines 1224-1258): Main editor screen
- `_render_context_control()` (lines 1260-1307): Left sidebar with context files
- `_render_context_chain()` (lines 1309-1347): Message chain container
- `_render_message()` (lines 1349-1395): Individual message widget
- `_render_context_file()` (lines 1397-1442): Context file display

**Current Status:** These methods generate a virtual representation but aren't used for actual rendering. The reactive widgets (MessageChainWidget, ContextControlWidget) handle their own rendering.

**Design Note:** This suggests an incomplete migration from virtual DOM rendering to reactive widgets. The RenderNode system could be removed or fully implemented.

---

## Reactive Widgets (Lines 1452-1910)

### Design Philosophy

These widgets are **self-contained** and **reactive**:
- They maintain their own state as instance variables
- They rebuild their entire child tree when data changes
- They use atomic rebuild patterns to avoid partial updates

### MessageChainWidget (Lines 1452-1822)

**Purpose:** Display the full API request structure including config, system prompts, tools, messages, and context files.

#### Initialization (Lines 1458-1477)
```python
def __init__(
    self,
    model: str,
    max_tokens: int,
    system_blocks: List[SystemBlock],
    tools: List[Tool],
    messages: List[Message],
    selected_contexts: List[ContextFile],
    fs: FileSystemAPI,
):
    super().__init__(id="messages-container")
    self.fs = fs
    self._api_config = {"model": model, "max_tokens": max_tokens}
    self._system_blocks = system_blocks
    self._tools = tools
    self._messages = messages
    self._selected_contexts = selected_contexts
    self._is_rebuilding = False
    self._pending_rebuild = False
```

**Key Fields:**
- `_is_rebuilding`: Prevents concurrent rebuild operations
- `_pending_rebuild`: Flags that another rebuild is needed after current one completes

#### Public API (Lines 1483-1503)

```python
def update_data(
    self,
    model: str,
    max_tokens: int,
    system_blocks: List[SystemBlock],
    tools: List[Tool],
    messages: List[Message],
    selected_contexts: List[ContextFile],
) -> None:
    """Public API to update displayed data"""
    self._api_config = {"model": model, "max_tokens": max_tokens}
    self._system_blocks = system_blocks
    self._tools = tools
    self._messages = messages
    self._selected_contexts = selected_contexts

    # If already rebuilding, mark that we need another rebuild
    if self._is_rebuilding:
        self._pending_rebuild = True
    else:
        self._rebuild_content()
```

**Called:** By MainScreen when state changes (lines 2061-2068)

#### Atomic Rebuild Pattern (Lines 1505-1554)

```python
def _rebuild_content(self) -> None:
    """Rebuild message chain content atomically"""
    # Prevent concurrent rebuilds
    if self._is_rebuilding:
        self._pending_rebuild = True
        return

    self._is_rebuilding = True
    self._pending_rebuild = False

    # Remove existing children
    self.remove_children()

    # Build all widgets BEFORE mounting
    widgets_to_mount = []

    # [Build API config widget]
    # [Build system blocks widgets]
    # [Build tools widgets]
    # [Build message widgets]
    # [Build context widgets]

    # Mount all at once (atomic operation)
    if widgets_to_mount:
        self.mount(*widgets_to_mount)

    # Mark rebuild as complete and handle pending rebuild
    self._is_rebuilding = False
    if self._pending_rebuild:
        # Schedule another rebuild with the latest data
        self.call_after_refresh(self._rebuild_content)
```

**Critical Pattern:** This pattern ensures:
1. No partial updates (all widgets mounted atomically)
2. No concurrent rebuilds (flag-based locking)
3. No lost updates (pending rebuild queues next rebuild)

**Performance Note:** `call_after_refresh()` (line 1554) ensures the rebuild happens after the current refresh cycle, avoiding widget tree inconsistencies.

#### Widget Creation Methods

1. **_create_api_config_widget()** (lines 1556-1593): Model selector and max tokens input
2. **_create_system_blocks_section()** (lines 1595-1650): System prompt editor with cache control
3. **_create_tools_section()** (lines 1652-1717): Tool editor with JSON schema fields
4. **_create_message_widget()** (lines 1719-1791): Message with role selector and content blocks
5. **_create_context_widget()** (lines 1793-1821): Context file display with token count

**Key Pattern:** Each method constructs complete widget trees **before** returning. No incremental construction.

#### Stable Widget IDs

**Messages** (line 1722):
```python
msg_hash = message.get_content_hash()
# ...
id=f"message-{msg_hash}"
```

**Context Files** (lines 1887-1889):
```python
path_hash = hashlib.md5(abs_path.encode()).hexdigest()[:16]
widget_id = f"ctx-checkbox-{path_hash}"
```

**Purpose:** Stable IDs enable event routing. When a button is pressed, we can extract the index from its ID (e.g., `msg-delete-3` → index 3).

### ContextControlWidget (Lines 1824-1910)

**Purpose:** Display available context files organized by section with checkboxes for selection.

**Similar Pattern:** Uses the same atomic rebuild pattern as MessageChainWidget:
- `update_files()`: Public API for data updates
- `_rebuild_content()`: Atomic rebuild with flag-based locking
- Checkbox widgets store data via custom attributes (`checkbox.data_path`, `checkbox.data_section`)

**Key Difference:** Simpler than MessageChainWidget - only displays checkboxes, no complex nesting.

---

## Textual Screens (Lines 1918-2260)

### ProjectSelectScreen (Lines 1918-1991)

**Purpose:** Initial screen for project selection or creation.

#### Composition (Lines 1929-1949)
```python
def compose(self) -> ComposeResult:
    yield Header()

    with Container(id="project-select"):
        yield Label("Select a Project", classes="title")

        with ScrollableContainer(id="project-list"):
            # Build project buttons dynamically
            if self.app_component.state.available_projects:
                for project in self.app_component.state.available_projects:
                    yield Button(project, variant="primary", id=f"project-{project}")
            else:
                yield Label("No projects found. Create one below.")

        with Container(id="create-project"):
            yield Label("Create New Project")
            yield Input(placeholder="Project name", id="new-project-input")
            yield Button("Create", variant="success", id="create-project-btn")

    yield Footer()
```

**Textual Pattern:**
- `yield` returns widgets to parent
- `with Container():` creates context for child widgets
- IDs enable CSS targeting and query_one() lookups

#### Event Handling (Lines 1955-1991)

**on_button_pressed()** (lines 1955-1970):
- Extracts project name from button ID using string manipulation
- Calls `_load_project()` or `_create_project()`

**Pattern:**
```python
if button_id.startswith("project-"):
    project_name = button_id.replace("project-", "")
    self._load_project(project_name)
```

**on_input_submitted()** (lines 1972-1977):
- Handles Enter key in project name input
- Calls `_create_project()`

**_create_project()** (lines 1979-1984):
1. Create `ProjectCreateRequested` event
2. Pass to `app_component.handle_event()`
3. Push MainScreen onto screen stack

**_load_project()** (lines 1986-1991):
1. Create `ProjectSelected` event
2. Pass to `app_component.handle_event()`
3. Push MainScreen onto screen stack

### MainScreen (Lines 1994-2260)

**Purpose:** Main editor screen with three-column layout and command input.

#### Composition (Lines 2007-2044)

```python
def compose(self) -> ComposeResult:
    state = self.app_component.state

    yield Header()

    with Horizontal(id="main-container"):
        # Left sidebar - context files
        self.context_control_widget = ContextControlWidget(
            available_files=state.available_files,
            selected_contexts=state.selected_contexts,
        )
        yield self.context_control_widget

        # Right side - API request editor
        with Container(id="context-chain"):
            with Horizontal(classes="chain-header"):
                yield Label("API Request Editor", classes="section-header")
                yield Button("New Session", variant="success", id="new-session")
                yield Button("+ Add Message", variant="success", id="message-add")

            # Dynamic API request editor
            self.message_chain_widget = MessageChainWidget(
                model=state.model,
                max_tokens=state.max_tokens,
                system_blocks=state.system_blocks,
                tools=state.tools,
                messages=state.messages,
                selected_contexts=state.selected_contexts,
                fs=self.app_component.fs,
            )
            yield self.message_chain_widget

    # Command input
    with Container(id="command-container"):
        yield Input(placeholder="Enter command (e.g., /exit)", id="command-input")

    yield Footer()
```

**Widget References:** Stores references to reactive widgets for later updates (lines 2004-2005):
```python
self.message_chain_widget: Optional[MessageChainWidget] = None
self.context_control_widget: Optional[ContextControlWidget] = None
```

#### Core Event Handler (Lines 2050-2077)

```python
def handle_app_event(self, event: AppEvent) -> None:
    """Handle application event and update widgets"""
    # Update state via pure reducer
    should_render = self.app_component.handle_event(event)

    if should_render:
        # Get new state
        state = self.app_component.state

        # Update dynamic API request editor
        if self.message_chain_widget:
            self.message_chain_widget.update_data(
                model=state.model,
                max_tokens=state.max_tokens,
                system_blocks=state.system_blocks,
                tools=state.tools,
                messages=state.messages,
                selected_contexts=state.selected_contexts,
            )

        # Update context control if files changed
        if isinstance(event, (ProjectSelected, ProjectCreateRequested)):
            if self.context_control_widget:
                self.context_control_widget.update_files(
                    available_files=state.available_files,
                    selected_contexts=state.selected_contexts,
                )
```

**Flow:**
1. Call `app_component.handle_event(event)` to update state
2. If event triggers render, get new state
3. Push new state to reactive widgets via `update_data()` or `update_files()`

#### Button Event Routing (Lines 2078-2145)

**Pattern:** Extract action and index from button ID:

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id

    if not button_id:
        return

    app_event = None

    # Session management
    if button_id == "new-session":
        app_event = NewSessionRequested()

    # System block actions
    elif button_id == "system-block-add":
        app_event = SystemBlockAdded()
    elif button_id.startswith("system-delete-"):
        idx = int(button_id.replace("system-delete-", ""))
        app_event = SystemBlockDeleted(idx)
    # ... more button handlers ...

    if app_event:
        self.handle_app_event(app_event)
```

**ID Conventions:**
- `{action}-{index}`: Simple actions (e.g., `msg-delete-3`)
- `{type}-{action}-{index}`: Scoped actions (e.g., `system-delete-1`)
- `{type}-{action}-{index1}-{index2}`: Nested actions (e.g., `msg-block-delete-2-1`)

**Complex ID Parsing** (lines 2127-2131):
```python
elif button_id.startswith("msg-block-delete-"):
    # Format: msg-block-delete-{msg_idx}-{block_idx}
    parts = button_id.replace("msg-block-delete-", "").split("-")
    msg_idx = int(parts[0])
    block_idx = int(parts[1])
    app_event = MessageContentBlockDeleted(msg_idx, block_idx)
```

#### Other Event Handlers

**on_checkbox_changed()** (lines 2147-2177):
- Handles system block cache control checkboxes
- Handles context file selection checkboxes
- Uses custom attributes (`data_path`, `data_section`) stored on checkbox widgets

**on_select_changed()** (lines 2179-2195):
- Handles model selection dropdown
- Handles message role selection dropdowns

**on_text_area_changed()** (lines 2197-2223):
- Handles system block text editing
- Handles tool schema editing (JSON)
- Handles message content block editing
- Auto-saves on every keystroke

**on_input_changed()** (lines 2225-2251):
- Handles max tokens input (with validation)
- Handles tool name and description inputs

**on_input_submitted()** (lines 2253-2259):
- Handles command input (currently only `/exit`)

---

## AnthropIDEApp (Lines 2266-2505)

### App Class (Lines 2266-2495)

**Purpose:** Top-level Textual app that manages screens and CSS.

#### CSS Styling (Lines 2269-2486)

**Layout System:**
- `width: 30%` / `width: 70%`: Percentage-based widths
- `height: 1fr`: Fractional units for flexible heights
- `height: 3`: Fixed height in rows
- `padding: 1`: Internal spacing
- `margin: 1 0`: Vertical margin only

**Component Styling:**
```css
#main-container {
    width: 100%;
    height: 1fr;  /* Takes all available height */
}

#context-control {
    width: 30%;
    height: 100%;
    border-right: solid $primary;
    padding: 1;
}

#context-chain {
    width: 70%;
    height: 100%;
    padding: 1;
}
```

**Color Variables:** Uses Textual's built-in color variables:
- `$primary`: Primary theme color (blue)
- `$success`: Success color (green)
- `$error`: Error color (red)
- `$warning`: Warning color (yellow)
- `$accent`: Accent color

**Widget-Specific Styling:**
```css
TextArea {
    height: 10;
    margin-top: 1;
}
```

**Class-Based Styling:**
- `.section-header`: Bold, primary background
- `.message-container`: Primary border, padding
- `.context-file-container`: Success border (green)
- `.btn-up`, `.btn-down`: Small fixed-width buttons

#### Initialization (Lines 2488-2495)

```python
def __init__(self):
    super().__init__()
    self.app_component = AppComponent()

def on_mount(self) -> None:
    """Initialize the application"""
    # Start with project select screen
    self.push_screen(ProjectSelectScreen(self.app_component))
```

**Key:** `app_component` is shared across all screens, providing centralized state management.

### Entry Point (Lines 2498-2505)

```python
def main():
    """Entry point for the application"""
    app = AnthropIDEApp()
    app.run()

if __name__ == "__main__":
    main()
```

---

## Textual Framework Deep Dive

### 1. Widget Composition Pattern

**Declarative Composition:**
```python
def compose(self) -> ComposeResult:
    yield Header()

    with Container(id="main-container"):
        yield Label("Title")
        yield Button("Click me")

    yield Footer()
```

**How it works:**
- `yield` returns widgets to parent container
- `with Container():` creates a context for nested widgets
- Widgets are constructed immediately, not lazily

**ComposeResult:** Special return type that accumulates yielded widgets.

### 2. Event System

**Event Bubbling:**
Events bubble up from child widgets to parent containers:
```
Button → Container → Screen → App
```

**Handler Convention:**
```python
def on_{widget_type}_{event_name}(self, event: EventType) -> None:
    # Handle event
```

Examples:
- `on_button_pressed(self, event: Button.Pressed)`
- `on_input_submitted(self, event: Input.Submitted)`
- `on_text_area_changed(self, event: TextArea.Changed)`

**Accessing Widget:**
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id
    button_text = event.button.label
```

### 3. Widget Querying

**query_one():** Get single widget by ID or type:
```python
input_widget = self.query_one("#new-project-input", Input)
```

**query():** Get multiple widgets:
```python
all_buttons = self.query(Button)
```

**Type Safety:** The second parameter provides type hints for the return value.

### 4. Dynamic Widget Management

**remove_children():** Remove all child widgets:
```python
self.remove_children()
```

**mount():** Add new widgets to container:
```python
self.mount(widget1, widget2, widget3)
```

**Atomic Updates:**
```python
self.remove_children()
widgets = [create_widget() for item in items]
self.mount(*widgets)  # All mounted atomically
```

### 5. Widget Lifecycle Hooks

**on_mount():** Called after widget is added to DOM:
```python
def on_mount(self) -> None:
    """Build initial content when mounted"""
    self._rebuild_content()
```

**on_unmount():** Called before widget is removed (not used in AnthropIDE).

**compose():** Called once during widget construction:
```python
def compose(self) -> ComposeResult:
    yield Label("Static content")
```

### 6. Reactive Properties

**Not heavily used in AnthropIDE**, but imported (line 1449):
```python
from textual.reactive import reactive

class MyWidget(Widget):
    counter = reactive(0)  # Automatically triggers refresh on change
```

**Design Choice:** AnthropIDE uses manual rebuilds instead of reactive properties for more explicit control.

### 7. Screen Management

**push_screen():** Add screen to stack:
```python
self.app.push_screen(MainScreen(self.app_component))
```

**pop_screen():** Remove current screen and return to previous.

**switch_screen():** Replace current screen without stacking.

**Screen Stack:** AnthropIDE uses a simple two-screen stack:
```
[ProjectSelectScreen] → push → [ProjectSelectScreen, MainScreen]
```

### 8. CSS System

**Syntax:** Similar to web CSS but with Textual-specific properties:

```css
#widget-id {
    width: 50%;
    height: 1fr;
    border: solid $primary;
    padding: 1;
}

.css-class {
    text-style: bold;
    background: $success;
}
```

**Layout Properties:**
- `width`, `height`: Size (%, fr, fixed)
- `padding`, `margin`: Spacing
- `border`: Border style and color

**Styling Properties:**
- `background`, `color`: Colors
- `text-style`: bold, italic, underline
- `text-align`: left, center, right

**Specificity:** ID selectors > class selectors > type selectors

---

## File System and Persistence

### Directory Structure

```
.anthropide/
└── projects/
    └── {project_name}/
        ├── current_session.json          # Active session
        ├── current_session.json.{timestamp}  # Backups
        ├── environments/
        │   └── *.md                      # Context files (environments)
        ├── explorations/
        │   └── *.md                      # Context files (explorations)
        └── plans/
            └── *.md                      # Context files (plans)
```

### Session File Format

**Example: current_session.json**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8192,
  "system": [
    {
      "type": "text",
      "text": "You are a helpful AI assistant.",
      "cache_control": {"type": "ephemeral"}
    }
  ],
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
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Hello, Claude!"
        }
      ]
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

**Format:** Matches Anthropic's Messages API format for easy API integration.

### FileSystemAPI (Lines 317-366)

**Purpose:** Abstraction layer for file operations, enabling:
- **Testing:** Mock file system in unit tests
- **Portability:** Swap implementations for different storage backends
- **Consistency:** Centralized error handling

**Methods:**
- `read_file(file_path)`: Read file contents
- `write_file(file_path, content)`: Write file contents
- `file_exists(file_path)`: Check if file exists
- `create_directory(dir_path)`: Create directory (with parents)
- `list_files(dir_path, pattern)`: List files matching glob pattern
- `list_directories(dir_path)`: List subdirectories
- `calculate_tokens(content)`: Count tokens using tiktoken

**Token Counting** (lines 359-365):
```python
@staticmethod
def calculate_tokens(content: str) -> int:
    """Calculate token count for string"""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(content))
    except Exception:
        return 0
```

**Encoding:** Uses `cl100k_base`, which is compatible with Claude models.

---

## Key Implementation Patterns

### 1. Stable ID Generation

**Problem:** Need consistent IDs for widgets across rebuilds to enable event routing.

**Solution: Content Hashing**

**Messages** (line 84-87):
```python
def get_content_hash(self) -> str:
    """Get a stable hash for this message to use as unique ID"""
    content_str = f"{self.role}:{self.content[0].text if self.content else ''}"
    return hashlib.md5(content_str.encode()).hexdigest()[:12]
```

**Context Files** (lines 1287-1288, 1888-1889):
```python
path_hash = hashlib.md5(abs_path.encode()).hexdigest()[:16]
widget_id = f"ctx-checkbox-{path_hash}"
```

**Trade-off:** Hash collisions are possible but unlikely. Could use full hash or UUID for complete uniqueness.

### 2. Atomic Rebuild Pattern

**Problem:** Partial widget updates can cause UI inconsistencies.

**Solution: Remove All → Build All → Mount All**

```python
def _rebuild_content(self) -> None:
    # 1. Prevent concurrent rebuilds
    if self._is_rebuilding:
        self._pending_rebuild = True
        return

    self._is_rebuilding = True
    self._pending_rebuild = False

    # 2. Remove existing children
    self.remove_children()

    # 3. Build all widgets
    widgets_to_mount = []
    for item in self._items:
        widgets_to_mount.append(self._create_widget(item))

    # 4. Mount all at once
    if widgets_to_mount:
        self.mount(*widgets_to_mount)

    # 5. Handle pending rebuilds
    self._is_rebuilding = False
    if self._pending_rebuild:
        self.call_after_refresh(self._rebuild_content)
```

**Benefits:**
- No partial states visible to user
- Prevents concurrent rebuilds
- Ensures latest data is rendered

### 3. Path Normalization

**Problem:** File paths may be stored in different forms (relative, absolute, with symlinks).

**Solution: Normalize to Absolute Paths**

```python
# When adding context
abs_path = str(Path(event.file_path).resolve())

# When comparing contexts
if not any(str(Path(c.path).resolve()) == abs_path for c in state.selected_contexts):
    # Add context
```

**Benefits:**
- Consistent comparison
- Handles symlinks correctly
- Works across different working directories

### 4. Event-Driven State Updates

**Pattern:**
```
UI Interaction → Event Creation → Reducer → State Update → Widget Update
```

**Example Flow:**

1. User clicks "Delete" button on message 2
2. `MainScreen.on_button_pressed()` extracts index from button ID: `msg-delete-2`
3. Creates `MessageDeleted(2)` event
4. Calls `handle_app_event(event)`
5. Reducer creates new state with message removed
6. `handle_app_event()` calls `message_chain_widget.update_data()`
7. Widget rebuilds to show updated message list

**Benefits:**
- Separation of concerns
- Testable logic
- Predictable state changes
- Easy debugging (log events)

### 5. Index-Based Editing

**Problem:** How to identify which message/block to edit when button is clicked?

**Solution: Embed Index in Widget ID**

**Button Creation:**
```python
delete_btn = Button("Delete", variant="error", id=f"msg-delete-{index}")
```

**Event Handling:**
```python
elif button_id.startswith("msg-delete-"):
    idx = int(button_id.replace("msg-delete-", ""))
    app_event = MessageDeleted(idx)
```

**Trade-off:** Indices change when items are reordered or deleted. Works because:
1. State updates happen before widget rebuild
2. Rebuild uses new indices from updated state
3. No stale index references

### 6. Custom Widget Attributes

**Problem:** How to pass data from widget creation to event handler?

**Solution: Store Data as Custom Attributes**

**Widget Creation:**
```python
checkbox = Checkbox(
    file_name,
    value=abs_path in self._selected_paths,
    id=widget_id,
)
# Store data for event handling
checkbox.data_path = abs_path
checkbox.data_section = section
```

**Event Handling:**
```python
def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
    checkbox = event.checkbox
    file_path = getattr(checkbox, 'data_path', None)
    section = getattr(checkbox, 'data_section', None)

    if file_path and section:
        app_event = ContextToggled(file_path, section, checkbox.value)
```

**Benefits:**
- Simple data passing
- No need for global state
- Type-safe with getattr() defaults

---

## Architectural Insights

### Strengths

1. **Clear Separation of Concerns**:
   - Data layer (AppState)
   - Logic layer (Reducer, AppComponent)
   - Event layer (AppEvent classes)
   - UI layer (Textual widgets/screens)

2. **Testability**:
   - Pure reducer function can be tested in isolation
   - FileSystemAPI is mockable
   - Events are data-only (no side effects)

3. **Predictability**:
   - All state changes go through single reducer
   - Unidirectional data flow
   - No hidden mutations

4. **Atomic Updates**:
   - Widgets rebuild completely on data change
   - No partial states

5. **Persistence**:
   - Auto-save on every state change
   - Session backup on reset
   - Human-readable JSON format

### Weaknesses and Opportunities

1. **Incomplete Virtual DOM**:
   - RenderNode system exists but isn't used (lines 297-311, 1161-1442)
   - Consider removing or fully implementing
   - Current hybrid approach is confusing

2. **Verbose State Updates**:
   - Reducer creates new AppState by copying all fields (lines 593-618, 629-643, etc.)
   - Consider using `dataclasses.replace()` for cleaner code:
     ```python
     new_state = dataclasses.replace(state, model=event.model)
     ```

3. **No Undo/Redo**:
   - Event log could enable undo/redo functionality
   - Would require storing event history

4. **Performance Concerns**:
   - Complete widget rebuild on every change
   - Could be slow with many messages/contexts
   - Consider diffing or selective updates for large sessions

5. **Error Handling**:
   - Minimal error handling in UI layer
   - File I/O errors could crash app
   - Consider try/except in FileSystemAPI callers

6. **No API Integration Yet**:
   - Anthropic SDK imported but not used (line 32)
   - Session format ready for API integration
   - Need to add "Send Request" functionality

7. **Limited Command System**:
   - Only `/exit` command implemented (line 2257)
   - Could add `/save`, `/load`, `/export`, etc.

---

## Common AI Assistant Tasks

### Adding a New Event Type

1. **Define Event Class** (in event section):
   ```python
   class MyNewEvent(AppEvent):
       def __init__(self, param: str):
           self.param = param
   ```

2. **Add to RENDER_EVENTS** (if it should trigger re-render):
   ```python
   RENDER_EVENTS = {
       # ...
       MyNewEvent,
   }
   ```

3. **Handle in Reducer**:
   ```python
   elif isinstance(event, MyNewEvent):
       # Create new state
       new_state = AppState(...)
       # Save if needed
       if new_state.project_path:
           save_session(new_state.project_path, new_state.to_session_dict(), fs)
       return new_state
   ```

4. **Dispatch from UI**:
   ```python
   def on_button_pressed(self, event: Button.Pressed) -> None:
       if button_id == "my-button":
           app_event = MyNewEvent("param_value")
           self.handle_app_event(app_event)
   ```

### Adding a New Widget Section

1. **Update AppState** (add new field):
   ```python
   @dataclass
   class AppState:
       # ...
       my_new_data: List[MyDataType] = field(default_factory=list)
   ```

2. **Create Widget Builder** (in MessageChainWidget):
   ```python
   def _create_my_section(self) -> Container:
       widgets = []
       for idx, item in enumerate(self._my_new_data):
           widgets.append(self._create_my_widget(item, idx))
       return Container(*widgets, classes="my-section", id="my-section")
   ```

3. **Add to Rebuild** (in `_rebuild_content`):
   ```python
   # Add my section
   if hasattr(self, '_my_new_data'):
       my_section_widget = self._create_my_section()
       widgets_to_mount.append(my_section_widget)
   ```

4. **Update `update_data()` Signature**:
   ```python
   def update_data(
       self,
       # ...
       my_new_data: List[MyDataType],
   ) -> None:
       # ...
       self._my_new_data = my_new_data
       # ...
   ```

### Debugging Tips

1. **Print State Changes**:
   ```python
   def reduce_state(state: AppState, event: AppEvent, fs: FileSystemAPI) -> AppState:
       print(f"Event: {type(event).__name__}")  # Debug print
       # ... reducer logic ...
       print(f"New state: {new_state}")  # Debug print
       return new_state
   ```

2. **Inspect Widget Tree**:
   ```python
   def _rebuild_content(self) -> None:
       print(f"Rebuilding with {len(self._messages)} messages")  # Debug
       # ... rebuild logic ...
   ```

3. **Check Event Routing**:
   ```python
   def on_button_pressed(self, event: Button.Pressed) -> None:
       button_id = event.button.id
       print(f"Button pressed: {button_id}")  # Debug
       # ... handler logic ...
   ```

4. **Validate State Persistence**:
   - Check `.anthropide/projects/{project}/current_session.json`
   - Verify format matches Anthropic API spec
   - Look for backup files with timestamps

---

## Performance Considerations

### Current Performance Profile

**Fast Operations:**
- Event handling (pure functions)
- State updates (immutable data structures)
- File I/O (small JSON files)

**Slow Operations:**
- Complete widget rebuilds (lines 1505-1554)
- Token counting for large files (lines 1796-1799)
- Path normalization on every comparison (lines 584-585, 589, 608)

### Optimization Opportunities

1. **Cache Token Counts**:
   ```python
   # Current: Recalculate on every rebuild
   token_count = self.fs.calculate_tokens(content)

   # Optimized: Cache by file path and modification time
   token_count = self._token_cache.get(file_path, mtime)
   ```

2. **Selective Widget Updates**:
   ```python
   # Current: Rebuild entire message list
   self.remove_children()
   self.mount(*all_new_widgets)

   # Optimized: Update only changed widgets
   # (Requires tracking which messages changed)
   ```

3. **Lazy Loading**:
   ```python
   # Current: Load all context files on project load
   available_files = {
       "environments": fs.list_files(...)
   }

   # Optimized: Load on-demand when section expanded
   ```

4. **Path Normalization Cache**:
   ```python
   # Current: Normalize on every comparison
   abs_path = str(Path(event.file_path).resolve())

   # Optimized: Normalize once, store normalized paths
   ```

### Scalability Limits

**Current Design Works Well For:**
- Up to ~50 messages per session
- Up to ~100 context files
- File sizes under ~1 MB

**May Struggle With:**
- Sessions with 500+ messages (rebuild time)
- Large context files (token counting)
- Frequent rapid updates (rebuild queue)

---

## Future Development Directions

### Immediate Opportunities

1. **Anthropic API Integration**:
   - Add "Send Request" button
   - Stream responses into new assistant message
   - Handle tool calls

2. **Export/Import**:
   - Export session to shareable format
   - Import sessions from other projects
   - Copy/paste messages between sessions

3. **Search and Filter**:
   - Search message content
   - Filter by role
   - Find text in context files

4. **Keyboard Shortcuts**:
   - Ctrl+S: Save (though auto-save exists)
   - Ctrl+N: New message
   - Ctrl+D: Delete selected
   - Ctrl+↑/↓: Reorder selected

### Architectural Improvements

1. **Complete Virtual DOM** or **Remove RenderNode**:
   - Either fully implement reconciliation
   - Or remove unused RenderNode code

2. **Event Log**:
   - Store event history for undo/redo
   - Enable session replay for debugging

3. **Plugin System**:
   - Allow custom tools
   - Allow custom context file types
   - Allow custom message formatters

4. **Testing Infrastructure**:
   - Unit tests for reducer
   - Integration tests with mocked FileSystemAPI
   - UI tests with Textual's testing framework

---

## Textual-Specific Gotchas

### 1. Widget IDs Must Be Unique

**Problem:** Duplicate IDs cause `query_one()` to fail unpredictably.

**Solution:** Use hash-based IDs or ensure uniqueness via index:
```python
id=f"msg-content-{msg_idx}-{block_idx}"  # Unique across all messages
```

### 2. Event Handlers Must Match Convention

**Wrong:**
```python
def handle_button_press(self, event):  # Won't be called!
```

**Right:**
```python
def on_button_pressed(self, event: Button.Pressed):  # Will be called
```

### 3. Context Managers vs. Explicit Parents

**Works:**
```python
with Container():
    yield Label("Child")
```

**Also Works:**
```python
container = Container()
container.mount(Label("Child"))
yield container
```

**Choice:** Context managers are more readable, explicit mounting gives more control.

### 4. Widget Removal Timing

**Problem:** Can't modify widget tree during event handling.

**Wrong:**
```python
def on_button_pressed(self, event):
    self.remove_children()  # May cause errors
    self.mount(new_widgets)
```

**Right:**
```python
def on_button_pressed(self, event):
    self.call_after_refresh(self._rebuild)  # Schedule for later

def _rebuild(self):
    self.remove_children()
    self.mount(new_widgets)
```

### 5. CSS Specificity

Higher specificity wins:
```css
Button { color: red; }           /* Specificity: 1 */
.my-class { color: blue; }       /* Specificity: 10 */
#my-id { color: green; }         /* Specificity: 100 */
```

Result: Button with `id="my-id"` will be green, even if it has class `my-class`.

---

## Summary for AI Assistants

### Quick Reference

**File:** `anthropide.py` (single file, 2,506 lines)

**Key Sections:**
- Lines 39-146: Data structures (AppState, Message, etc.)
- Lines 152-290: Event classes (20+ event types)
- Lines 372-550: State loading/saving
- Lines 556-1111: Reducer (pure state updates)
- Lines 1452-1910: Reactive widgets (self-rebuilding)
- Lines 1918-2260: Textual screens (UI layer)
- Lines 2269-2486: CSS styling

**Architecture Pattern:** Redux-style unidirectional data flow
- Events describe what happened
- Reducer creates new state
- Widgets display current state

**Common Tasks:**
- Add event type: Define class → Handle in reducer → Dispatch from UI
- Modify state: Always go through reducer, never mutate directly
- Add UI section: Create widget builder → Add to rebuild → Update update_data()

**Debugging:**
- Print events in reducer to trace state changes
- Check `.anthropide/projects/{project}/current_session.json` for persistence
- Add prints in `_rebuild_content()` to debug rendering

**Performance:**
- Complete rebuilds on every change (may be slow for large sessions)
- Token counting uses tiktoken (fast for most files)
- Auto-save after every state change (I/O bound)

**Future Work:**
- API integration (Anthropic SDK already imported)
- Undo/redo (event log would enable this)
- Plugin system (custom tools, context types)
- Performance optimization (selective updates)

### When Working with This Codebase

1. **Always update state through events**: Never mutate AppState directly
2. **Add auto-save after state changes**: Call `save_session()` in reducer
3. **Use atomic rebuilds**: Follow the `remove_children() → mount()` pattern
4. **Generate stable IDs**: Use hashing or unique prefixes
5. **Normalize paths**: Always resolve to absolute paths for comparison
6. **Handle edge cases**: Check indices before list operations
7. **Test with real data**: Create test project with multiple messages and contexts

**Happy coding!** This architecture is clean, predictable, and ready for extension.
