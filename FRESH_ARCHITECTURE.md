# Fresh Architecture Design for AnthropIDE

## Core Philosophy

**Simple, Direct, Textual-Native**

- No virtual DOM, no reconciliation, no complex state management
- Widgets are views that display data and emit events
- Screens own data and orchestrate updates
- Everything rebuilds when data changes (Textual is fast enough)

## Layer 1: Data Model (Pure Python)

```python
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional
import json
import uuid
from datetime import datetime

@dataclass
class ContentBlock:
    """A single content block in a message"""
    type: str = "text"  # "text", "image", "tool_use", etc.
    text: str = ""

@dataclass
class Message:
    """A single message in the conversation"""
    role: str  # "user", "assistant"
    content: List[ContentBlock] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def user_message(cls, text: str = "") -> 'Message':
        return cls(role="user", content=[ContentBlock(text=text)])

    @classmethod
    def assistant_message(cls, text: str = "") -> 'Message':
        return cls(role="assistant", content=[ContentBlock(text=text)])

@dataclass
class SystemBlock:
    """A system prompt block"""
    text: str
    cache_control: Optional[Dict] = None  # {"type": "ephemeral"}
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Tool:
    """A tool definition"""
    name: str
    description: str
    input_schema: Dict
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ContextFile:
    """A selected context file"""
    path: str
    section: str  # "environments", "explorations", "plans"

@dataclass
class Session:
    """Complete session data - matches Anthropic API format"""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 8192
    system_blocks: List[SystemBlock] = field(default_factory=list)
    tools: List[Tool] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    selected_contexts: List[ContextFile] = field(default_factory=list)

    def to_anthropic_format(self) -> Dict:
        """Convert to Anthropic API request format"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": block.text,
                    **({"cache_control": block.cache_control} if block.cache_control else {}),
                }
                for block in self.system_blocks
            ],
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in self.tools
            ],
            "messages": [
                {
                    "role": msg.role,
                    "content": [
                        {"type": block.type, "text": block.text}
                        for block in msg.content
                    ],
                }
                for msg in self.messages
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Load from dictionary"""
        return cls(
            model=data.get("model", "claude-sonnet-4-5-20250929"),
            max_tokens=data.get("max_tokens", 8192),
            system_blocks=[
                SystemBlock(
                    text=block.get("text", ""),
                    cache_control=block.get("cache_control"),
                    id=block.get("id", str(uuid.uuid4())),
                )
                for block in data.get("system", [])
            ],
            tools=[
                Tool(
                    name=tool.get("name", ""),
                    description=tool.get("description", ""),
                    input_schema=tool.get("input_schema", {}),
                    id=tool.get("id", str(uuid.uuid4())),
                )
                for tool in data.get("tools", [])
            ],
            messages=[
                Message(
                    role=msg.get("role", "user"),
                    content=[
                        ContentBlock(
                            type=block.get("type", "text"),
                            text=block.get("text", ""),
                        )
                        for block in msg.get("content", [])
                    ],
                    id=msg.get("id", str(uuid.uuid4())),
                )
                for msg in data.get("messages", [])
            ],
            selected_contexts=[
                ContextFile(path=ctx["path"], section=ctx["section"])
                for ctx in data.get("selected_contexts", [])
            ],
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": block.text,
                    "id": block.id,
                    **({"cache_control": block.cache_control} if block.cache_control else {}),
                }
                for block in self.system_blocks
            ],
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "id": tool.id,
                }
                for tool in self.tools
            ],
            "messages": [
                {
                    "role": msg.role,
                    "content": [
                        {"type": block.type, "text": block.text}
                        for block in msg.content
                    ],
                    "id": msg.id,
                }
                for msg in self.messages
            ],
            "selected_contexts": [
                {"path": ctx.path, "section": ctx.section}
                for ctx in self.selected_contexts
            ],
        }

    @classmethod
    def load(cls, path: Path) -> 'Session':
        """Load session from file"""
        if not path.exists():
            return cls.default()

        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save(self, path: Path):
        """Save session to file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def backup(self, path: Path):
        """Create timestamped backup"""
        if path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = path.with_suffix(f".json.{timestamp}")
            with open(path) as f:
                content = f.read()
            with open(backup_path, 'w') as f:
                f.write(content)

    @classmethod
    def default(cls) -> 'Session':
        """Create default session"""
        return cls(
            system_blocks=[
                SystemBlock(
                    text="You are a helpful AI assistant. You provide clear, accurate, and concise responses.",
                ),
            ],
            tools=[
                Tool(
                    name="Read",
                    description="Reads a file from the filesystem",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute path to the file",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="Edit",
                    description="Performs exact string replacements in files",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "old_string": {"type": "string"},
                            "new_string": {"type": "string"},
                        },
                        "required": ["file_path", "old_string", "new_string"],
                    },
                ),
            ],
        )

@dataclass
class Project:
    """A project with its directory structure"""
    name: str
    path: Path

    def __post_init__(self):
        """Ensure directory structure exists"""
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "environments").mkdir(exist_ok=True)
        (self.path / "explorations").mkdir(exist_ok=True)
        (self.path / "plans").mkdir(exist_ok=True)

    def session_path(self) -> Path:
        return self.path / "current_session.json"

    def load_session(self) -> Session:
        return Session.load(self.session_path())

    def save_session(self, session: Session):
        session.save(self.session_path())

    def list_context_files(self) -> Dict[str, List[Path]]:
        """List all context files by section"""
        return {
            "environments": sorted((self.path / "environments").glob("*.md")),
            "explorations": sorted((self.path / "explorations").glob("*.md")),
            "plans": sorted((self.path / "plans").glob("*.md")),
        }

    @classmethod
    def list_projects(cls, base_dir: Path) -> List[str]:
        """List all project names"""
        base_dir.mkdir(parents=True, exist_ok=True)
        return [d.name for d in base_dir.iterdir() if d.is_dir()]

    @classmethod
    def create(cls, name: str, base_dir: Path) -> 'Project':
        """Create a new project"""
        project = cls(name=name, path=base_dir / name)
        session = Session.default()
        project.save_session(session)
        return project
```

