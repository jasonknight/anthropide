"""
Tests for AgentManager implementation.

This test suite provides comprehensive coverage for agent loading, parsing,
saving, deleting, validation, and error handling. Tests use fixture files in
tests/fixtures/agents/ to verify behavior with various agent formats.

Tests mock SkillManager and ToolManager to simulate valid/invalid tool and
skill references.
"""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml
from pydantic import ValidationError

from lib.agent_manager import (
    AgentManager,
    AgentError,
    AgentNotFoundError,
    AgentLoadError,
    AgentValidationError,
    VALID_MODELS,
)
from lib.data_models import AgentConfig
from lib.file_operations import FileReadError, FileWriteError, FileDeleteError


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "agents"


@pytest.fixture
def temp_project_dir(tmp_path):
    """
    Create a temporary project directory for testing.

    Returns:
        Path: Path to temporary project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def mock_skill_manager():
    """
    Create a mock SkillManager for testing.

    Returns:
        Mock: Mock SkillManager with list_skills method
    """
    mock_manager = Mock()
    mock_manager.list_skills.return_value = [
        'code-analysis',
        'testing',
        'debugging',
        'documentation',
    ]
    return mock_manager


@pytest.fixture
def mock_tool_manager():
    """
    Create a mock ToolManager for testing.

    Returns:
        Mock: Mock ToolManager with list_tools method
    """
    mock_manager = Mock()
    mock_manager.list_tools.return_value = [
        'Read',
        'Write',
        'Grep',
        'Glob',
        'Bash',
        'Edit',
    ]
    return mock_manager


@pytest.fixture
def agent_manager(temp_project_dir, mock_skill_manager, mock_tool_manager):
    """
    Create an AgentManager instance for testing.

    Args:
        temp_project_dir: Temporary project directory fixture
        mock_skill_manager: Mock SkillManager fixture
        mock_tool_manager: Mock ToolManager fixture

    Returns:
        AgentManager: Configured AgentManager instance
    """
    return AgentManager(
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    )


@pytest.fixture
def populated_agent_manager(
    temp_project_dir,
    mock_skill_manager,
    mock_tool_manager,
):
    """
    Create an AgentManager with pre-populated valid agents.

    Args:
        temp_project_dir: Temporary project directory fixture
        mock_skill_manager: Mock SkillManager fixture
        mock_tool_manager: Mock ToolManager fixture

    Returns:
        AgentManager: AgentManager with valid test agents
    """
    manager = AgentManager(
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    )
    agents_dir = manager.agents_dir

    # Copy valid fixture files to the agents directory
    valid_files = [
        "valid_agent.md",
        "minimal_agent.md",
    ]

    for filename in valid_files:
        src = FIXTURES_DIR / filename
        dst = agents_dir / filename
        shutil.copy(src, dst)

    return manager


@pytest.fixture
def sample_agent_config():
    """
    Create a sample AgentConfig for testing.

    Returns:
        AgentConfig: Sample agent configuration
    """
    return AgentConfig(
        name="test_agent",
        description="A test agent for unit testing",
        model="inherit",
        tools=["Read", "Write"],
        skills=["testing"],
        color="green",
        prompt="# Test Agent\n\nThis is test content.",
    )


class TestAgentManagerInit:
    """Tests for AgentManager initialization."""

    def test_init_creates_agents_directory(
        self,
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    ):
        """Test that __init__ creates agents directory if it doesn't exist."""
        # Ensure agents directory doesn't exist
        agents_dir = temp_project_dir / "agents"
        assert not agents_dir.exists()

        # Initialize manager
        manager = AgentManager(
            temp_project_dir,
            mock_skill_manager,
            mock_tool_manager,
        )

        # Verify agents directory was created
        assert manager.agents_dir.exists()
        assert manager.agents_dir.is_dir()
        assert manager.agents_dir == agents_dir

    def test_init_with_existing_agents_directory(
        self,
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    ):
        """Test initialization with pre-existing agents directory."""
        # Create agents directory
        agents_dir = temp_project_dir / "agents"
        agents_dir.mkdir()

        # Initialize manager
        manager = AgentManager(
            temp_project_dir,
            mock_skill_manager,
            mock_tool_manager,
        )

        # Verify directory is used
        assert manager.agents_dir == agents_dir
        assert manager.agents_dir.exists()

    def test_init_sets_project_path(
        self,
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    ):
        """Test that __init__ sets project_path correctly."""
        manager = AgentManager(
            temp_project_dir,
            mock_skill_manager,
            mock_tool_manager,
        )

        assert manager.project_path == temp_project_dir
        assert isinstance(manager.project_path, Path)

    def test_init_sets_managers(
        self,
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    ):
        """Test that __init__ sets skill and tool managers."""
        manager = AgentManager(
            temp_project_dir,
            mock_skill_manager,
            mock_tool_manager,
        )

        assert manager.skill_manager is mock_skill_manager
        assert manager.tool_manager is mock_tool_manager

    def test_init_initializes_empty_cache(
        self,
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    ):
        """Test that __init__ initializes an empty agent cache."""
        manager = AgentManager(
            temp_project_dir,
            mock_skill_manager,
            mock_tool_manager,
        )

        assert hasattr(manager, '_agent_cache')
        assert isinstance(manager._agent_cache, dict)
        assert len(manager._agent_cache) == 0

    def test_init_with_path_string(
        self,
        temp_project_dir,
        mock_skill_manager,
        mock_tool_manager,
    ):
        """Test initialization with string path instead of Path object."""
        manager = AgentManager(
            str(temp_project_dir),
            mock_skill_manager,
            mock_tool_manager,
        )

        assert manager.project_path == temp_project_dir
        assert isinstance(manager.project_path, Path)


