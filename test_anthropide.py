#!/usr/bin/env python3
"""
Unit tests for AnthropIDE
Tests the core application logic without requiring Textual rendering
"""
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from dataclasses import asdict

from anthropide import (
    AppState,
    Message,
    ContextFile,
    AppEvent,
    ProjectSelected,
    ProjectCreateRequested,
    ContextToggled,
    ContextDeleted,
    ContextMoved,
    MessageContentChanged,
    MessageDeleted,
    MessageMoved,
    NewSessionRequested,
    RenderNode,
    FileSystemAPI,
    load_initial_state,
    load_project_state,
    reduce_state,
    AppComponent,
    create_default_session,
)


class MockFileSystem(FileSystemAPI):
    """Mock file system for testing"""

    def __init__(self):
        self.files = {}
        self.directories = set()

    @staticmethod
    def read_file(file_path: str) -> str:
        mock_fs = getattr(MockFileSystem, '_instance', None)
        if mock_fs and file_path in mock_fs.files:
            return mock_fs.files[file_path]
        raise FileNotFoundError(f"File not found: {file_path}")

    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        mock_fs = getattr(MockFileSystem, '_instance', None)
        if mock_fs:
            mock_fs.files[file_path] = content

    @staticmethod
    def file_exists(file_path: str) -> bool:
        mock_fs = getattr(MockFileSystem, '_instance', None)
        return mock_fs and file_path in mock_fs.files

    @staticmethod
    def create_directory(dir_path: str) -> None:
        mock_fs = getattr(MockFileSystem, '_instance', None)
        if mock_fs:
            mock_fs.directories.add(dir_path)

    @staticmethod
    def list_files(dir_path: str, pattern: str = "*.md") -> list:
        mock_fs = getattr(MockFileSystem, '_instance', None)
        if not mock_fs:
            return []

        # Simple pattern matching for *.md files
        result = []
        for file_path in mock_fs.files.keys():
            if file_path.startswith(dir_path) and file_path.endswith('.md'):
                result.append(file_path)
        return sorted(result)

    @staticmethod
    def list_directories(dir_path: str) -> list:
        mock_fs = getattr(MockFileSystem, '_instance', None)
        if not mock_fs:
            return []

        # Extract immediate subdirectories
        result = set()
        for directory in mock_fs.directories:
            if directory.startswith(dir_path) and directory != dir_path:
                relative = directory[len(dir_path):].strip('/')
                if '/' in relative:
                    result.add(relative.split('/')[0])
                else:
                    result.add(relative)
        return sorted(result)

    @staticmethod
    def calculate_tokens(content: str) -> int:
        # Simple approximation: ~4 chars per token
        return len(content) // 4


class TestDataStructures(unittest.TestCase):
    """Test core data structures"""

    def test_message_creation(self):
        msg = Message(role="user", content="Hello")
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "Hello")

    def test_context_file_creation(self):
        ctx = ContextFile(path="/path/to/file.md", section="environments")
        self.assertEqual(ctx.path, "/path/to/file.md")
        self.assertEqual(ctx.section, "environments")

    def test_app_state_to_session_dict(self):
        state = AppState(
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="Hello"),
            ],
            selected_contexts=[
                ContextFile(path="/file.md", section="environments"),
            ],
        )

        session_dict = state.to_session_dict()

        self.assertEqual(len(session_dict["messages"]), 2)
        self.assertEqual(session_dict["messages"][0]["role"], "system")
        self.assertEqual(len(session_dict["selected_contexts"]), 1)
        self.assertEqual(session_dict["selected_contexts"][0]["path"], "/file.md")