## Layer 2: Widget Components (Dumb Views)

Widgets receive data and render it. They emit events when the user interacts.

```python
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Label, Select, TextArea, Static
from textual.message import Message as TextualMessage

# Custom messages for widget events
class DeleteItem(TextualMessage):
    """Request to delete an item"""
    def __init__(self, item_id: str):
        super().__init__()
        self.item_id = item_id

class MoveItem(TextualMessage):
    """Request to move an item"""
    def __init__(self, item_id: str, direction: int):
        super().__init__()
        self.item_id = item_id
        self.direction = direction  # -1 for up, +1 for down

class ItemChanged(TextualMessage):
    """An item's data changed"""
    def __init__(self, item_id: str, field: str, value: any):
        super().__init__()
        self.item_id = item_id
        self.field = field
        self.value = value


# Message Widget
class MessageWidget(Vertical):
    """Display a single message with edit controls"""

    DEFAULT_CSS = """
    MessageWidget {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }

    MessageWidget .message-header {
        height: 3;
    }

    MessageWidget TextArea {
        height: 10;
        margin-top: 1;
    }
    """

    def __init__(self, message: Message, index: int, total: int):
        super().__init__()
        self.message = message
        self.index = index
        self.total = total

    def compose(self) -> ComposeResult:
        # Header with role and controls
        with Horizontal(classes="message-header"):
            yield Select(
                [("user", "user"), ("assistant", "assistant")],
                value=self.message.role,
                id=f"role-{self.message.id}",
            )
            if self.index > 0:
                yield Button("↑", id=f"up-{self.message.id}", classes="btn-small")
            if self.index < self.total - 1:
                yield Button("↓", id=f"down-{self.message.id}", classes="btn-small")
            yield Button("Delete", variant="error", id=f"delete-{self.message.id}")

        # Content (for now, just first block - can expand later)
        content = self.message.content[0].text if self.message.content else ""
        yield TextArea(content, language="markdown", id=f"content-{self.message.id}")

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses"""
        if event.button.id.startswith("delete-"):
            self.post_message(DeleteItem(self.message.id))
            event.stop()
        elif event.button.id.startswith("up-"):
            self.post_message(MoveItem(self.message.id, -1))
            event.stop()
        elif event.button.id.startswith("down-"):
            self.post_message(MoveItem(self.message.id, +1))
            event.stop()

    def on_select_changed(self, event: Select.Changed):
        """Handle role change"""
        if event.select.id.startswith("role-"):
            self.post_message(ItemChanged(self.message.id, "role", event.value))
            event.stop()

    def on_text_area_changed(self, event: TextArea.Changed):
        """Handle content edit"""
        if event.text_area.id.startswith("content-"):
            self.post_message(ItemChanged(self.message.id, "content", event.text_area.text))
            event.stop()


# Context File Widget
class ContextFileWidget(Horizontal):
    """Display a context file in the sidebar"""

    DEFAULT_CSS = """
    ContextFileWidget {
        height: 3;
        padding: 0 1;
    }

    ContextFileWidget Checkbox {
        width: 1fr;
    }
    """

    def __init__(self, file_path: Path, section: str, selected: bool):
        super().__init__()
        self.file_path = file_path
        self.section = section
        self.is_selected = selected

    def compose(self) -> ComposeResult:
        yield Checkbox(
            self.file_path.name,
            value=self.is_selected,
            id=f"ctx-{self.section}-{self.file_path.stem}",
        )


# System Block Widget
class SystemBlockWidget(Vertical):
    """Display a system prompt block"""

    DEFAULT_CSS = """
    SystemBlockWidget {
        border: solid $warning;
        padding: 1;
        margin: 1 0;
    }

    SystemBlockWidget .block-header {
        height: 3;
    }

    SystemBlockWidget TextArea {
        height: 8;
        margin-top: 1;
    }
    """

    def __init__(self, block: SystemBlock, index: int, total: int):
        super().__init__()
        self.block = block
        self.index = index
        self.total = total

    def compose(self) -> ComposeResult:
        with Horizontal(classes="block-header"):
            yield Label(f"System Block {self.index + 1}")
            yield Checkbox(
                "Enable caching",
                value=self.block.cache_control is not None,
                id=f"cache-{self.block.id}",
            )
            if self.index > 0:
                yield Button("↑", id=f"up-{self.block.id}", classes="btn-small")
            if self.index < self.total - 1:
                yield Button("↓", id=f"down-{self.block.id}", classes="btn-small")
            yield Button("Delete", variant="error", id=f"delete-{self.block.id}")

        yield TextArea(self.block.text, language="markdown", id=f"text-{self.block.id}")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id.startswith("delete-"):
            self.post_message(DeleteItem(self.block.id))
            event.stop()
        elif event.button.id.startswith("up-"):
            self.post_message(MoveItem(self.block.id, -1))
            event.stop()
        elif event.button.id.startswith("down-"):
            self.post_message(MoveItem(self.block.id, +1))
            event.stop()

    def on_checkbox_changed(self, event: Checkbox.Changed):
        if event.checkbox.id.startswith("cache-"):
            cache = {"type": "ephemeral"} if event.value else None
            self.post_message(ItemChanged(self.block.id, "cache_control", cache))
            event.stop()

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id.startswith("text-"):
            self.post_message(ItemChanged(self.block.id, "text", event.text_area.text))
            event.stop()


# Tool Widget
class ToolWidget(Vertical):
    """Display a tool definition"""

    DEFAULT_CSS = """
    ToolWidget {
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }

    ToolWidget .tool-header {
        height: 3;
    }

    ToolWidget Input {
        margin: 1 0;
    }

    ToolWidget TextArea {
        height: 8;
    }
    """

    def __init__(self, tool: Tool):
        super().__init__()
        self.tool = tool

    def compose(self) -> ComposeResult:
        with Horizontal(classes="tool-header"):
            yield Label(f"Tool: {self.tool.name}")
            yield Button("Delete", variant="error", id=f"delete-{self.tool.id}")

        yield Label("Name:")
        yield Input(value=self.tool.name, id=f"name-{self.tool.id}")

        yield Label("Description:")
        yield Input(value=self.tool.description, id=f"desc-{self.tool.id}")

        yield Label("Input Schema (JSON):")
        yield TextArea(
            json.dumps(self.tool.input_schema, indent=2),
            language="json",
            id=f"schema-{self.tool.id}",
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id.startswith("delete-"):
            self.post_message(DeleteItem(self.tool.id))
            event.stop()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id.startswith("name-"):
            self.post_message(ItemChanged(self.tool.id, "name", event.value))
            event.stop()
        elif event.input.id.startswith("desc-"):
            self.post_message(ItemChanged(self.tool.id, "description", event.value))
            event.stop()

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.id.startswith("schema-"):
            try:
                schema = json.loads(event.text_area.text)
                self.post_message(ItemChanged(self.tool.id, "input_schema", schema))
            except json.JSONDecodeError:
                pass  # Invalid JSON, don't update
            event.stop()
```