class TestParseAgent:
    """Tests for parse_agent method."""

    def test_parse_valid_agent(self, agent_manager):
        """Test parsing a valid agent with all fields."""
        content = """---
name: test_agent
description: |
  Test description with multiple lines.
  Second line here.
model: inherit
tools: Read, Write, Grep
skills: testing, debugging
color: blue
---

# Test Content

This is the markdown content.
"""

        agent = agent_manager.parse_agent(content)

        assert agent.name == "test_agent"
        assert "Test description" in agent.description
        assert agent.model == "inherit"
        assert agent.tools == ["Read", "Write", "Grep"]
        assert agent.skills == ["testing", "debugging"]
        assert agent.color == "blue"
        assert "# Test Content" in agent.prompt
        assert "This is the markdown content." in agent.prompt

    def test_parse_minimal_agent(self, agent_manager):
        """Test parsing an agent with only required fields."""
        content = """---
name: minimal
description: Minimal agent
---

Content here.
"""

        agent = agent_manager.parse_agent(content)

        assert agent.name == "minimal"
        assert agent.description == "Minimal agent"
        assert agent.model == "inherit"  # Default
        assert agent.tools == []
        assert agent.skills == []
        assert agent.color == "blue"  # Default
        assert agent.prompt == "Content here."

    def test_parse_tools_as_list(self, agent_manager):
        """Test parsing agent with tools as YAML list."""
        content = """---
name: test
description: Test
tools:
  - Read
  - Write
  - Grep
---

Content
"""

        agent = agent_manager.parse_agent(content)

        assert agent.tools == ["Read", "Write", "Grep"]

    def test_parse_skills_as_list(self, agent_manager):
        """Test parsing agent with skills as YAML list."""
        content = """---
name: test
description: Test
skills:
  - testing
  - debugging
  - documentation
---

Content
"""

        agent = agent_manager.parse_agent(content)

        assert agent.skills == ["testing", "debugging", "documentation"]

    def test_parse_empty_tools_string(self, agent_manager):
        """Test parsing agent with empty tools string."""
        content = """---
name: test
description: Test
tools: ""
---

Content
"""

        agent = agent_manager.parse_agent(content)

        assert agent.tools == []

    def test_parse_empty_skills_string(self, agent_manager):
        """Test parsing agent with empty skills string."""
        content = """---
name: test
description: Test
skills: ""
---

Content
"""

        agent = agent_manager.parse_agent(content)

        assert agent.skills == []

    def test_parse_missing_frontmatter(self, agent_manager):
        """Test parsing agent without frontmatter raises ValueError."""
        content = "# No Frontmatter\n\nJust content."

        with pytest.raises(ValueError, match="missing YAML frontmatter"):
            agent_manager.parse_agent(content)

    def test_parse_invalid_yaml(self, agent_manager):
        """Test parsing agent with invalid YAML raises YAMLError."""
        content = """---
name: test
description: desc
  bad_indent: value
---

Content
"""

        with pytest.raises(yaml.YAMLError):
            agent_manager.parse_agent(content)

    def test_parse_missing_name_field(self, agent_manager):
        """Test parsing agent without name field raises ValueError."""
        content = """---
description: Missing name field
model: inherit
---

Content
"""

        with pytest.raises(ValueError, match="Missing required fields.*name"):
            agent_manager.parse_agent(content)

    def test_parse_missing_description_field(self, agent_manager):
        """Test parsing agent without description field raises ValueError."""
        content = """---
name: test
model: inherit
---

Content
"""

        with pytest.raises(
            ValueError,
            match="Missing required fields.*description",
        ):
            agent_manager.parse_agent(content)

    def test_parse_missing_both_required_fields(self, agent_manager):
        """Test parsing agent without name and description raises ValueError."""
        content = """---
model: inherit
---

Content
"""

        with pytest.raises(ValueError, match="Missing required fields"):
            agent_manager.parse_agent(content)

    def test_parse_yaml_not_dict(self, agent_manager):
        """Test parsing agent where YAML is not a dictionary raises ValueError."""
        content = """---
- list item 1
- list item 2
---

Content
"""

        with pytest.raises(
            ValueError,
            match="YAML frontmatter must be a dictionary",
        ):
            agent_manager.parse_agent(content)

    def test_parse_empty_content(self, agent_manager):
        """Test parsing agent with empty markdown content."""
        content = """---
name: test
description: Test agent
---

"""

        agent = agent_manager.parse_agent(content)

        assert agent.prompt == ""

    def test_parse_multiline_content(self, agent_manager):
        """Test parsing agent with multiline markdown content."""
        content = """---
name: test
description: Test agent
---

# Heading 1

Paragraph 1.

## Heading 2

Paragraph 2.

- List item 1
- List item 2
"""

        agent = agent_manager.parse_agent(content)

        assert "# Heading 1" in agent.prompt
        assert "## Heading 2" in agent.prompt
        assert "- List item 1" in agent.prompt
        assert agent.prompt.count('\n') > 5

    def test_parse_strips_trailing_newlines(self, agent_manager):
        """Test that parse_agent strips trailing newlines from content."""
        content = """---
name: test
description: Test agent
---

Content here.


"""

        agent = agent_manager.parse_agent(content)

        assert agent.prompt == "Content here."
        assert not agent.prompt.endswith('\n\n')

    def test_parse_tools_with_whitespace(self, agent_manager):
        """Test parsing tools with extra whitespace."""
        content = """---
name: test
description: Test
tools: "  Read  ,  Write  , Grep  "
---

Content
"""

        agent = agent_manager.parse_agent(content)

        assert agent.tools == ["Read", "Write", "Grep"]

    def test_parse_skills_with_whitespace(self, agent_manager):
        """Test parsing skills with extra whitespace."""
        content = """---
name: test
description: Test
skills: "  testing  ,  debugging  "
---

Content
"""

        agent = agent_manager.parse_agent(content)

        assert agent.skills == ["testing", "debugging"]

    def test_parse_tools_as_non_string_non_list(self, agent_manager):
        """Test parsing agent with tools as unexpected type (e.g., int)."""
        content = """---
name: test
description: Test
tools: 123
---

Content
"""

        agent = agent_manager.parse_agent(content)

        # Should default to empty list for non-string/non-list
        assert agent.tools == []

    def test_parse_skills_as_non_string_non_list(self, agent_manager):
        """Test parsing agent with skills as unexpected type (e.g., int)."""
        content = """---
name: test
description: Test
skills: 456
---

Content
"""

        agent = agent_manager.parse_agent(content)

        # Should default to empty list for non-string/non-list
        assert agent.skills == []