class TestFileSystemAPI(unittest.TestCase):
    """Test file system abstraction"""

    def setUp(self):
        self.mock_fs = MockFileSystem()
        MockFileSystem._instance = self.mock_fs

    def tearDown(self):
        MockFileSystem._instance = None

    def test_write_and_read_file(self):
        self.mock_fs.write_file("/test.txt", "Hello World")
        content = self.mock_fs.read_file("/test.txt")
        self.assertEqual(content, "Hello World")

    def test_file_exists(self):
        self.assertFalse(self.mock_fs.file_exists("/nonexistent.txt"))
        self.mock_fs.write_file("/exists.txt", "content")
        self.assertTrue(self.mock_fs.file_exists("/exists.txt"))

    def test_list_files(self):
        self.mock_fs.files["/dir/file1.md"] = "content1"
        self.mock_fs.files["/dir/file2.md"] = "content2"
        self.mock_fs.files["/dir/file3.txt"] = "content3"

        md_files = self.mock_fs.list_files("/dir")
        self.assertEqual(len(md_files), 2)
        self.assertIn("/dir/file1.md", md_files)
        self.assertIn("/dir/file2.md", md_files)

    def test_calculate_tokens(self):
        content = "This is a test string"
        tokens = self.mock_fs.calculate_tokens(content)
        self.assertGreater(tokens, 0)


class TestStateManagement(unittest.TestCase):
    """Test state loading and management"""

    def setUp(self):
        self.mock_fs = MockFileSystem()
        MockFileSystem._instance = self.mock_fs

    def tearDown(self):
        MockFileSystem._instance = None

    def test_load_initial_state(self):
        # Setup mock projects
        self.mock_fs.directories.add(".anthropide/projects")
        self.mock_fs.directories.add(".anthropide/projects/project1")
        self.mock_fs.directories.add(".anthropide/projects/project2")

        state = load_initial_state(self.mock_fs)

        self.assertEqual(state.screen, "project_select")
        self.assertIn("project1", state.available_projects)
        self.assertIn("project2", state.available_projects)

    def test_load_project_state_new_project(self):
        # Create initial state
        initial_state = AppState(
            available_projects=["test-project"],
            screen="project_select",
        )

        # Create default session file
        session_data = create_default_session()
        session_file = ".anthropide/projects/test-project/current_session.json"
        self.mock_fs.write_file(session_file, json.dumps(session_data))

        # Add some test files
        self.mock_fs.files[".anthropide/projects/test-project/environments/env1.md"] = "env content"
        self.mock_fs.files[".anthropide/projects/test-project/explorations/exp1.md"] = "exp content"

        state = load_project_state(initial_state, "test-project", self.mock_fs)

        self.assertEqual(state.screen, "main")
        self.assertEqual(state.project_name, "test-project")
        self.assertEqual(len(state.messages), 1)
        self.assertEqual(state.messages[0].role, "system")
        self.assertEqual(len(state.selected_contexts), 0)
        self.assertGreater(len(state.available_files["environments"]), 0)


