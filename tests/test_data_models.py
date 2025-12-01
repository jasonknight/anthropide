"""
Comprehensive unit tests for Pydantic data models in lib/data_models.py.

Tests cover:
- Valid data creation for all models
- Invalid data rejection and validation errors
- Edge cases: empty lists, None values, boundary values
- Session validation logic including role alternation and tool references
- Project name validation
- ContentBlock and SystemBlock type-specific validation
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from lib.data_models import (
    ProjectSettings,
    Project,
    SystemBlock,
    ToolSchema,
    ContentBlock,
    Message,
    Session,
    AgentConfig,
    SkillConfig,
    TestMatch,
    TestResponse,
    TestSequenceItem,
    TestCase,
    TestConfig,
    UIState,
)


# ==================== ProjectSettings Tests ====================

class TestProjectSettings:
    """Test ProjectSettings model."""

    def test_valid_project_settings_with_defaults(self):
        """Test creating ProjectSettings with default values."""
        settings = ProjectSettings()
        assert settings.max_session_backups == 20
        assert settings.auto_save is True
        assert settings.default_model == "claude-sonnet-4-5-20250929"

    def test_valid_project_settings_with_custom_values(self):
        """Test creating ProjectSettings with custom values."""
        settings = ProjectSettings(
            max_session_backups=50,
            auto_save=False,
            default_model="claude-3-opus-20240229",
        )
        assert settings.max_session_backups == 50
        assert settings.auto_save is False
        assert settings.default_model == "claude-3-opus-20240229"

    def test_project_settings_accepts_zero_backups(self):
        """Test that zero backups is allowed as edge case."""
        settings = ProjectSettings(max_session_backups=0)
        assert settings.max_session_backups == 0

    def test_project_settings_accepts_negative_backups(self):
        """Test that negative backups are allowed (no validation on this field)."""
        settings = ProjectSettings(max_session_backups=-1)
        assert settings.max_session_backups == -1


# ==================== Project Tests ====================

class TestProject:
    """Test Project model."""

    def test_valid_project_creation(self):
        """Test creating a valid project."""
        now = datetime.now()
        project = Project(
            name="test-project",
            description="Test project",
            created=now,
            modified=now,
        )
        assert project.name == "test-project"
        assert project.description == "Test project"
        assert project.created == now
        assert project.modified == now
        assert isinstance(project.settings, ProjectSettings)

    def test_valid_project_without_description(self):
        """Test creating project without optional description."""
        now = datetime.now()
        project = Project(
            name="test-project",
            created=now,
            modified=now,
        )
        assert project.name == "test-project"
        assert project.description is None

    def test_valid_project_name_with_hyphens(self):
        """Test project name with hyphens."""
        now = datetime.now()
        project = Project(name="test-project-123", created=now, modified=now)
        assert project.name == "test-project-123"

    def test_valid_project_name_with_underscores(self):
        """Test project name with underscores."""
        now = datetime.now()
        project = Project(name="test_project_123", created=now, modified=now)
        assert project.name == "test_project_123"

    def test_valid_project_name_alphanumeric(self):
        """Test project name with only alphanumeric characters."""
        now = datetime.now()
        project = Project(name="TestProject123", created=now, modified=now)
        assert project.name == "TestProject123"

    def test_valid_project_name_max_length(self):
        """Test project name at maximum length boundary (100 chars)."""
        now = datetime.now()
        name = "a" * 100
        project = Project(name=name, created=now, modified=now)
        assert project.name == name
        assert len(project.name) == 100

    def test_invalid_project_name_empty(self):
        """Test that empty project name raises ValueError."""
        now = datetime.now()
        with pytest.raises(ValidationError) as exc_info:
            Project(name="", created=now, modified=now)
        assert "Project name cannot be empty" in str(exc_info.value)

    def test_invalid_project_name_too_long(self):
        """Test that project name over 100 characters raises ValueError."""
        now = datetime.now()
        name = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            Project(name=name, created=now, modified=now)
        assert "Project name must be 100 characters or less" in str(exc_info.value)

    def test_invalid_project_name_with_spaces(self):
        """Test that project name with spaces raises ValueError."""
        now = datetime.now()
        with pytest.raises(ValidationError) as exc_info:
            Project(name="test project", created=now, modified=now)
        assert "alphanumeric characters, hyphens, and underscores" in str(exc_info.value)

    def test_invalid_project_name_with_special_chars(self):
        """Test that project name with special characters raises ValueError."""
        now = datetime.now()
        invalid_names = ["test@project", "test.project", "test!project", "test/project"]
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                Project(name=invalid_name, created=now, modified=now)
            assert "alphanumeric characters, hyphens, and underscores" in str(exc_info.value)

    def test_project_with_custom_settings(self):
        """Test creating project with custom settings."""
        now = datetime.now()
        settings = ProjectSettings(max_session_backups=10, auto_save=False)
        project = Project(
            name="test-project",
            created=now,
            modified=now,
            settings=settings,
        )
        assert project.settings.max_session_backups == 10
        assert project.settings.auto_save is False


# ==================== SystemBlock Tests ====================

class TestSystemBlock:
    """Test SystemBlock model."""

    def test_valid_system_block_text(self):
        """Test creating valid text system block."""
        block = SystemBlock(type="text", text="System prompt")
        assert block.type == "text"
        assert block.text == "System prompt"
        assert block.source is None

    def test_valid_system_block_text_with_cache_control(self):
        """Test creating text system block with cache control."""
        block = SystemBlock(
            type="text",
            text="System prompt",
            cache_control={"type": "ephemeral"},
        )
        assert block.type == "text"
        assert block.text == "System prompt"
        assert block.cache_control == {"type": "ephemeral"}

    def test_valid_system_block_image(self):
        """Test creating valid image system block."""
        source = {
            "type": "base64",
            "media_type": "image/png",
            "data": "base64data",
        }
        block = SystemBlock(type="image", source=source)
        assert block.type == "image"
        assert block.source == source
        assert block.text is None

    def test_valid_system_block_empty_text(self):
        """Test that empty string text is invalid for text type."""
        with pytest.raises(ValidationError) as exc_info:
            SystemBlock(type="text", text="")
        assert "text field is required when type is 'text'" in str(exc_info.value)

    def test_invalid_system_block_text_missing_text(self):
        """Test that text type requires text field."""
        with pytest.raises(ValidationError) as exc_info:
            SystemBlock(type="text")
        assert "text field is required when type is 'text'" in str(exc_info.value)

    def test_invalid_system_block_image_missing_source(self):
        """Test that image type requires source field."""
        with pytest.raises(ValidationError) as exc_info:
            SystemBlock(type="image")
        assert "source field is required when type is 'image'" in str(exc_info.value)

    def test_invalid_system_block_text_with_none(self):
        """Test that None text is invalid for text type."""
        with pytest.raises(ValidationError) as exc_info:
            SystemBlock(type="text", text=None)
        assert "text field is required when type is 'text'" in str(exc_info.value)


# ==================== ToolSchema Tests ====================

class TestToolSchema:
    """Test ToolSchema model."""

    def test_valid_tool_schema(self):
        """Test creating valid tool schema."""
        schema = ToolSchema(
            name="calculator",
            description="Performs calculations",
            input_schema={"type": "object", "properties": {}},
        )
        assert schema.name == "calculator"
        assert schema.description == "Performs calculations"
        assert schema.input_schema == {"type": "object", "properties": {}}

    def test_valid_tool_schema_complex_input(self):
        """Test tool schema with complex input schema."""
        input_schema = {
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
                "precision": {"type": "integer"},
            },
            "required": ["expression"],
        }
        schema = ToolSchema(
            name="calculator",
            description="Performs calculations",
            input_schema=input_schema,
        )
        assert schema.input_schema == input_schema

    def test_valid_tool_schema_empty_input(self):
        """Test tool schema with empty input schema."""
        schema = ToolSchema(
            name="tool",
            description="Description",
            input_schema={},
        )
        assert schema.input_schema == {}


# ==================== ContentBlock Tests ====================

class TestContentBlock:
    """Test ContentBlock model."""

    def test_valid_content_block_text(self):
        """Test creating valid text content block."""
        block = ContentBlock(type="text", text="Hello world")
        assert block.type == "text"
        assert block.text == "Hello world"

    def test_valid_content_block_text_empty_string(self):
        """Test that empty string is invalid for text type."""
        # Note: The validator checks for None, but empty string should pass
        # However, looking at the code, it checks `self.text is None`
        # Empty string is not None, so this should be valid
        block = ContentBlock(type="text", text="")
        assert block.text == ""

    def test_valid_content_block_image(self):
        """Test creating valid image content block."""
        source = {
            "type": "base64",
            "media_type": "image/png",
            "data": "base64data",
        }
        block = ContentBlock(type="image", source=source)
        assert block.type == "image"
        assert block.source == source

    def test_valid_content_block_tool_use(self):
        """Test creating valid tool_use content block."""
        block = ContentBlock(
            type="tool_use",
            id="tool_123",
            name="calculator",
            input={"expression": "2+2"},
        )
        assert block.type == "tool_use"
        assert block.id == "tool_123"
        assert block.name == "calculator"
        assert block.input == {"expression": "2+2"}

    def test_valid_content_block_tool_use_empty_input(self):
        """Test tool_use with empty dict input is valid."""
        block = ContentBlock(
            type="tool_use",
            id="tool_123",
            name="calculator",
            input={},
        )
        assert block.input == {}

    def test_valid_content_block_tool_result_string(self):
        """Test creating valid tool_result with string content."""
        block = ContentBlock(
            type="tool_result",
            tool_use_id="tool_123",
            content="Result: 4",
        )
        assert block.type == "tool_result"
        assert block.tool_use_id == "tool_123"
        assert block.content == "Result: 4"
        assert block.is_error is None

    def test_valid_content_block_tool_result_list(self):
        """Test creating valid tool_result with list content."""
        content = [{"type": "text", "text": "Result"}]
        block = ContentBlock(
            type="tool_result",
            tool_use_id="tool_123",
            content=content,
        )
        assert block.content == content

    def test_valid_content_block_tool_result_with_error(self):
        """Test tool_result with is_error flag."""
        block = ContentBlock(
            type="tool_result",
            tool_use_id="tool_123",
            content="Error occurred",
            is_error=True,
        )
        assert block.is_error is True

    def test_valid_content_block_tool_result_empty_string(self):
        """Test tool_result with empty string content is valid."""
        block = ContentBlock(
            type="tool_result",
            tool_use_id="tool_123",
            content="",
        )
        assert block.content == ""

    def test_invalid_content_block_text_missing_text(self):
        """Test that text type requires text field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="text")
        assert "text field is required when type is 'text'" in str(exc_info.value)

    def test_invalid_content_block_image_missing_source(self):
        """Test that image type requires source field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="image")
        assert "source field is required when type is 'image'" in str(exc_info.value)

    def test_invalid_content_block_tool_use_missing_id(self):
        """Test that tool_use requires id field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="tool_use", name="calc", input={})
        assert "id field is required when type is 'tool_use'" in str(exc_info.value)

    def test_invalid_content_block_tool_use_missing_name(self):
        """Test that tool_use requires name field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="tool_use", id="tool_123", input={})
        assert "name field is required when type is 'tool_use'" in str(exc_info.value)

    def test_invalid_content_block_tool_use_missing_input(self):
        """Test that tool_use requires input field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="tool_use", id="tool_123", name="calc")
        assert "input field is required when type is 'tool_use'" in str(exc_info.value)

    def test_invalid_content_block_tool_result_missing_tool_use_id(self):
        """Test that tool_result requires tool_use_id field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="tool_result", content="result")
        assert "tool_use_id field is required when type is 'tool_result'" in str(exc_info.value)

    def test_invalid_content_block_tool_result_missing_content(self):
        """Test that tool_result requires content field."""
        with pytest.raises(ValidationError) as exc_info:
            ContentBlock(type="tool_result", tool_use_id="tool_123")
        assert "content field is required when type is 'tool_result'" in str(exc_info.value)


# ==================== Message Tests ====================

class TestMessage:
    """Test Message model."""

    def test_valid_message_user(self):
        """Test creating valid user message."""
        content = [ContentBlock(type="text", text="Hello")]
        message = Message(role="user", content=content)
        assert message.role == "user"
        assert len(message.content) == 1
        assert message.content[0].text == "Hello"

    def test_valid_message_assistant(self):
        """Test creating valid assistant message."""
        content = [ContentBlock(type="text", text="Hi there")]
        message = Message(role="assistant", content=content)
        assert message.role == "assistant"
        assert len(message.content) == 1

    def test_valid_message_multiple_content_blocks(self):
        """Test message with multiple content blocks."""
        content = [
            ContentBlock(type="text", text="Part 1"),
            ContentBlock(type="text", text="Part 2"),
        ]
        message = Message(role="user", content=content)
        assert len(message.content) == 2

    def test_valid_message_empty_content_list(self):
        """Test message with empty content list."""
        message = Message(role="user", content=[])
        assert message.content == []

    def test_valid_message_with_tool_use(self):
        """Test message with tool_use block."""
        content = [
            ContentBlock(
                type="tool_use",
                id="tool_123",
                name="calc",
                input={},
            ),
        ]
        message = Message(role="assistant", content=content)
        assert len(message.content) == 1
        assert message.content[0].type == "tool_use"


# ==================== Session Tests ====================

class TestSession:
    """Test Session model and validation logic."""

    def test_valid_session_minimal(self):
        """Test creating minimal valid session."""
        session = Session(model="claude-sonnet-4-5-20250929")
        assert session.model == "claude-sonnet-4-5-20250929"
        assert session.max_tokens == 8192
        assert session.temperature == 1.0
        assert session.system == []
        assert session.tools == []
        assert session.messages == []

    def test_valid_session_with_all_fields(self):
        """Test creating session with all fields populated."""
        system = [SystemBlock(type="text", text="You are helpful")]
        tools = [
            ToolSchema(
                name="calc",
                description="Calculator",
                input_schema={},
            ),
        ]
        messages = [
            Message(
                role="user",
                content=[ContentBlock(type="text", text="Hello")],
            ),
        ]
        session = Session(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.5,
            system=system,
            tools=tools,
            messages=messages,
        )
        assert session.model == "claude-3-opus-20240229"
        assert session.max_tokens == 4096
        assert session.temperature == 0.5
        assert len(session.system) == 1
        assert len(session.tools) == 1
        assert len(session.messages) == 1

    def test_valid_session_temperature_boundary_zero(self):
        """Test session with temperature at lower boundary (0)."""
        session = Session(model="test", temperature=0.0)
        session.validate()
        assert session.temperature == 0.0

    def test_valid_session_temperature_boundary_one(self):
        """Test session with temperature at upper boundary (1)."""
        session = Session(model="test", temperature=1.0)
        session.validate()
        assert session.temperature == 1.0

    def test_valid_session_temperature_none(self):
        """Test session with temperature set to None."""
        session = Session(model="test", temperature=None)
        session.validate()
        assert session.temperature is None

    def test_valid_session_max_tokens_boundary_min(self):
        """Test session with max_tokens at minimum boundary (1)."""
        session = Session(model="test", max_tokens=1)
        session.validate()
        assert session.max_tokens == 1

    def test_valid_session_max_tokens_boundary_max(self):
        """Test session with max_tokens at maximum boundary (200000)."""
        session = Session(model="test", max_tokens=200000)
        session.validate()
        assert session.max_tokens == 200000

    def test_valid_session_alternating_roles(self):
        """Test session with properly alternating user/assistant roles."""
        messages = [
            Message(role="user", content=[ContentBlock(type="text", text="Q1")]),
            Message(role="assistant", content=[ContentBlock(type="text", text="A1")]),
            Message(role="user", content=[ContentBlock(type="text", text="Q2")]),
            Message(role="assistant", content=[ContentBlock(type="text", text="A2")]),
        ]
        session = Session(model="test", messages=messages)
        session.validate()

    def test_valid_session_consecutive_user_messages(self):
        """Test that consecutive user messages are allowed (for tool results)."""
        messages = [
            Message(role="user", content=[ContentBlock(type="text", text="Q1")]),
            Message(role="user", content=[ContentBlock(type="text", text="Q2")]),
        ]
        session = Session(model="test", messages=messages)
        session.validate()

    def test_valid_session_tool_use_and_result(self):
        """Test session with tool_use in assistant and tool_result in user message."""
        tools = [
            ToolSchema(
                name="calc",
                description="Calculator",
                input_schema={},
            ),
        ]
        messages = [
            Message(role="user", content=[ContentBlock(type="text", text="Calculate")]),
            Message(
                role="assistant",
                content=[
                    ContentBlock(
                        type="tool_use",
                        id="tool_123",
                        name="calc",
                        input={"expr": "2+2"},
                    ),
                ],
            ),
            Message(
                role="user",
                content=[
                    ContentBlock(
                        type="tool_result",
                        tool_use_id="tool_123",
                        content="4",
                    ),
                ],
            ),
        ]
        session = Session(model="test", tools=tools, messages=messages)
        session.validate()

    def test_invalid_session_max_tokens_zero(self):
        """Test that max_tokens of 0 raises ValueError."""
        session = Session(model="test", max_tokens=0)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "max_tokens must be between 1 and 200000" in str(exc_info.value)

    def test_invalid_session_max_tokens_negative(self):
        """Test that negative max_tokens raises ValueError."""
        session = Session(model="test", max_tokens=-1)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "max_tokens must be between 1 and 200000" in str(exc_info.value)

    def test_invalid_session_max_tokens_too_large(self):
        """Test that max_tokens over 200000 raises ValueError."""
        session = Session(model="test", max_tokens=200001)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "max_tokens must be between 1 and 200000" in str(exc_info.value)

    def test_invalid_session_temperature_negative(self):
        """Test that negative temperature raises ValueError."""
        session = Session(model="test", temperature=-0.1)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "temperature must be between 0 and 1" in str(exc_info.value)

    def test_invalid_session_temperature_too_large(self):
        """Test that temperature over 1 raises ValueError."""
        session = Session(model="test", temperature=1.1)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "temperature must be between 0 and 1" in str(exc_info.value)

    def test_invalid_session_consecutive_assistant_messages(self):
        """Test that consecutive assistant messages raise ValueError."""
        messages = [
            Message(role="user", content=[ContentBlock(type="text", text="Q1")]),
            Message(role="assistant", content=[ContentBlock(type="text", text="A1")]),
            Message(role="assistant", content=[ContentBlock(type="text", text="A2")]),
        ]
        session = Session(model="test", messages=messages)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "consecutive assistant messages not allowed" in str(exc_info.value)

    def test_invalid_session_tool_result_missing_tool_use(self):
        """Test that tool_result without corresponding tool_use raises ValueError."""
        messages = [
            Message(
                role="user",
                content=[
                    ContentBlock(
                        type="tool_result",
                        tool_use_id="nonexistent",
                        content="result",
                    ),
                ],
            ),
        ]
        session = Session(model="test", messages=messages)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "tool_result references unknown tool_use_id" in str(exc_info.value)

    def test_invalid_session_tool_use_unknown_tool(self):
        """Test that tool_use referencing unknown tool raises ValueError."""
        messages = [
            Message(
                role="assistant",
                content=[
                    ContentBlock(
                        type="tool_use",
                        id="tool_123",
                        name="unknown_tool",
                        input={},
                    ),
                ],
            ),
        ]
        session = Session(model="test", tools=[], messages=messages)
        with pytest.raises(ValueError) as exc_info:
            session.validate()
        assert "tool_use references unknown tool 'unknown_tool'" in str(exc_info.value)

    def test_invalid_session_multiple_tool_results_same_id(self):
        """Test validation with multiple tool_results for same tool_use_id."""
        tools = [
            ToolSchema(
                name="calc",
                description="Calculator",
                input_schema={},
            ),
        ]
        messages = [
            Message(
                role="assistant",
                content=[
                    ContentBlock(
                        type="tool_use",
                        id="tool_123",
                        name="calc",
                        input={},
                    ),
                ],
            ),
            Message(
                role="user",
                content=[
                    ContentBlock(
                        type="tool_result",
                        tool_use_id="tool_123",
                        content="result1",
                    ),
                    ContentBlock(
                        type="tool_result",
                        tool_use_id="tool_123",
                        content="result2",
                    ),
                ],
            ),
        ]
        session = Session(model="test", tools=tools, messages=messages)
        # This should be valid - multiple results for same tool_use_id are allowed
        session.validate()

    def test_session_validate_empty_messages(self):
        """Test validation with empty messages list."""
        session = Session(model="test", messages=[])
        session.validate()

    def test_session_validate_tool_use_before_definition(self):
        """Test tool_use appearing before tool is defined in session."""
        # Tool is in the session tools list, so this should be valid
        tools = [
            ToolSchema(
                name="calc",
                description="Calculator",
                input_schema={},
            ),
        ]
        messages = [
            Message(
                role="assistant",
                content=[
                    ContentBlock(
                        type="tool_use",
                        id="tool_123",
                        name="calc",
                        input={},
                    ),
                ],
            ),
        ]
        session = Session(model="test", tools=tools, messages=messages)
        session.validate()


# ==================== AgentConfig Tests ====================

class TestAgentConfig:
    """Test AgentConfig model."""

    def test_valid_agent_config_minimal(self):
        """Test creating minimal valid agent config."""
        agent = AgentConfig(
            name="test-agent",
            description="Test agent",
            prompt="Agent prompt",
        )
        assert agent.name == "test-agent"
        assert agent.description == "Test agent"
        assert agent.model == "inherit"
        assert agent.tools == []
        assert agent.skills == []
        assert agent.color == "blue"
        assert agent.prompt == "Agent prompt"

    def test_valid_agent_config_with_all_fields(self):
        """Test creating agent config with all fields."""
        agent = AgentConfig(
            name="test-agent",
            description="Test agent",
            model="claude-3-opus-20240229",
            tools=["tool1", "tool2"],
            skills=["skill1"],
            color="red",
            prompt="Agent prompt",
        )
        assert agent.model == "claude-3-opus-20240229"
        assert agent.tools == ["tool1", "tool2"]
        assert agent.skills == ["skill1"]
        assert agent.color == "red"

    def test_valid_agent_config_empty_lists(self):
        """Test agent config with empty tools and skills lists."""
        agent = AgentConfig(
            name="test-agent",
            description="Test",
            tools=[],
            skills=[],
            prompt="Prompt",
        )
        assert agent.tools == []
        assert agent.skills == []


# ==================== SkillConfig Tests ====================

class TestSkillConfig:
    """Test SkillConfig model."""

    def test_valid_skill_config_minimal(self):
        """Test creating minimal valid skill config."""
        skill = SkillConfig(
            name="test-skill",
            description="Test skill",
            content="Skill content",
        )
        assert skill.name == "test-skill"
        assert skill.description == "Test skill"
        assert skill.version == "1.0.0"
        assert skill.author is None
        assert skill.content == "Skill content"

    def test_valid_skill_config_with_all_fields(self):
        """Test creating skill config with all fields."""
        skill = SkillConfig(
            name="test-skill",
            description="Test skill",
            version="2.0.0",
            author="Test Author",
            content="Skill content",
        )
        assert skill.version == "2.0.0"
        assert skill.author == "Test Author"

    def test_valid_skill_config_empty_content(self):
        """Test skill config with empty content string."""
        skill = SkillConfig(
            name="test-skill",
            description="Test",
            content="",
        )
        assert skill.content == ""


# ==================== TestMatch Tests ====================

class TestTestMatch:
    """Test TestMatch model."""

    def test_valid_test_match_regex(self):
        """Test creating valid regex test match."""
        match = TestMatch(
            type="regex",
            path="messages[0].content",
            pattern="hello.*world",
        )
        assert match.type == "regex"
        assert match.path == "messages[0].content"
        assert match.pattern == "hello.*world"

    def test_valid_test_match_contains(self):
        """Test creating valid contains test match."""
        match = TestMatch(
            type="contains",
            path="messages[0].role",
            value="user",
        )
        assert match.type == "contains"
        assert match.path == "messages[0].role"
        assert match.value == "user"

    def test_valid_test_match_contains_with_none_value(self):
        """Test that contains with None value is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            TestMatch(
                type="contains",
                path="path",
                value=None,
            )
        assert "value field is required when type is 'contains'" in str(exc_info.value)

    def test_invalid_test_match_regex_missing_pattern(self):
        """Test that regex type requires pattern field."""
        with pytest.raises(ValidationError) as exc_info:
            TestMatch(type="regex", path="path")
        assert "pattern field is required when type is 'regex'" in str(exc_info.value)

    def test_invalid_test_match_contains_missing_value(self):
        """Test that contains type requires value field."""
        with pytest.raises(ValidationError) as exc_info:
            TestMatch(type="contains", path="path")
        assert "value field is required when type is 'contains'" in str(exc_info.value)