class TestLoadAgent:
    """Tests for load_agent method."""

    def test_load_valid_agent(self, agent_manager):
        """Test loading a valid agent file."""
        # Copy fixture to agents directory
        src = FIXTURES_DIR / "valid_agent.md"
        dst = agent_manager.agents_dir / "valid_agent.md"
        shutil.copy(src, dst)

        agent = agent_manager.load_agent("valid_agent")

        assert agent.name == "valid_agent"
        assert "A valid test agent" in agent.description
        assert agent.model == "inherit"
        assert agent.tools == ["Read", "Write", "Grep"]
        assert agent.skills == ["code-analysis", "testing"]
        assert agent.color == "blue"
        assert "# Valid Agent System Prompt" in agent.prompt

    def test_load_minimal_agent(self, agent_manager):
        """Test loading a minimal agent file."""
        src = FIXTURES_DIR / "minimal_agent.md"
        dst = agent_manager.agents_dir / "minimal_agent.md"
        shutil.copy(src, dst)

        agent = agent_manager.load_agent("minimal_agent")

        assert agent.name == "minimal_agent"
        assert agent.description == "A minimal agent with only required fields"
        assert agent.model == "inherit"
        assert agent.tools == []
        assert agent.skills == []

    def test_load_nonexistent_agent(self, agent_manager):
        """Test loading non-existent agent raises AgentNotFoundError."""
        with pytest.raises(
            AgentNotFoundError,
            match="Agent 'nonexistent' not found",
        ):
            agent_manager.load_agent("nonexistent")

    def test_load_invalid_yaml_agent(self, agent_manager):
        """Test loading agent with invalid YAML raises AgentLoadError."""
        src = FIXTURES_DIR / "invalid_yaml.md"
        dst = agent_manager.agents_dir / "invalid_yaml.md"
        shutil.copy(src, dst)

        with pytest.raises(AgentLoadError, match="Failed to parse agent"):
            agent_manager.load_agent("invalid_yaml")

    def test_load_missing_frontmatter_agent(self, agent_manager):
        """Test loading agent without frontmatter raises AgentLoadError."""
        src = FIXTURES_DIR / "missing_frontmatter.md"
        dst = agent_manager.agents_dir / "missing_frontmatter.md"
        shutil.copy(src, dst)

        with pytest.raises(AgentLoadError, match="Failed to parse agent"):
            agent_manager.load_agent("missing_frontmatter")

    def test_load_missing_required_field(self, agent_manager):
        """Test loading agent with missing required field raises AgentLoadError."""
        src = FIXTURES_DIR / "missing_name.md"
        dst = agent_manager.agents_dir / "missing_name.md"
        shutil.copy(src, dst)

        with pytest.raises(AgentLoadError, match="Failed to parse agent"):
            agent_manager.load_agent("missing_name")

    def test_load_caches_agent(self, agent_manager):
        """Test that load_agent caches the loaded agent."""
        src = FIXTURES_DIR / "valid_agent.md"
        dst = agent_manager.agents_dir / "valid_agent.md"
        shutil.copy(src, dst)

        # Load agent first time
        agent1 = agent_manager.load_agent("valid_agent")

        # Verify it's in cache
        assert "valid_agent" in agent_manager._agent_cache
        assert agent_manager._agent_cache["valid_agent"] == agent1

        # Load again - should return cached version
        agent2 = agent_manager.load_agent("valid_agent")

        assert agent2 is agent1  # Same object reference

    def test_load_returns_cached_agent(self, agent_manager):
        """Test that load_agent returns cached agent on subsequent calls."""
        src = FIXTURES_DIR / "valid_agent.md"
        dst = agent_manager.agents_dir / "valid_agent.md"
        shutil.copy(src, dst)

        # Load and cache
        agent_manager.load_agent("valid_agent")

        # Remove file to prove cache is used
        dst.unlink()

        # Should still return cached agent
        cached_agent = agent_manager.load_agent("valid_agent")
        assert cached_agent.name == "valid_agent"

    def test_load_name_mismatch_uses_filename(self, agent_manager):
        """Test that load_agent corrects name mismatch and uses filename."""
        src = FIXTURES_DIR / "name_mismatch.md"
        dst = agent_manager.agents_dir / "name_mismatch.md"
        shutil.copy(src, dst)

        agent = agent_manager.load_agent("name_mismatch")

        # Should use filename, not YAML name
        assert agent.name == "name_mismatch"
        assert "different_name" not in agent_manager._agent_cache
        assert "name_mismatch" in agent_manager._agent_cache

    def test_load_file_read_error(self, agent_manager):
        """Test that load_agent raises AgentLoadError on file read failure."""
        # Create an agent file
        agent_file = agent_manager.agents_dir / "test.md"
        agent_file.write_text(
            "---\nname: test\ndescription: test\n---\nContent",
        )

        # Mock safe_read_file to raise FileReadError
        with patch('lib.agent_manager.safe_read_file') as mock_read:
            mock_read.side_effect = FileReadError("Read failed")

            with pytest.raises(
                AgentLoadError,
                match="Failed to read agent file",
            ):
                agent_manager.load_agent("test")

    def test_load_invalid_model_raises_validation_error(self, agent_manager):
        """Test that load_agent validates model and raises AgentValidationError."""
        src = FIXTURES_DIR / "invalid_model.md"
        dst = agent_manager.agents_dir / "invalid_model.md"
        shutil.copy(src, dst)

        with pytest.raises(
            AgentValidationError,
            match="Validation failed for agent",
        ):
            agent_manager.load_agent("invalid_model")

    def test_load_agent_with_invalid_tools(self, agent_manager):
        """Test loading agent with invalid tool references raises AgentValidationError."""
        # Create agent with invalid tools
        agent_file = agent_manager.agents_dir / "bad_tools.md"
        agent_file.write_text(
            """---
name: bad_tools
description: Agent with invalid tools
tools: InvalidTool, AnotherBadTool
---

Content
""",
        )

        with pytest.raises(
            AgentValidationError,
            match="Tool 'InvalidTool' referenced by agent but not found",
        ):
            agent_manager.load_agent("bad_tools")

    def test_load_agent_with_invalid_skills(self, agent_manager):
        """Test loading agent with invalid skill references raises AgentValidationError."""
        # Create agent with invalid skills
        agent_file = agent_manager.agents_dir / "bad_skills.md"
        agent_file.write_text(
            """---
name: bad_skills
description: Agent with invalid skills
skills: invalid-skill, another-bad-skill
---

Content
""",
        )

        with pytest.raises(
            AgentValidationError,
            match="Skill 'invalid-skill' referenced by agent but not found",
        ):
            agent_manager.load_agent("bad_skills")