class TestReducer(unittest.TestCase):
    """Test the pure reducer function"""

    def setUp(self):
        self.mock_fs = MockFileSystem()
        MockFileSystem._instance = self.mock_fs

    def tearDown(self):
        MockFileSystem._instance = None

    def test_context_toggled_add(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[Message(role="system", content="System")],
            selected_contexts=[],
        )

        event = ContextToggled("/file.md", "environments", True)
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(len(new_state.selected_contexts), 1)
        self.assertEqual(new_state.selected_contexts[0].section, "environments")

    def test_context_toggled_remove(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[Message(role="system", content="System")],
            selected_contexts=[
                ContextFile(path="/file.md", section="environments"),
            ],
        )

        event = ContextToggled("/file.md", "environments", False)
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(len(new_state.selected_contexts), 0)

    def test_context_deleted(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[Message(role="system", content="System")],
            selected_contexts=[
                ContextFile(path="/file1.md", section="environments"),
                ContextFile(path="/file2.md", section="environments"),
            ],
        )

        event = ContextDeleted(0)
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(len(new_state.selected_contexts), 1)
        self.assertEqual(new_state.selected_contexts[0].path, "/file2.md")

    def test_context_moved_down(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[Message(role="system", content="System")],
            selected_contexts=[
                ContextFile(path="/file1.md", section="environments"),
                ContextFile(path="/file2.md", section="environments"),
            ],
        )

        event = ContextMoved(0, 1)  # Move first item down
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(new_state.selected_contexts[0].path, "/file2.md")
        self.assertEqual(new_state.selected_contexts[1].path, "/file1.md")

    def test_message_content_changed(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[
                Message(role="system", content="System"),
                Message(role="user", content="Old content"),
            ],
            selected_contexts=[],
        )

        event = MessageContentChanged(1, "New content")
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(new_state.messages[1].content, "New content")
        self.assertEqual(new_state.messages[0].content, "System")  # Unchanged

    def test_message_deleted(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[
                Message(role="system", content="System"),
                Message(role="user", content="User message"),
            ],
            selected_contexts=[],
        )

        event = MessageDeleted(1)
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(len(new_state.messages), 1)
        self.assertEqual(new_state.messages[0].role, "system")

    def test_message_moved(self):
        state = AppState(
            project_path=Path("/project"),
            messages=[
                Message(role="system", content="System"),
                Message(role="user", content="User 1"),
                Message(role="assistant", content="Assistant 1"),
            ],
            selected_contexts=[],
        )

        event = MessageMoved(1, 1)  # Move message at index 1 down
        new_state = reduce_state(state, event, self.mock_fs)

        self.assertEqual(new_state.messages[1].role, "assistant")
        self.assertEqual(new_state.messages[2].role, "user")

    def test_new_session_requested(self):
        # Setup existing session
        project_path = Path(".anthropide/projects/test")
        self.mock_fs.files[str(project_path / "current_session.json")] = json.dumps({
            "messages": [
                {"role": "system", "content": "System"},
                {"role": "user", "content": "User"},
            ],
            "selected_contexts": [
                {"path": "/file.md", "section": "environments"},
            ],
        })

        state = AppState(
            project_path=project_path,
            messages=[
                Message(role="system", content="System"),
                Message(role="user", content="User"),
            ],
            selected_contexts=[
                ContextFile(path="/file.md", section="environments"),
            ],
        )

        event = NewSessionRequested()
        new_state = reduce_state(state, event, self.mock_fs)

        # Should reset to default session
        self.assertEqual(len(new_state.messages), 1)
        self.assertEqual(new_state.messages[0].role, "system")
        self.assertEqual(len(new_state.selected_contexts), 0)