## Layer 3: Container Widgets (Smart Containers)

Container widgets own a list of items and rebuild when the list changes.

```python
class MessageList(VerticalScroll):
    """Container for all messages"""

    DEFAULT_CSS = """
    MessageList {
        height: 1fr;
        border: solid $primary;
    }
    """

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        for idx, message in enumerate(self.session.messages):
            yield MessageWidget(message, idx, len(self.session.messages))

    def refresh_messages(self, session: Session):
        """Rebuild message list"""
        self.session = session
        self.remove_children()
        for idx, message in enumerate(self.session.messages):
            self.mount(MessageWidget(message, idx, len(self.session.messages)))


class SystemBlockList(VerticalScroll):
    """Container for system blocks"""

    DEFAULT_CSS = """
    SystemBlockList {
        height: auto;
        max-height: 30;
        border: solid $warning;
    }
    """

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        yield Label("System Prompt", classes="section-header")
        yield Button("+ Add Block", variant="success", id="add-system-block")

        for idx, block in enumerate(self.session.system_blocks):
            yield SystemBlockWidget(block, idx, len(self.session.system_blocks))

    def refresh_blocks(self, session: Session):
        """Rebuild system blocks list"""
        self.session = session
        self.remove_children()

        # Re-add header and button
        self.mount(Label("System Prompt", classes="section-header"))
        self.mount(Button("+ Add Block", variant="success", id="add-system-block"))

        # Add blocks
        for idx, block in enumerate(self.session.system_blocks):
            self.mount(SystemBlockWidget(block, idx, len(self.session.system_blocks)))


class ToolList(VerticalScroll):
    """Container for tools"""

    DEFAULT_CSS = """
    ToolList {
        height: auto;
        max-height: 30;
        border: solid $accent;
    }
    """

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        yield Label("Tools", classes="section-header")
        yield Button("+ Add Tool", variant="success", id="add-tool")

        for tool in self.session.tools:
            yield ToolWidget(tool)

    def refresh_tools(self, session: Session):
        """Rebuild tools list"""
        self.session = session
        self.remove_children()

        self.mount(Label("Tools", classes="section-header"))
        self.mount(Button("+ Add Tool", variant="success", id="add-tool"))

        for tool in self.session.tools:
            self.mount(ToolWidget(tool))


class ContextFileList(VerticalScroll):
    """Sidebar showing available context files"""

    DEFAULT_CSS = """
    ContextFileList {
        width: 30%;
        height: 100%;
        border-right: solid $primary;
    }
    """

    def __init__(self, project: Project, session: Session):
        super().__init__()
        self.project = project
        self.session = session

    def compose(self) -> ComposeResult:
        yield Label("Context Files", classes="section-header")

        selected_paths = {ctx.path for ctx in self.session.selected_contexts}

        for section in ["environments", "explorations", "plans"]:
            yield Label(section.capitalize(), classes="subsection-header")

            files = self.project.list_context_files()[section]
            for file_path in files:
                selected = str(file_path) in selected_paths
                yield ContextFileWidget(file_path, section, selected)

    def refresh_files(self, session: Session):
        """Rebuild file list (when selection changes)"""
        self.session = session
        self.remove_children()

        yield Label("Context Files", classes="section-header")

        selected_paths = {ctx.path for ctx in self.session.selected_contexts}

        for section in ["environments", "explorations", "plans"]:
            self.mount(Label(section.capitalize(), classes="subsection-header"))

            files = self.project.list_context_files()[section]
            for file_path in files:
                selected = str(file_path) in selected_paths
                self.mount(ContextFileWidget(file_path, section, selected))
```