class TestLoadAgents:
    """Tests for load_agents method."""

    def test_load_multiple_agents(self, populated_agent_manager):
        """Test loading multiple valid agents."""
        agents = populated_agent_manager.load_agents()

        assert len(agents) == 2
        assert "valid_agent" in agents
        assert "minimal_agent" in agents
        assert agents["valid_agent"].name == "valid_agent"
        assert agents["minimal_agent"].name == "minimal_agent"

    def test_load_agents_clears_cache(self, populated_agent_manager):
        """Test that load_agents clears the cache before loading."""
        # Populate cache with dummy data
        populated_agent_manager._agent_cache["dummy"] = Mock()

        agents = populated_agent_manager.load_agents()

        # Dummy should not be in result
        assert "dummy" not in agents
        assert "dummy" not in populated_agent_manager._agent_cache

    def test_load_agents_empty_directory(self, agent_manager):
        """Test loading agents from empty directory."""
        agents = agent_manager.load_agents()

        assert agents == {}
        assert len(agent_manager._agent_cache) == 0

    def test_load_agents_ignores_invalid_agents(self, agent_manager):
        """Test that load_agents continues loading even if some agents are invalid."""
        # Copy valid and invalid agents
        shutil.copy(
            FIXTURES_DIR / "valid_agent.md",
            agent_manager.agents_dir / "valid_agent.md",
        )
        shutil.copy(
            FIXTURES_DIR / "invalid_yaml.md",
            agent_manager.agents_dir / "invalid_yaml.md",
        )
        shutil.copy(
            FIXTURES_DIR / "minimal_agent.md",
            agent_manager.agents_dir / "minimal_agent.md",
        )

        agents = agent_manager.load_agents()

        # Should load 2 valid agents, skip 1 invalid
        assert len(agents) == 2
        assert "valid_agent" in agents
        assert "minimal_agent" in agents
        assert "invalid_yaml" not in agents

    def test_load_agents_alphabetical_order(self, agent_manager):
        """Test that load_agents processes files in alphabetical order."""
        # Create agents with names that sort alphabetically
        for name in ["zebra", "alpha", "middle"]:
            agent_file = agent_manager.agents_dir / f"{name}.md"
            agent_file.write_text(
                f"---\nname: {name}\ndescription: Test\n---\nContent",
            )

        agents = agent_manager.load_agents()

        agent_names = list(agents.keys())
        assert agent_names == sorted(agent_names)

    def test_load_agents_caches_results(self, populated_agent_manager):
        """Test that load_agents populates the cache."""
        populated_agent_manager.load_agents()

        assert len(populated_agent_manager._agent_cache) == 2
        assert "valid_agent" in populated_agent_manager._agent_cache
        assert "minimal_agent" in populated_agent_manager._agent_cache

    def test_load_agents_returns_copy(self, populated_agent_manager):
        """Test that load_agents returns a copy of the cache."""
        agents1 = populated_agent_manager.load_agents()
        agents2 = populated_agent_manager.load_agents()

        # Should be equal but not the same object
        assert agents1 == agents2
        assert agents1 is not agents2

    def test_load_agents_ignores_non_md_files(self, agent_manager):
        """Test that load_agents ignores non-.md files."""
        # Create various files
        (agent_manager.agents_dir / "valid.md").write_text(
            "---\nname: valid\ndescription: Test\n---\nContent",
        )
        (agent_manager.agents_dir / "readme.txt").write_text("Not an agent")
        (agent_manager.agents_dir / "data.json").write_text(
            '{"key": "value"}',
        )

        agents = agent_manager.load_agents()

        assert len(agents) == 1
        assert "valid" in agents