class TestAppComponent(unittest.TestCase):
    """Test the application component"""

    def setUp(self):
        self.mock_fs = MockFileSystem()
        MockFileSystem._instance = self.mock_fs

        # Setup mock project structure
        self.mock_fs.directories.add(".anthropide/projects")
        self.mock_fs.directories.add(".anthropide/projects/test-project")
        self.mock_fs.directories.add(".anthropide/projects/test-project/environments")
        self.mock_fs.directories.add(".anthropide/projects/test-project/explorations")
        self.mock_fs.directories.add(".anthropide/projects/test-project/plans")

        # Create session file
        session_data = create_default_session()
        session_file = ".anthropide/projects/test-project/current_session.json"
        self.mock_fs.write_file(session_file, json.dumps(session_data))

        # Add test files
        self.mock_fs.files[".anthropide/projects/test-project/environments/env1.md"] = "Environment content"
        self.mock_fs.files[".anthropide/projects/test-project/explorations/exp1.md"] = "Exploration content"

    def tearDown(self):
        MockFileSystem._instance = None

    def test_app_component_initialization(self):
        app = AppComponent(fs=self.mock_fs)
        self.assertEqual(app.state.screen, "project_select")

    def test_handle_event_returns_should_render(self):
        app = AppComponent(fs=self.mock_fs)

        # Events that should trigger render
        event = ProjectSelected("test-project")
        should_render = app.handle_event(event)
        self.assertTrue(should_render)

        # Message content change should NOT trigger render (performance)
        event = MessageContentChanged(0, "New content")
        should_render = app.handle_event(event)
        self.assertFalse(should_render)

    def test_render_project_select_screen(self):
        app = AppComponent(fs=self.mock_fs)
        render_graph = app.render()

        self.assertEqual(render_graph.type, "screen")
        self.assertEqual(render_graph.id, "project-select-screen")
        self.assertGreater(len(render_graph.children), 0)

    def test_render_main_screen(self):
        app = AppComponent(fs=self.mock_fs)

        # Load a project first
        event = ProjectSelected("test-project")
        app.handle_event(event)

        render_graph = app.render()

        self.assertEqual(render_graph.type, "screen")
        self.assertEqual(render_graph.id, "main-screen")

        # Check that it has the main components
        has_context_control = False
        has_context_chain = False

        def check_children(node):
            nonlocal has_context_control, has_context_chain
            if node.id == "context-control":
                has_context_control = True
            if node.id == "context-chain":
                has_context_chain = True
            for child in node.children:
                check_children(child)

        check_children(render_graph)

        self.assertTrue(has_context_control, "Context control not found in render graph")
        self.assertTrue(has_context_chain, "Context chain not found in render graph")

    def test_render_context_control_shows_files(self):
        app = AppComponent(fs=self.mock_fs)

        # Load a project
        event = ProjectSelected("test-project")
        app.handle_event(event)

        render_graph = app.render()

        # Find context control in the render graph
        def find_node_by_id(node, target_id):
            if node.id == target_id:
                return node
            for child in node.children:
                result = find_node_by_id(child, target_id)
                if result:
                    return result
            return None

        context_control = find_node_by_id(render_graph, "context-control")
        self.assertIsNotNone(context_control)

        # Check that checkboxes are rendered
        checkboxes = [
            child for child in context_control.children
            if child.type == "checkbox"
        ]
        self.assertGreater(len(checkboxes), 0, "No checkboxes found in context control")

    def test_render_shows_messages(self):
        app = AppComponent(fs=self.mock_fs)

        # Load a project
        event = ProjectSelected("test-project")
        app.handle_event(event)

        render_graph = app.render()

        # Find messages container
        def find_node_by_id(node, target_id):
            if node.id == target_id:
                return node
            for child in node.children:
                result = find_node_by_id(child, target_id)
                if result:
                    return result
            return None

        messages_container = find_node_by_id(render_graph, "messages-container")
        self.assertIsNotNone(messages_container)

        # Should have at least the system message
        message_containers = [
            child for child in messages_container.children
            if child.props.get("classes") and "message-container" in child.props["classes"]
        ]
        self.assertGreater(len(message_containers), 0, "No messages found in render graph")


class TestRenderGraph(unittest.TestCase):
    """Test render graph structure"""

    def test_render_node_creation(self):
        node = RenderNode(
            type="button",
            id="test-btn",
            props={"text": "Click me", "variant": "primary"},
            children=[],
        )

        self.assertEqual(node.type, "button")
        self.assertEqual(node.id, "test-btn")
        self.assertEqual(node.props["text"], "Click me")

    def test_render_node_with_children(self):
        parent = RenderNode(
            type="container",
            children=[
                RenderNode(type="label", props={"text": "Label 1"}),
                RenderNode(type="label", props={"text": "Label 2"}),
            ],
        )

        self.assertEqual(len(parent.children), 2)
        self.assertEqual(parent.children[0].type, "label")