## Layer 4: Screens (Orchestrators)

Screens own the data model, handle events, and update widgets.

```python
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer

class ProjectSelectScreen(Screen):
    """Screen for selecting or creating a project"""

    BINDINGS = [Binding("ctrl+c", "quit", "Quit")]

    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="project-select"):
            yield Label("Select a Project", classes="title")

            projects = Project.list_projects(self.base_dir)
            if projects:
                for project_name in projects:
                    yield Button(project_name, id=f"project-{project_name}")
            else:
                yield Label("No projects found. Create one below.")

            yield Label("Create New Project")
            yield Input(placeholder="Project name", id="new-project-input")
            yield Button("Create", variant="success", id="create-project-btn")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id.startswith("project-"):
            project_name = event.button.id.replace("project-", "")
            self.load_project(project_name)
        elif event.button.id == "create-project-btn":
            input_widget = self.query_one("#new-project-input", Input)
            if input_widget.value:
                self.create_project(input_widget.value.strip())

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "new-project-input" and event.value:
            self.create_project(event.value.strip())

    def create_project(self, name: str):
        """Create a new project and open it"""
        project = Project.create(name, self.base_dir)
        self.app.push_screen(MainScreen(project))

    def load_project(self, name: str):
        """Load an existing project"""
        project = Project(name=name, path=self.base_dir / name)
        self.app.push_screen(MainScreen(project))

    def action_quit(self):
        self.app.exit()


class MainScreen(Screen):
    """Main editing screen"""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.session = project.load_session()

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            # Left sidebar
            yield ContextFileList(self.project, self.session)

            # Right side - main editor
            with VerticalScroll(id="editor"):
                # API Config
                with Container(id="api-config"):
                    yield Label("API Configuration", classes="section-header")
                    yield Label("Model:")
                    yield Select(
                        [
                            ("Claude Sonnet 4.5", "claude-sonnet-4-5-20250929"),
                            ("Claude Sonnet 3.5", "claude-3-5-sonnet-20241022"),
                        ],
                        value=self.session.model,
                        id="model-select",
                    )
                    yield Label("Max Tokens:")
                    yield Input(value=str(self.session.max_tokens), id="max-tokens-input")

                # System Blocks
                yield SystemBlockList(self.session)

                # Tools
                yield ToolList(self.session)

                # Messages
                with Vertical(id="messages-section"):
                    with Horizontal():
                        yield Label("Messages", classes="section-header")
                        yield Button("New Session", variant="warning", id="new-session")
                        yield Button("+ Add Message", variant="success", id="add-message")
                    yield MessageList(self.session)

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses"""
        if event.button.id == "new-session":
            self.new_session()
        elif event.button.id == "add-message":
            self.add_message()
        elif event.button.id == "add-system-block":
            self.add_system_block()
        elif event.button.id == "add-tool":
            self.add_tool()

    def on_delete_item(self, event: DeleteItem):
        """Handle delete requests from widgets"""
        # Find and remove the item
        if any(msg.id == event.item_id for msg in self.session.messages):
            self.session.messages = [m for m in self.session.messages if m.id != event.item_id]
            self.save_and_refresh_messages()

        elif any(block.id == event.item_id for block in self.session.system_blocks):
            self.session.system_blocks = [b for b in self.session.system_blocks if b.id != event.item_id]
            self.save_and_refresh_system_blocks()

        elif any(tool.id == event.item_id for tool in self.session.tools):
            self.session.tools = [t for t in self.session.tools if t.id != event.item_id]
            self.save_and_refresh_tools()

    def on_move_item(self, event: MoveItem):
        """Handle move requests"""
        # Find the item in messages
        for i, msg in enumerate(self.session.messages):
            if msg.id == event.item_id:
                new_idx = i + event.direction
                if 0 <= new_idx < len(self.session.messages):
                    self.session.messages[i], self.session.messages[new_idx] = (
                        self.session.messages[new_idx],
                        self.session.messages[i],
                    )
                    self.save_and_refresh_messages()
                return

        # Find the item in system blocks
        for i, block in enumerate(self.session.system_blocks):
            if block.id == event.item_id:
                new_idx = i + event.direction
                if 0 <= new_idx < len(self.session.system_blocks):
                    self.session.system_blocks[i], self.session.system_blocks[new_idx] = (
                        self.session.system_blocks[new_idx],
                        self.session.system_blocks[i],
                    )
                    self.save_and_refresh_system_blocks()
                return

    def on_item_changed(self, event: ItemChanged):
        """Handle item field changes"""
        # Find and update the item
        for msg in self.session.messages:
            if msg.id == event.item_id:
                if event.field == "role":
                    msg.role = event.value
                elif event.field == "content":
                    if msg.content:
                        msg.content[0].text = event.value
                    else:
                        msg.content = [ContentBlock(text=event.value)]
                self.save()
                return

        for block in self.session.system_blocks:
            if block.id == event.item_id:
                if event.field == "text":
                    block.text = event.value
                elif event.field == "cache_control":
                    block.cache_control = event.value
                self.save()
                return

        for tool in self.session.tools:
            if tool.id == event.item_id:
                if event.field == "name":
                    tool.name = event.value
                elif event.field == "description":
                    tool.description = event.value
                elif event.field == "input_schema":
                    tool.input_schema = event.value
                self.save()
                return

    def on_checkbox_changed(self, event: Checkbox.Changed):
        """Handle context file selection"""
        if event.checkbox.id.startswith("ctx-"):
            # Parse: ctx-{section}-{filename}
            parts = event.checkbox.id.split("-", 2)
            if len(parts) == 3:
                section = parts[1]
                filename_stem = parts[2]

                # Find the file
                files = self.project.list_context_files()[section]
                for file_path in files:
                    if file_path.stem == filename_stem:
                        if event.value:
                            # Add to selected contexts
                            if not any(ctx.path == str(file_path) for ctx in self.session.selected_contexts):
                                self.session.selected_contexts.append(
                                    ContextFile(path=str(file_path), section=section),
                                )
                        else:
                            # Remove from selected contexts
                            self.session.selected_contexts = [
                                ctx for ctx in self.session.selected_contexts
                                if ctx.path != str(file_path)
                            ]
                        self.save()
                        return

    def on_select_changed(self, event: Select.Changed):
        """Handle model selection"""
        if event.select.id == "model-select":
            self.session.model = str(event.value)
            self.save()

    def on_input_changed(self, event: Input.Changed):
        """Handle max tokens change"""
        if event.input.id == "max-tokens-input":
            try:
                self.session.max_tokens = int(event.value)
                self.save()
            except ValueError:
                pass

    # Helper methods
    def save(self):
        """Save session"""
        self.project.save_session(self.session)

    def save_and_refresh_messages(self):
        """Save and rebuild message list"""
        self.save()
        self.query_one(MessageList).refresh_messages(self.session)

    def save_and_refresh_system_blocks(self):
        """Save and rebuild system blocks"""
        self.save()
        self.query_one(SystemBlockList).refresh_blocks(self.session)

    def save_and_refresh_tools(self):
        """Save and rebuild tools"""
        self.save()
        self.query_one(ToolList).refresh_tools(self.session)

    def add_message(self):
        """Add a new message"""
        self.session.messages.append(Message.user_message())
        self.save_and_refresh_messages()

    def add_system_block(self):
        """Add a new system block"""
        self.session.system_blocks.append(SystemBlock(text="New system prompt"))
        self.save_and_refresh_system_blocks()

    def add_tool(self):
        """Add a new tool"""
        self.session.tools.append(
            Tool(
                name="NewTool",
                description="Tool description",
                input_schema={"type": "object", "properties": {}, "required": []},
            ),
        )
        self.save_and_refresh_tools()

    def new_session(self):
        """Start a new session"""
        self.session.backup(self.project.session_path())
        self.session = Session.default()
        self.save()

        # Refresh all widgets
        self.query_one(MessageList).refresh_messages(self.session)
        self.query_one(SystemBlockList).refresh_blocks(self.session)
        self.query_one(ToolList).refresh_tools(self.session)

    def action_save(self):
        """Manual save action"""
        self.save()
        self.notify("Session saved")

    def action_quit(self):
        self.app.exit()


# Main App
class AnthropIDEApp(App):
    """Main application"""

    CSS = """
    /* Add CSS styling here */
    .section-header {
        text-style: bold;
        background: $primary;
        padding: 0 1;
        margin: 1 0;
    }

    .subsection-header {
        text-style: bold;
        padding: 0 1;
        margin: 1 0 0 2;
    }

    .btn-small {
        width: 5;
        margin: 0 1;
    }
    """

    def on_mount(self):
        base_dir = Path(".anthropide/projects")
        self.push_screen(ProjectSelectScreen(base_dir))


def main():
    app = AnthropIDEApp()
    app.run()


if __name__ == "__main__":
    main()
```