class TestSaveAgent:
    """Tests for save_agent method."""

    def test_save_new_agent(self, agent_manager, sample_agent_config):
        """Test saving a new agent file."""
        agent_manager.save_agent(sample_agent_config)

        # Verify file was created
        agent_file = agent_manager.agents_dir / "test_agent.md"
        assert agent_file.exists()

        # Verify content
        content = agent_file.read_text()
        assert "name: test_agent" in content
        assert "description: A test agent for unit testing" in content
        assert "model: inherit" in content
        assert "tools: Read, Write" in content
        assert "skills: testing" in content
        assert "color: green" in content
        assert "# Test Agent" in content

    def test_save_agent_updates_cache(self, agent_manager, sample_agent_config):
        """Test that save_agent updates the cache."""
        agent_manager.save_agent(sample_agent_config)

        assert "test_agent" in agent_manager._agent_cache
        assert agent_manager._agent_cache["test_agent"] == sample_agent_config

    def test_save_agent_with_empty_tools(self, agent_manager):
        """Test saving agent with empty tools list."""
        agent = AgentConfig(
            name="no_tools",
            description="Agent without tools",
            model="inherit",
            tools=[],
            skills=["testing"],
            prompt="Content here.",
        )

        agent_manager.save_agent(agent)

        # Verify file content
        agent_file = agent_manager.agents_dir / "no_tools.md"
        content = agent_file.read_text()
        assert "tools: ''" in content or "tools:" in content

    def test_save_agent_with_empty_skills(self, agent_manager):
        """Test saving agent with empty skills list."""
        agent = AgentConfig(
            name="no_skills",
            description="Agent without skills",
            model="inherit",
            tools=["Read"],
            skills=[],
            prompt="Content here.",
        )

        agent_manager.save_agent(agent)

        # Verify file content
        agent_file = agent_manager.agents_dir / "no_skills.md"
        content = agent_file.read_text()
        assert "skills: ''" in content or "skills:" in content

    def test_save_agent_overwrites_existing(
        self,
        agent_manager,
        sample_agent_config,
    ):
        """Test that save_agent overwrites existing agent file."""
        # Save initial version
        agent_manager.save_agent(sample_agent_config)

        # Modify and save again
        sample_agent_config.description = "Updated description"
        sample_agent_config.model = "claude-3-opus-20240229"
        agent_manager.save_agent(sample_agent_config)

        # Verify updated content
        agent_file = agent_manager.agents_dir / "test_agent.md"
        content = agent_file.read_text()
        assert "Updated description" in content
        assert "claude-3-opus-20240229" in content

    def test_save_agent_formats_correctly(
        self,
        agent_manager,
        sample_agent_config,
    ):
        """Test that save_agent formats the file correctly."""
        agent_manager.save_agent(sample_agent_config)

        agent_file = agent_manager.agents_dir / "test_agent.md"
        content = agent_file.read_text()

        # Should start with ---
        assert content.startswith("---\n")

        # Should have closing ---
        assert "\n---\n" in content

        # Content should be after frontmatter
        parts = content.split("---\n")
        assert len(parts) >= 3
        assert "# Test Agent" in parts[2]

    def test_save_agent_adds_trailing_newline(self, agent_manager):
        """Test that save_agent ensures content ends with newline."""
        agent = AgentConfig(
            name="test",
            description="Test",
            prompt="No trailing newline",
        )

        agent_manager.save_agent(agent)

        agent_file = agent_manager.agents_dir / "test.md"
        content = agent_file.read_text()

        # File should end with single newline
        assert content.endswith("\n")
        assert not content.endswith("\n\n")

    def test_save_agent_validation_error(self, agent_manager):
        """Test that save_agent raises AgentValidationError for invalid config."""
        # Create invalid agent config (mock validation failure)
        invalid_agent = Mock(spec=AgentConfig)
        invalid_agent.model_validate.side_effect = ValidationError.from_exception_data(
            "validation_error",
            [
                {
                    "type": "missing",
                    "loc": ("name",),
                    "msg": "Field required",
                    "input": {},
                },
            ],
        )

        with pytest.raises(
            AgentValidationError,
            match="Invalid agent configuration",
        ):
            agent_manager.save_agent(invalid_agent)

    def test_save_agent_file_write_error(
        self,
        agent_manager,
        sample_agent_config,
    ):
        """Test that save_agent raises AgentError on write failure."""
        with patch('lib.agent_manager.safe_write_file') as mock_write:
            mock_write.side_effect = FileWriteError("Write failed")

            with pytest.raises(AgentError, match="Failed to write agent file"):
                agent_manager.save_agent(sample_agent_config)

    def test_save_agent_yaml_formatting(
        self,
        agent_manager,
        sample_agent_config,
    ):
        """Test that save_agent formats YAML correctly."""
        agent_manager.save_agent(sample_agent_config)

        agent_file = agent_manager.agents_dir / "test_agent.md"
        content = agent_file.read_text()

        # Extract YAML part
        yaml_part = content.split("---\n")[1]
        parsed = yaml.safe_load(yaml_part)

        assert parsed["name"] == "test_agent"
        assert parsed["description"] == "A test agent for unit testing"
        assert parsed["model"] == "inherit"
        assert parsed["color"] == "green"

    def test_save_agent_with_invalid_tools(self, agent_manager):
        """Test saving agent with invalid tool references raises AgentValidationError."""
        agent = AgentConfig(
            name="bad_tools",
            description="Agent with invalid tools",
            tools=["InvalidTool"],
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Tool 'InvalidTool' referenced by agent but not found",
        ):
            agent_manager.save_agent(agent)

    def test_save_agent_with_invalid_skills(self, agent_manager):
        """Test saving agent with invalid skill references raises AgentValidationError."""
        agent = AgentConfig(
            name="bad_skills",
            description="Agent with invalid skills",
            skills=["invalid-skill"],
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Skill 'invalid-skill' referenced by agent but not found",
        ):
            agent_manager.save_agent(agent)

    def test_save_agent_with_invalid_model(self, agent_manager):
        """Test saving agent with invalid model raises AgentValidationError."""
        agent = AgentConfig(
            name="bad_model",
            description="Agent with invalid model",
            model="gpt-4-turbo",
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Invalid model",
        ):
            agent_manager.save_agent(agent)