# ==================== TestResponse Tests ====================

class TestTestResponse:
    """Test TestResponse model."""

    def test_valid_test_response_user(self):
        """Test creating valid user test response."""
        content = [ContentBlock(type="text", text="Response")]
        response = TestResponse(role="user", content=content)
        assert response.role == "user"
        assert len(response.content) == 1

    def test_valid_test_response_assistant(self):
        """Test creating valid assistant test response."""
        content = [ContentBlock(type="text", text="Response")]
        response = TestResponse(role="assistant", content=content)
        assert response.role == "assistant"

    def test_valid_test_response_empty_content(self):
        """Test test response with empty content list."""
        response = TestResponse(role="user", content=[])
        assert response.content == []


# ==================== TestSequenceItem Tests ====================

class TestTestSequenceItem:
    """Test TestSequenceItem model."""

    def test_valid_test_sequence_item_minimal(self):
        """Test creating minimal valid test sequence item."""
        match = TestMatch(type="regex", path="path", pattern="pattern")
        response = TestResponse(
            role="user",
            content=[ContentBlock(type="text", text="Response")],
        )
        item = TestSequenceItem(match=match, response=response)
        assert item.match == match
        assert item.response == response
        assert item.tool_behavior == "mock"
        assert item.tool_results is None

    def test_valid_test_sequence_item_with_tool_behavior(self):
        """Test test sequence item with different tool behaviors."""
        match = TestMatch(type="regex", path="path", pattern="pattern")
        response = TestResponse(
            role="user",
            content=[ContentBlock(type="text", text="Response")],
        )

        for behavior in ["mock", "execute", "skip"]:
            item = TestSequenceItem(
                match=match,
                response=response,
                tool_behavior=behavior,
            )
            assert item.tool_behavior == behavior

    def test_valid_test_sequence_item_with_tool_results(self):
        """Test test sequence item with tool results."""
        match = TestMatch(type="regex", path="path", pattern="pattern")
        response = TestResponse(
            role="user",
            content=[ContentBlock(type="text", text="Response")],
        )
        tool_results = {"tool_123": "result"}
        item = TestSequenceItem(
            match=match,
            response=response,
            tool_results=tool_results,
        )
        assert item.tool_results == tool_results