## Key Benefits

### 1. Simplicity
- **No reducer pattern**: Direct state manipulation
- **No virtual DOM**: Widgets rebuild when data changes
- **No reconciliation**: Just `remove_children()` + `mount()`
- **No complex flags**: No `_is_rebuilding`, `_pending_rebuild`, generation counters

### 2. Textual-Native
- **compose() for structure**: Static layout defined once
- **Custom messages for events**: Widgets post messages that bubble up
- **Direct widget updates**: Screens handle messages and refresh widgets
- **Uses Textual patterns**: Not fighting the framework

### 3. Extensibility
- **Plugin-style widgets**: Easy to add new widget types
- **Custom messages**: New features can define new message types
- **Data-driven**: Add new fields to data model, update widgets
- **Clear separation**: Data → Widget → Screen layers

### 4. Maintainability
- **Single responsibility**: Each widget does one thing
- **Clear data flow**: Event → Update data → Refresh widget
- **No hidden state**: All data in Session object
- **Easy to debug**: Print data, inspect widgets

### 5. Testability
- **Data model is pure**: Test load/save/validation
- **Widgets are composable**: Test widget rendering
- **Events are simple**: Test event handling
- **No framework dependencies in data layer**: Mock-free testing

## Migration Strategy

1. **Phase 1: Implement new data model** (Session, Project, Message, etc.)
2. **Phase 2: Implement simple widgets** (MessageWidget, ContextFileWidget)
3. **Phase 3: Implement container widgets** (MessageList, SystemBlockList)
4. **Phase 4: Implement screens** (ProjectSelectScreen, MainScreen)
5. **Phase 5: Test and refine**
6. **Phase 6: Delete old code**