class TestDeleteAgent:
    """Tests for delete_agent method."""

    def test_delete_existing_agent(self, agent_manager):
        """Test deleting an existing agent file."""
        # Create an agent file
        agent_file = agent_manager.agents_dir / "to_delete.md"
        agent_file.write_text(
            "---\nname: to_delete\ndescription: Test\n---\nContent",
        )

        # Delete it
        agent_manager.delete_agent("to_delete")

        # Verify it's gone
        assert not agent_file.exists()

    def test_delete_removes_from_cache(self, agent_manager):
        """Test that delete_agent removes agent from cache."""
        # Create and load agent
        agent_file = agent_manager.agents_dir / "cached.md"
        agent_file.write_text(
            "---\nname: cached\ndescription: Test\n---\nContent",
        )
        agent_manager.load_agent("cached")

        # Verify it's cached
        assert "cached" in agent_manager._agent_cache

        # Delete
        agent_manager.delete_agent("cached")

        # Verify removed from cache
        assert "cached" not in agent_manager._agent_cache

    def test_delete_nonexistent_agent(self, agent_manager):
        """Test deleting non-existent agent raises AgentNotFoundError."""
        with pytest.raises(
            AgentNotFoundError,
            match="Agent 'nonexistent' not found",
        ):
            agent_manager.delete_agent("nonexistent")

    def test_delete_agent_file_delete_error(self, agent_manager):
        """Test that delete_agent raises AgentError on delete failure."""
        # Create agent file
        agent_file = agent_manager.agents_dir / "test.md"
        agent_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        with patch('lib.agent_manager.safe_delete_file') as mock_delete:
            mock_delete.side_effect = FileDeleteError("Delete failed")

            with pytest.raises(
                AgentError,
                match="Failed to delete agent file",
            ):
                agent_manager.delete_agent("test")

    def test_delete_agent_not_cached(self, agent_manager):
        """Test deleting agent that isn't in cache."""
        # Create agent without loading it
        agent_file = agent_manager.agents_dir / "uncached.md"
        agent_file.write_text(
            "---\nname: uncached\ndescription: Test\n---\nContent",
        )

        # Delete should work fine
        agent_manager.delete_agent("uncached")

        assert not agent_file.exists()


class TestListAgents:
    """Tests for list_agents method."""

    def test_list_empty_directory(self, agent_manager):
        """Test listing agents in empty directory."""
        agents = agent_manager.list_agents()

        assert agents == []

    def test_list_single_agent(self, agent_manager):
        """Test listing single agent."""
        agent_file = agent_manager.agents_dir / "single.md"
        agent_file.write_text(
            "---\nname: single\ndescription: Test\n---\nContent",
        )

        agents = agent_manager.list_agents()

        assert agents == ["single"]

    def test_list_multiple_agents(self, populated_agent_manager):
        """Test listing multiple agents."""
        agents = populated_agent_manager.list_agents()

        assert len(agents) == 2
        assert "valid_agent" in agents
        assert "minimal_agent" in agents

    def test_list_returns_sorted(self, agent_manager):
        """Test that list_agents returns sorted agent names."""
        # Create agents in non-alphabetical order
        for name in ["zebra", "alpha", "middle"]:
            agent_file = agent_manager.agents_dir / f"{name}.md"
            agent_file.write_text(
                f"---\nname: {name}\ndescription: Test\n---\nContent",
            )

        agents = agent_manager.list_agents()

        assert agents == ["alpha", "middle", "zebra"]

    def test_list_ignores_non_md_files(self, agent_manager):
        """Test that list_agents ignores non-.md files."""
        # Create various files
        (agent_manager.agents_dir / "agent.md").write_text("content")
        (agent_manager.agents_dir / "readme.txt").write_text("content")
        (agent_manager.agents_dir / "data.json").write_text("content")

        agents = agent_manager.list_agents()

        assert len(agents) == 1
        assert agents == ["agent"]

    def test_list_includes_invalid_agents(self, agent_manager):
        """Test that list_agents includes all .md files, even invalid ones."""
        # Create valid and invalid agents
        (agent_manager.agents_dir / "valid.md").write_text(
            "---\nname: valid\ndescription: Test\n---\nContent",
        )
        (agent_manager.agents_dir / "invalid.md").write_text(
            "Not a valid agent",
        )

        agents = agent_manager.list_agents()

        # Should list both files
        assert len(agents) == 2
        assert "valid" in agents
        assert "invalid" in agents

    def test_list_does_not_load_agents(self, agent_manager):
        """Test that list_agents doesn't load or validate agents."""
        # Create agent file
        agent_file = agent_manager.agents_dir / "test.md"
        agent_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        # List agents
        agents = agent_manager.list_agents()

        # Should not be in cache
        assert "test" not in agent_manager._agent_cache
        assert agents == ["test"]


class TestGetAgent:
    """Tests for get_agent method."""

    def test_get_agent_calls_load_agent(self, agent_manager):
        """Test that get_agent is an alias for load_agent."""
        # Create agent file
        agent_file = agent_manager.agents_dir / "test.md"
        agent_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        # Get agent
        agent = agent_manager.get_agent("test")

        assert agent.name == "test"
        assert agent.description == "Test"

    def test_get_agent_returns_same_as_load_agent(self, agent_manager):
        """Test that get_agent returns same result as load_agent."""
        src = FIXTURES_DIR / "valid_agent.md"
        dst = agent_manager.agents_dir / "valid_agent.md"
        shutil.copy(src, dst)

        agent1 = agent_manager.load_agent("valid_agent")
        agent2 = agent_manager.get_agent("valid_agent")

        # Should return same cached object
        assert agent1 is agent2

    def test_get_nonexistent_agent(self, agent_manager):
        """Test that get_agent raises AgentNotFoundError for missing agent."""
        with pytest.raises(AgentNotFoundError):
            agent_manager.get_agent("nonexistent")