# ==================== TestCase Tests ====================

class TestTestCase:
    """Test TestCase model."""

    def test_valid_test_case(self):
        """Test creating valid test case."""
        match = TestMatch(type="regex", path="path", pattern="pattern")
        response = TestResponse(
            role="user",
            content=[ContentBlock(type="text", text="Response")],
        )
        sequence_item = TestSequenceItem(match=match, response=response)

        test_case = TestCase(
            name="test-case-1",
            sequence=[sequence_item],
        )
        assert test_case.name == "test-case-1"
        assert len(test_case.sequence) == 1

    def test_valid_test_case_multiple_sequence_items(self):
        """Test test case with multiple sequence items."""
        items = []
        for i in range(3):
            match = TestMatch(type="regex", path="path", pattern=f"pattern{i}")
            response = TestResponse(
                role="user",
                content=[ContentBlock(type="text", text=f"Response{i}")],
            )
            items.append(TestSequenceItem(match=match, response=response))

        test_case = TestCase(name="multi-step", sequence=items)
        assert len(test_case.sequence) == 3

    def test_valid_test_case_empty_sequence(self):
        """Test test case with empty sequence."""
        test_case = TestCase(name="empty-test", sequence=[])
        assert test_case.sequence == []


# ==================== TestConfig Tests ====================