## What Makes This Different

| Current Architecture | Fresh Architecture |
|---------------------|-------------------|
| Redux-style reducer | Direct state updates |
| Virtual DOM (RenderNode) | Real widgets only |
| Reconciliation engine | Simple rebuilds |
| Complex rebuild logic | `remove_children()` + `mount()` |
| Generation counters | No ID conflicts (proper separation) |
| UUID tracking through reducer | IDs only for event routing |
| 18+ event classes | Simple Textual messages |
| AppComponent layer | No unnecessary layers |

## Extensibility Examples

### Adding a New Field to Messages

1. **Update data model**:
```python
@dataclass
class Message:
    role: str
    content: List[ContentBlock]
    metadata: Dict = field(default_factory=dict)  # NEW
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

2. **Update widget** (if you want to display it):
```python
class MessageWidget(Vertical):
    def compose(self):
        # ... existing code ...
        if self.message.metadata:
            yield Label(f"Metadata: {self.message.metadata}")
```

3. **Done!** No reducer changes, no event classes, no reconciliation.

### Adding a Plugin System

```python
# Define plugin interface
class EditorPlugin:
    def get_name(self) -> str:
        """Plugin name"""

    def get_widget(self, session: Session) -> Widget:
        """Return widget to display"""

    def on_message(self, message: TextualMessage):
        """Handle custom messages"""

# Load plugins
class MainScreen(Screen):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project
        self.session = project.load_session()
        self.plugins = self.load_plugins()

    def compose(self):
        # ... existing code ...

        # Add plugin widgets
        for plugin in self.plugins:
            yield plugin.get_widget(self.session)
```

### Adding API Integration

```python
# Add to Session
@dataclass
class Session:
    # ... existing fields ...
    api_client: Optional[Any] = None  # Anthropic client

    async def send_request(self) -> Message:
        """Send request to Anthropic API"""
        response = await self.api_client.messages.create(
            **self.to_anthropic_format(),
        )
        # Convert response to Message
        return Message.assistant_message(response.content[0].text)

# Add to MainScreen
class MainScreen(Screen):
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "send-request":
            response = await self.session.send_request()
            self.session.messages.append(response)
            self.save_and_refresh_messages()
```

## Summary

This architecture is:
- **Simple**: No unnecessary abstractions
- **Direct**: Straight line from event to update
- **Textual-native**: Uses framework as designed
- **Extensible**: Easy to add features
- **Maintainable**: Clear responsibilities
- **Testable**: Pure data model
- **Debuggable**: Inspect data and widgets

It eliminates all the bugs in the current system by removing the complex reconciliation logic and embracing Textual's natural patterns.