class TestValidateAgent:
    """Tests for validate_agent method."""

    def test_validate_valid_agent(self, agent_manager, sample_agent_config):
        """Test validating a valid agent configuration."""
        # Should not raise any exception
        agent_manager.validate_agent(sample_agent_config)

    def test_validate_agent_with_invalid_model(self, agent_manager):
        """Test validating agent with invalid model raises AgentValidationError."""
        agent = AgentConfig(
            name="test",
            description="Test",
            model="gpt-4-turbo",
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Invalid model 'gpt-4-turbo'",
        ):
            agent_manager.validate_agent(agent)

    def test_validate_agent_with_valid_models(self, agent_manager):
        """Test validating agent with all valid model IDs."""
        for model in VALID_MODELS:
            agent = AgentConfig(
                name="test",
                description="Test",
                model=model,
                prompt="Content",
            )
            # Should not raise
            agent_manager.validate_agent(agent)

    def test_validate_agent_with_invalid_tool(self, agent_manager):
        """Test validating agent with invalid tool raises AgentValidationError."""
        agent = AgentConfig(
            name="test",
            description="Test",
            tools=["Read", "InvalidTool"],
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Tool 'InvalidTool' referenced by agent but not found",
        ):
            agent_manager.validate_agent(agent)

    def test_validate_agent_with_invalid_skill(self, agent_manager):
        """Test validating agent with invalid skill raises AgentValidationError."""
        agent = AgentConfig(
            name="test",
            description="Test",
            skills=["testing", "invalid-skill"],
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Skill 'invalid-skill' referenced by agent but not found",
        ):
            agent_manager.validate_agent(agent)

    def test_validate_agent_with_multiple_errors(self, agent_manager):
        """Test validating agent with multiple errors reports all issues."""
        agent = AgentConfig(
            name="test",
            description="Test",
            model="invalid-model",
            tools=["InvalidTool1", "InvalidTool2"],
            skills=["invalid-skill"],
            prompt="Content",
        )

        with pytest.raises(
            AgentValidationError,
            match="Agent validation failed",
        ) as exc_info:
            agent_manager.validate_agent(agent)

        # Should mention all errors
        error_msg = str(exc_info.value)
        assert "Invalid model" in error_msg
        assert "InvalidTool1" in error_msg
        assert "InvalidTool2" in error_msg
        assert "invalid-skill" in error_msg

    def test_validate_agent_with_empty_tools_and_skills(self, agent_manager):
        """Test validating agent with no tools or skills is valid."""
        agent = AgentConfig(
            name="test",
            description="Test",
            tools=[],
            skills=[],
            prompt="Content",
        )

        # Should not raise
        agent_manager.validate_agent(agent)