class TestTestConfig:
    """Test TestConfig model."""

    def test_valid_test_config(self):
        """Test creating valid test config."""
        match = TestMatch(type="regex", path="path", pattern="pattern")
        response = TestResponse(
            role="user",
            content=[ContentBlock(type="text", text="Response")],
        )
        sequence_item = TestSequenceItem(match=match, response=response)
        test_case = TestCase(name="test1", sequence=[sequence_item])

        config = TestConfig(tests=[test_case])
        assert len(config.tests) == 1

    def test_valid_test_config_multiple_tests(self):
        """Test test config with multiple test cases."""
        test_cases = []
        for i in range(3):
            match = TestMatch(type="regex", path="path", pattern=f"pattern{i}")
            response = TestResponse(
                role="user",
                content=[ContentBlock(type="text", text=f"Response{i}")],
            )
            sequence_item = TestSequenceItem(match=match, response=response)
            test_cases.append(TestCase(name=f"test{i}", sequence=[sequence_item]))

        config = TestConfig(tests=test_cases)
        assert len(config.tests) == 3

    def test_valid_test_config_empty_tests(self):
        """Test test config with empty tests list."""
        config = TestConfig(tests=[])
        assert config.tests == []


# ==================== UIState Tests ====================

class TestUIState:
    """Test UIState model."""

    def test_valid_ui_state_minimal(self):
        """Test creating minimal valid UI state."""
        now = datetime.now()
        state = UIState(last_modified=now)
        assert state.version == "1.0"
        assert state.selected_project is None
        assert state.ui == {}
        assert state.last_modified == now

    def test_valid_ui_state_with_all_fields(self):
        """Test creating UI state with all fields."""
        now = datetime.now()
        ui_data = {"theme": "dark", "sidebar_width": 250}
        state = UIState(
            version="2.0",
            selected_project="my-project",
            ui=ui_data,
            last_modified=now,
        )
        assert state.version == "2.0"
        assert state.selected_project == "my-project"
        assert state.ui == ui_data

    def test_valid_ui_state_empty_ui_dict(self):
        """Test UI state with empty ui dictionary."""
        now = datetime.now()
        state = UIState(last_modified=now, ui={})
        assert state.ui == {}

    def test_valid_ui_state_none_selected_project(self):
        """Test UI state with None as selected_project."""
        now = datetime.now()
        state = UIState(last_modified=now, selected_project=None)
        assert state.selected_project is None