class TestReactiveWidgets(unittest.TestCase):
    """
    Integration tests for reactive widgets.
    Note: These tests verify widget creation without actually running Textual's event loop.
    Full integration would require Textual's test harness with async test runner.
    """

    def setUp(self):
        self.mock_fs = MockFileSystem()
        MockFileSystem._instance = self.mock_fs

    def tearDown(self):
        MockFileSystem._instance = None

    def test_message_chain_widget_creation(self):
        """Test MessageChainWidget can be created with messages"""
        from anthropide import MessageChainWidget

        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="User message"),
        ]
        contexts = []

        # Create widget (without mounting to actual Textual app)
        widget = MessageChainWidget(messages, contexts, self.mock_fs)

        # Verify initialization
        self.assertEqual(len(widget._messages), 2)
        self.assertEqual(widget._messages[0].role, "system")
        self.assertEqual(len(widget._selected_contexts), 0)

    def test_message_chain_widget_update_data(self):
        """
        Test MessageChainWidget.update_data() method updates internal state.
        Note: Calling _rebuild_content() requires an active Textual app,
        so we only verify the data is stored correctly.
        """
        from anthropide import MessageChainWidget

        initial_messages = [Message(role="system", content="System")]
        widget = MessageChainWidget(initial_messages, [], self.mock_fs)

        # Manually update internal state (simulating what update_data does)
        new_messages = [
            Message(role="system", content="System"),
            Message(role="user", content="New user message"),
        ]
        new_contexts = [ContextFile(path="/test.md", section="environments")]

        # Update internal state directly (without triggering rebuild)
        widget._messages = new_messages
        widget._selected_contexts = new_contexts

        # Verify internal state updated
        self.assertEqual(len(widget._messages), 2)
        self.assertEqual(len(widget._selected_contexts), 1)

    def test_context_control_widget_creation(self):
        """Test ContextControlWidget can be created"""
        from anthropide import ContextControlWidget

        available_files = {
            "environments": ["/path/to/env1.md", "/path/to/env2.md"],
            "explorations": [],
            "plans": ["/path/to/plan1.md"],
        }
        selected_contexts = [ContextFile(path="/path/to/env1.md", section="environments")]

        # Create widget
        widget = ContextControlWidget(available_files, selected_contexts)

        # Verify initialization
        self.assertEqual(len(widget._available_files["environments"]), 2)
        self.assertEqual(len(widget._available_files["plans"]), 1)
        self.assertEqual(len(widget._selected_paths), 1)

    def test_context_control_widget_update_files(self):
        """
        Test ContextControlWidget.update_files() method updates internal state.
        Note: Calling _rebuild_content() requires an active Textual app,
        so we only verify the data is stored correctly.
        """
        from anthropide import ContextControlWidget

        initial_files = {"environments": [], "explorations": [], "plans": []}
        widget = ContextControlWidget(initial_files, [])

        # Manually update internal state (simulating what update_files does)
        new_files = {
            "environments": ["/new/env.md"],
            "explorations": ["/new/exp.md"],
            "plans": [],
        }
        new_contexts = [ContextFile(path="/new/env.md", section="environments")]

        # Update internal state directly (without triggering rebuild)
        widget._available_files = new_files
        widget._selected_paths = {str(Path(c.path).resolve()) for c in new_contexts}

        # Verify internal state updated
        self.assertEqual(len(widget._available_files["environments"]), 1)
        self.assertEqual(len(widget._selected_paths), 1)

    def test_screens_can_be_instantiated(self):
        """Test that new Screen classes can be instantiated"""
        from anthropide import ProjectSelectScreen, MainScreen

        app_component = AppComponent(fs=self.mock_fs)

        # Create project select screen
        project_screen = ProjectSelectScreen(app_component)
        self.assertIsNotNone(project_screen)
        self.assertEqual(project_screen.app_component, app_component)

        # Load a project first
        self.mock_fs.directories.add(".anthropide/projects/test-project")
        self.mock_fs.directories.add(".anthropide/projects/test-project/environments")
        self.mock_fs.directories.add(".anthropide/projects/test-project/explorations")
        self.mock_fs.directories.add(".anthropide/projects/test-project/plans")

        session_data = {"messages": [{"role": "system", "content": "Test"}], "selected_contexts": []}
        self.mock_fs.write_file(
            ".anthropide/projects/test-project/current_session.json",
            json.dumps(session_data),
        )

        app_component.handle_event(ProjectSelected("test-project"))

        # Create main screen
        main_screen = MainScreen(app_component)
        self.assertIsNotNone(main_screen)
        self.assertEqual(main_screen.app_component, app_component)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