class TestClearCache:
    """Tests for clear_cache method."""

    def test_clear_empty_cache(self, agent_manager):
        """Test clearing empty cache."""
        agent_manager.clear_cache()

        assert len(agent_manager._agent_cache) == 0

    def test_clear_populated_cache(self, populated_agent_manager):
        """Test clearing populated cache."""
        # Load agents to populate cache
        populated_agent_manager.load_agents()
        assert len(populated_agent_manager._agent_cache) > 0

        # Clear cache
        populated_agent_manager.clear_cache()

        assert len(populated_agent_manager._agent_cache) == 0

    def test_clear_cache_forces_reload(self, agent_manager):
        """Test that clearing cache forces agents to be reloaded."""
        # Create and load agent
        agent_file = agent_manager.agents_dir / "test.md"
        agent_file.write_text(
            "---\nname: test\ndescription: Original\n---\nContent",
        )
        agent1 = agent_manager.load_agent("test")

        # Modify file
        agent_file.write_text(
            "---\nname: test\ndescription: Modified\n---\nContent",
        )

        # Without clearing cache, should get cached version
        agent2 = agent_manager.load_agent("test")
        assert agent2.description == "Original"

        # Clear cache
        agent_manager.clear_cache()

        # Should now load modified version
        agent3 = agent_manager.load_agent("test")
        assert agent3.description == "Modified"


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_unicode_in_agent_content(self, agent_manager):
        """Test handling agents with unicode characters."""
        content = """---
name: unicode_agent
description: "Agent with unicode: 你好 🚀 café"
---

# Unicode Content

This has unicode: 你好世界 🚀 café résumé
"""

        agent = agent_manager.parse_agent(content)

        assert "你好" in agent.description
        assert "🚀" in agent.description
        assert "你好世界" in agent.prompt
        assert "café" in agent.prompt

    def test_very_long_agent_content(self, agent_manager):
        """Test handling agent with very long content."""
        long_content = "# Long Content\n\n" + ("Lorem ipsum " * 10000)
        content = f"""---
name: long_agent
description: Very long agent
---

{long_content}
"""

        agent = agent_manager.parse_agent(content)

        assert len(agent.prompt) > 50000
        assert "Lorem ipsum" in agent.prompt

    def test_agent_with_special_yaml_characters(self, agent_manager):
        """Test handling agent with special YAML characters in values."""
        content = """---
name: special_chars
description: "Description with: colons and 'quotes'"
model: inherit
---

Content here.
"""

        agent = agent_manager.parse_agent(content)

        assert agent.description == "Description with: colons and 'quotes'"

    def test_empty_agents_directory_operations(self, agent_manager):
        """Test all operations work with empty agents directory."""
        assert agent_manager.list_agents() == []
        assert agent_manager.load_agents() == {}

        with pytest.raises(AgentNotFoundError):
            agent_manager.load_agent("nonexistent")

        with pytest.raises(AgentNotFoundError):
            agent_manager.delete_agent("nonexistent")

    def test_concurrent_agent_operations(self, agent_manager):
        """Test that agent operations are safe with save/load cycles."""
        # Create initial agent
        agent_v1 = AgentConfig(
            name="versioned_agent",
            description="Test agent",
            model="inherit",
            prompt="Original content",
        )

        # Save agent v1
        agent_manager.save_agent(agent_v1)

        # Load agent (gets cached)
        loaded_v1 = agent_manager.load_agent("versioned_agent")
        assert loaded_v1.prompt == "Original content"

        # Create updated version
        agent_v2 = AgentConfig(
            name="versioned_agent",
            description="Test agent",
            model="claude-3-opus-20240229",
            prompt="Updated content",
        )

        # Save updated version
        agent_manager.save_agent(agent_v2)

        # Clear cache and reload to get new version
        agent_manager.clear_cache()
        reloaded = agent_manager.load_agent("versioned_agent")

        assert reloaded.model == "claude-3-opus-20240229"
        assert reloaded.prompt == "Updated content"

    def test_agent_with_code_blocks_in_content(self, agent_manager):
        """Test parsing agent with code blocks containing YAML-like content."""
        content = """---
name: code_agent
description: Agent with code blocks
---

# Code Example

```yaml
---
name: fake_agent
description: This is in a code block
---
```

More content.
"""

        agent = agent_manager.parse_agent(content)

        assert agent.name == "code_agent"
        assert "```yaml" in agent.prompt
        assert "fake_agent" in agent.prompt

    def test_agent_file_permissions_error(self, agent_manager):
        """Test handling file permission errors."""
        agent_file = agent_manager.agents_dir / "test.md"
        agent_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        # Mock permission error on read
        with patch('lib.agent_manager.safe_read_file') as mock_read:
            mock_read.side_effect = FileReadError("Permission denied")

            with pytest.raises(
                AgentLoadError,
                match="Failed to read agent file",
            ):
                agent_manager.load_agent("test")


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_crud_workflow(self, agent_manager, sample_agent_config):
        """Test complete create-read-update-delete workflow."""
        # Create
        agent_manager.save_agent(sample_agent_config)
        assert sample_agent_config.name in agent_manager.list_agents()

        # Read
        loaded = agent_manager.get_agent(sample_agent_config.name)
        assert loaded.name == sample_agent_config.name
        assert loaded.description == sample_agent_config.description

        # Update
        sample_agent_config.description = "Updated description"
        agent_manager.save_agent(sample_agent_config)
        agent_manager.clear_cache()
        updated = agent_manager.get_agent(sample_agent_config.name)
        assert updated.description == "Updated description"

        # Delete
        agent_manager.delete_agent(sample_agent_config.name)
        assert sample_agent_config.name not in agent_manager.list_agents()

    def test_load_save_round_trip(self, agent_manager):
        """Test that loading and saving preserves agent data."""
        # Copy fixture
        src = FIXTURES_DIR / "valid_agent.md"
        dst = agent_manager.agents_dir / "valid_agent.md"
        shutil.copy(src, dst)

        # Load agent
        original = agent_manager.load_agent("valid_agent")

        # Save with new name
        original.name = "copied_agent"
        agent_manager.save_agent(original)

        # Load the copy
        agent_manager.clear_cache()
        copied = agent_manager.load_agent("copied_agent")

        # Should have same content (except name)
        assert copied.description == original.description
        assert copied.model == original.model
        assert copied.tools == original.tools
        assert copied.skills == original.skills
        assert copied.prompt == original.prompt

    def test_bulk_operations(self, agent_manager):
        """Test bulk create, list, and delete operations."""
        # Create multiple agents
        agent_names = []
        for i in range(5):
            agent = AgentConfig(
                name=f"bulk_agent_{i}",
                description=f"Bulk agent {i}",
                prompt=f"Content {i}",
            )
            agent_manager.save_agent(agent)
            agent_names.append(agent.name)

        # List all
        listed = agent_manager.list_agents()
        assert len(listed) == 5
        assert all(name in listed for name in agent_names)

        # Load all
        loaded = agent_manager.load_agents()
        assert len(loaded) == 5

        # Delete all
        for name in agent_names:
            agent_manager.delete_agent(name)

        assert agent_manager.list_agents() == []

    def test_validation_during_load_workflow(self, agent_manager):
        """Test that validation occurs during load workflow."""
        # Create agent with valid references
        agent = AgentConfig(
            name="valid_refs",
            description="Agent with valid tool/skill refs",
            tools=["Read", "Write"],
            skills=["testing"],
            prompt="Content",
        )
        agent_manager.save_agent(agent)

        # Clear cache and reload - should succeed
        agent_manager.clear_cache()
        loaded = agent_manager.load_agent("valid_refs")
        assert loaded.name == "valid_refs"

        # Now create agent with invalid references
        agent_file = agent_manager.agents_dir / "invalid_refs.md"
        agent_file.write_text(
            """---
name: invalid_refs
description: Agent with invalid refs
tools: InvalidTool
skills: invalid-skill
---

Content
""",
        )

        # Loading should fail validation
        with pytest.raises(AgentValidationError):
            agent_manager.load_agent("invalid_refs")

    def test_tools_as_string_vs_list(self, agent_manager):
        """Test that tools work whether specified as string or list."""
        # Test with string (comma-separated)
        src = FIXTURES_DIR / "valid_agent.md"
        dst = agent_manager.agents_dir / "valid_agent.md"
        shutil.copy(src, dst)
        agent1 = agent_manager.load_agent("valid_agent")

        # Test with list
        src = FIXTURES_DIR / "tools_as_list.md"
        dst = agent_manager.agents_dir / "tools_as_list.md"
        shutil.copy(src, dst)
        agent2 = agent_manager.load_agent("tools_as_list")

        # Both should have tools as lists
        assert isinstance(agent1.tools, list)
        assert isinstance(agent2.tools, list)
        assert len(agent1.tools) == 3
        assert len(agent2.tools) == 3
