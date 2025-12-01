"""
Tests for SkillManager implementation.

This test suite provides comprehensive coverage for skill loading, parsing,
saving, deleting, and error handling. Tests use fixture files in
tests/fixtures/skills/ to verify behavior with various skill formats.
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import yaml
from pydantic import ValidationError

from lib.skill_manager import (
    SkillManager,
    SkillError,
    SkillNotFoundError,
    SkillLoadError,
    SkillValidationError,
)
from lib.data_models import SkillConfig
from lib.file_operations import FileReadError, FileWriteError, FileDeleteError


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skills"


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
def skill_manager(temp_project_dir):
    """
    Create a SkillManager instance for testing.

    Args:
        temp_project_dir: Temporary project directory fixture

    Returns:
        SkillManager: Configured SkillManager instance
    """
    return SkillManager(temp_project_dir)


@pytest.fixture
def populated_skill_manager(temp_project_dir):
    """
    Create a SkillManager with pre-populated valid skills.

    Args:
        temp_project_dir: Temporary project directory fixture

    Returns:
        SkillManager: SkillManager with valid test skills
    """
    manager = SkillManager(temp_project_dir)
    skills_dir = manager.skills_dir

    # Copy valid fixture files to the skills directory
    valid_files = [
        "valid_skill.md",
        "minimal_skill.md",
    ]

    for filename in valid_files:
        src = FIXTURES_DIR / filename
        dst = skills_dir / filename
        shutil.copy(src, dst)

    return manager


@pytest.fixture
def sample_skill_config():
    """
    Create a sample SkillConfig for testing.

    Returns:
        SkillConfig: Sample skill configuration
    """
    return SkillConfig(
        name="test_skill",
        description="A test skill for unit testing",
        version="1.0.0",
        author="Test Author",
        content="# Test Skill\n\nThis is test content.",
    )


class TestSkillManagerInit:
    """Tests for SkillManager initialization."""

    def test_init_creates_skills_directory(self, temp_project_dir):
        """Test that __init__ creates skills directory if it doesn't exist."""
        # Ensure skills directory doesn't exist
        skills_dir = temp_project_dir / "skills"
        assert not skills_dir.exists()

        # Initialize manager
        manager = SkillManager(temp_project_dir)

        # Verify skills directory was created
        assert manager.skills_dir.exists()
        assert manager.skills_dir.is_dir()
        assert manager.skills_dir == skills_dir

    def test_init_with_existing_skills_directory(self, temp_project_dir):
        """Test initialization with pre-existing skills directory."""
        # Create skills directory
        skills_dir = temp_project_dir / "skills"
        skills_dir.mkdir()

        # Initialize manager
        manager = SkillManager(temp_project_dir)

        # Verify directory is used
        assert manager.skills_dir == skills_dir
        assert manager.skills_dir.exists()

    def test_init_sets_project_path(self, temp_project_dir):
        """Test that __init__ sets project_path correctly."""
        manager = SkillManager(temp_project_dir)

        assert manager.project_path == temp_project_dir
        assert isinstance(manager.project_path, Path)

    def test_init_initializes_empty_cache(self, temp_project_dir):
        """Test that __init__ initializes an empty skill cache."""
        manager = SkillManager(temp_project_dir)

        assert hasattr(manager, '_skill_cache')
        assert isinstance(manager._skill_cache, dict)
        assert len(manager._skill_cache) == 0

    def test_init_with_path_string(self, temp_project_dir):
        """Test initialization with string path instead of Path object."""
        manager = SkillManager(str(temp_project_dir))

        assert manager.project_path == temp_project_dir
        assert isinstance(manager.project_path, Path)


class TestParseSkill:
    """Tests for parse_skill method."""

    def test_parse_valid_skill(self, skill_manager):
        """Test parsing a valid skill with all fields."""
        content = """---
name: test_skill
description: Test description
version: 1.0.0
author: Test Author
---

# Test Content

This is the markdown content.
"""

        skill = skill_manager.parse_skill(content)

        assert skill.name == "test_skill"
        assert skill.description == "Test description"
        assert skill.version == "1.0.0"
        assert skill.author == "Test Author"
        assert "# Test Content" in skill.content
        assert "This is the markdown content." in skill.content

    def test_parse_minimal_skill(self, skill_manager):
        """Test parsing a skill with only required fields."""
        content = """---
name: minimal
description: Minimal skill
---

Content here.
"""

        skill = skill_manager.parse_skill(content)

        assert skill.name == "minimal"
        assert skill.description == "Minimal skill"
        assert skill.version == "1.0.0"  # Default version
        assert skill.author is None
        assert skill.content == "Content here."

    def test_parse_missing_frontmatter(self, skill_manager):
        """Test parsing skill without frontmatter raises ValueError."""
        content = "# No Frontmatter\n\nJust content."

        with pytest.raises(ValueError, match="missing YAML frontmatter"):
            skill_manager.parse_skill(content)

    def test_parse_invalid_yaml(self, skill_manager):
        """Test parsing skill with invalid YAML raises YAMLError."""
        content = """---
name: test
description: desc
  bad_indent: value
---

Content
"""

        with pytest.raises(yaml.YAMLError):
            skill_manager.parse_skill(content)

    def test_parse_missing_name_field(self, skill_manager):
        """Test parsing skill without name field raises ValueError."""
        content = """---
description: Missing name field
version: 1.0.0
---

Content
"""

        with pytest.raises(ValueError, match="Missing required fields.*name"):
            skill_manager.parse_skill(content)

    def test_parse_missing_description_field(self, skill_manager):
        """Test parsing skill without description field raises ValueError."""
        content = """---
name: test
version: 1.0.0
---

Content
"""

        with pytest.raises(ValueError, match="Missing required fields.*description"):
            skill_manager.parse_skill(content)

    def test_parse_missing_both_required_fields(self, skill_manager):
        """Test parsing skill without name and description raises ValueError."""
        content = """---
version: 1.0.0
---

Content
"""

        with pytest.raises(ValueError, match="Missing required fields"):
            skill_manager.parse_skill(content)

    def test_parse_yaml_not_dict(self, skill_manager):
        """Test parsing skill where YAML is not a dictionary raises ValueError."""
        content = """---
- list item 1
- list item 2
---

Content
"""

        with pytest.raises(ValueError, match="YAML frontmatter must be a dictionary"):
            skill_manager.parse_skill(content)

    def test_parse_empty_content(self, skill_manager):
        """Test parsing skill with empty markdown content."""
        content = """---
name: test
description: Test skill
---

"""

        skill = skill_manager.parse_skill(content)

        assert skill.content == ""

    def test_parse_multiline_content(self, skill_manager):
        """Test parsing skill with multiline markdown content."""
        content = """---
name: test
description: Test skill
---

# Heading 1

Paragraph 1.

## Heading 2

Paragraph 2.

- List item 1
- List item 2
"""

        skill = skill_manager.parse_skill(content)

        assert "# Heading 1" in skill.content
        assert "## Heading 2" in skill.content
        assert "- List item 1" in skill.content
        assert skill.content.count('\n') > 5

    def test_parse_strips_trailing_newlines(self, skill_manager):
        """Test that parse_skill strips trailing newlines from content."""
        content = """---
name: test
description: Test skill
---

Content here.


"""

        skill = skill_manager.parse_skill(content)

        assert skill.content == "Content here."
        assert not skill.content.endswith('\n\n')


class TestLoadSkill:
    """Tests for load_skill method."""

    def test_load_valid_skill(self, skill_manager):
        """Test loading a valid skill file."""
        # Copy fixture to skills directory
        src = FIXTURES_DIR / "valid_skill.md"
        dst = skill_manager.skills_dir / "valid_skill.md"
        shutil.copy(src, dst)

        skill = skill_manager.load_skill("valid_skill")

        assert skill.name == "valid_skill"
        assert skill.description == "A valid test skill for testing purposes"
        assert skill.version == "1.0.0"
        assert skill.author == "Test Author"
        assert "# Valid Skill" in skill.content

    def test_load_minimal_skill(self, skill_manager):
        """Test loading a minimal skill file."""
        src = FIXTURES_DIR / "minimal_skill.md"
        dst = skill_manager.skills_dir / "minimal_skill.md"
        shutil.copy(src, dst)

        skill = skill_manager.load_skill("minimal_skill")

        assert skill.name == "minimal_skill"
        assert skill.description == "A minimal skill with only required fields"
        assert skill.version == "1.0.0"
        assert skill.author is None

    def test_load_nonexistent_skill(self, skill_manager):
        """Test loading non-existent skill raises SkillNotFoundError."""
        with pytest.raises(SkillNotFoundError, match="Skill 'nonexistent' not found"):
            skill_manager.load_skill("nonexistent")

    def test_load_invalid_yaml_skill(self, skill_manager):
        """Test loading skill with invalid YAML raises SkillLoadError."""
        src = FIXTURES_DIR / "invalid_yaml.md"
        dst = skill_manager.skills_dir / "invalid_yaml.md"
        shutil.copy(src, dst)

        with pytest.raises(SkillLoadError, match="Failed to parse skill"):
            skill_manager.load_skill("invalid_yaml")

    def test_load_missing_frontmatter_skill(self, skill_manager):
        """Test loading skill without frontmatter raises SkillLoadError."""
        src = FIXTURES_DIR / "missing_frontmatter.md"
        dst = skill_manager.skills_dir / "missing_frontmatter.md"
        shutil.copy(src, dst)

        with pytest.raises(SkillLoadError, match="Failed to parse skill"):
            skill_manager.load_skill("missing_frontmatter")

    def test_load_missing_required_field(self, skill_manager):
        """Test loading skill with missing required field raises SkillValidationError."""
        src = FIXTURES_DIR / "missing_name.md"
        dst = skill_manager.skills_dir / "missing_name.md"
        shutil.copy(src, dst)

        with pytest.raises(SkillLoadError, match="Failed to parse skill"):
            skill_manager.load_skill("missing_name")

    def test_load_caches_skill(self, skill_manager):
        """Test that load_skill caches the loaded skill."""
        src = FIXTURES_DIR / "valid_skill.md"
        dst = skill_manager.skills_dir / "valid_skill.md"
        shutil.copy(src, dst)

        # Load skill first time
        skill1 = skill_manager.load_skill("valid_skill")

        # Verify it's in cache
        assert "valid_skill" in skill_manager._skill_cache
        assert skill_manager._skill_cache["valid_skill"] == skill1

        # Load again - should return cached version
        skill2 = skill_manager.load_skill("valid_skill")

        assert skill2 is skill1  # Same object reference

    def test_load_returns_cached_skill(self, skill_manager):
        """Test that load_skill returns cached skill on subsequent calls."""
        src = FIXTURES_DIR / "valid_skill.md"
        dst = skill_manager.skills_dir / "valid_skill.md"
        shutil.copy(src, dst)

        # Load and cache
        skill_manager.load_skill("valid_skill")

        # Remove file to prove cache is used
        dst.unlink()

        # Should still return cached skill
        cached_skill = skill_manager.load_skill("valid_skill")
        assert cached_skill.name == "valid_skill"

    def test_load_name_mismatch_uses_filename(self, skill_manager):
        """Test that load_skill corrects name mismatch and uses filename."""
        src = FIXTURES_DIR / "name_mismatch.md"
        dst = skill_manager.skills_dir / "name_mismatch.md"
        shutil.copy(src, dst)

        skill = skill_manager.load_skill("name_mismatch")

        # Should use filename, not YAML name
        assert skill.name == "name_mismatch"
        assert "different_name" not in skill_manager._skill_cache
        assert "name_mismatch" in skill_manager._skill_cache

    def test_load_file_read_error(self, skill_manager):
        """Test that load_skill raises SkillLoadError on file read failure."""
        # Create a skill file
        skill_file = skill_manager.skills_dir / "test.md"
        skill_file.write_text("---\nname: test\ndescription: test\n---\nContent")

        # Mock safe_read_file to raise FileReadError
        with patch('lib.skill_manager.safe_read_file') as mock_read:
            mock_read.side_effect = FileReadError("Read failed")

            with pytest.raises(SkillLoadError, match="Failed to read skill file"):
                skill_manager.load_skill("test")


class TestLoadSkills:
    """Tests for load_skills method."""

    def test_load_multiple_skills(self, populated_skill_manager):
        """Test loading multiple valid skills."""
        skills = populated_skill_manager.load_skills()

        assert len(skills) == 2
        assert "valid_skill" in skills
        assert "minimal_skill" in skills
        assert skills["valid_skill"].name == "valid_skill"
        assert skills["minimal_skill"].name == "minimal_skill"

    def test_load_skills_clears_cache(self, populated_skill_manager):
        """Test that load_skills clears the cache before loading."""
        # Populate cache with dummy data
        populated_skill_manager._skill_cache["dummy"] = Mock()

        skills = populated_skill_manager.load_skills()

        # Dummy should not be in result
        assert "dummy" not in skills
        assert "dummy" not in populated_skill_manager._skill_cache

    def test_load_skills_empty_directory(self, skill_manager):
        """Test loading skills from empty directory."""
        skills = skill_manager.load_skills()

        assert skills == {}
        assert len(skill_manager._skill_cache) == 0

    def test_load_skills_ignores_invalid_skills(self, skill_manager):
        """Test that load_skills continues loading even if some skills are invalid."""
        # Copy valid and invalid skills
        shutil.copy(
            FIXTURES_DIR / "valid_skill.md",
            skill_manager.skills_dir / "valid_skill.md",
        )
        shutil.copy(
            FIXTURES_DIR / "invalid_yaml.md",
            skill_manager.skills_dir / "invalid_yaml.md",
        )
        shutil.copy(
            FIXTURES_DIR / "minimal_skill.md",
            skill_manager.skills_dir / "minimal_skill.md",
        )

        skills = skill_manager.load_skills()

        # Should load 2 valid skills, skip 1 invalid
        assert len(skills) == 2
        assert "valid_skill" in skills
        assert "minimal_skill" in skills
        assert "invalid_yaml" not in skills

    def test_load_skills_alphabetical_order(self, skill_manager):
        """Test that load_skills processes files in alphabetical order."""
        # Create skills with names that sort alphabetically
        for name in ["zebra", "alpha", "middle"]:
            skill_file = skill_manager.skills_dir / f"{name}.md"
            skill_file.write_text(
                f"---\nname: {name}\ndescription: Test\n---\nContent",
            )

        skills = skill_manager.load_skills()

        skill_names = list(skills.keys())
        assert skill_names == sorted(skill_names)

    def test_load_skills_caches_results(self, populated_skill_manager):
        """Test that load_skills populates the cache."""
        populated_skill_manager.load_skills()

        assert len(populated_skill_manager._skill_cache) == 2
        assert "valid_skill" in populated_skill_manager._skill_cache
        assert "minimal_skill" in populated_skill_manager._skill_cache

    def test_load_skills_returns_copy(self, populated_skill_manager):
        """Test that load_skills returns a copy of the cache."""
        skills1 = populated_skill_manager.load_skills()
        skills2 = populated_skill_manager.load_skills()

        # Should be equal but not the same object
        assert skills1 == skills2
        assert skills1 is not skills2

    def test_load_skills_ignores_non_md_files(self, skill_manager):
        """Test that load_skills ignores non-.md files."""
        # Create various files
        (skill_manager.skills_dir / "valid.md").write_text(
            "---\nname: valid\ndescription: Test\n---\nContent",
        )
        (skill_manager.skills_dir / "readme.txt").write_text("Not a skill")
        (skill_manager.skills_dir / "data.json").write_text('{"key": "value"}')

        skills = skill_manager.load_skills()

        assert len(skills) == 1
        assert "valid" in skills


class TestSaveSkill:
    """Tests for save_skill method."""

    def test_save_new_skill(self, skill_manager, sample_skill_config):
        """Test saving a new skill file."""
        skill_manager.save_skill(sample_skill_config)

        # Verify file was created
        skill_file = skill_manager.skills_dir / "test_skill.md"
        assert skill_file.exists()

        # Verify content
        content = skill_file.read_text()
        assert "name: test_skill" in content
        assert "description: A test skill for unit testing" in content
        assert "version: 1.0.0" in content
        assert "author: Test Author" in content
        assert "# Test Skill" in content

    def test_save_skill_updates_cache(self, skill_manager, sample_skill_config):
        """Test that save_skill updates the cache."""
        skill_manager.save_skill(sample_skill_config)

        assert "test_skill" in skill_manager._skill_cache
        assert skill_manager._skill_cache["test_skill"] == sample_skill_config

    def test_save_skill_without_author(self, skill_manager):
        """Test saving skill without author field."""
        skill = SkillConfig(
            name="no_author",
            description="Skill without author",
            version="2.0.0",
            content="Content here.",
        )

        skill_manager.save_skill(skill)

        # Verify file content doesn't include author
        skill_file = skill_manager.skills_dir / "no_author.md"
        content = skill_file.read_text()
        assert "author:" not in content
        assert "name: no_author" in content

    def test_save_skill_overwrites_existing(self, skill_manager, sample_skill_config):
        """Test that save_skill overwrites existing skill file."""
        # Save initial version
        skill_manager.save_skill(sample_skill_config)

        # Modify and save again
        sample_skill_config.description = "Updated description"
        sample_skill_config.version = "2.0.0"
        skill_manager.save_skill(sample_skill_config)

        # Verify updated content
        skill_file = skill_manager.skills_dir / "test_skill.md"
        content = skill_file.read_text()
        assert "Updated description" in content
        assert "version: 2.0.0" in content

    def test_save_skill_formats_correctly(self, skill_manager, sample_skill_config):
        """Test that save_skill formats the file correctly."""
        skill_manager.save_skill(sample_skill_config)

        skill_file = skill_manager.skills_dir / "test_skill.md"
        content = skill_file.read_text()

        # Should start with ---
        assert content.startswith("---\n")

        # Should have closing ---
        assert "\n---\n" in content

        # Content should be after frontmatter
        parts = content.split("---\n")
        assert len(parts) >= 3
        assert "# Test Skill" in parts[2]

    def test_save_skill_adds_trailing_newline(self, skill_manager):
        """Test that save_skill ensures content ends with newline."""
        skill = SkillConfig(
            name="test",
            description="Test",
            content="No trailing newline",
        )

        skill_manager.save_skill(skill)

        skill_file = skill_manager.skills_dir / "test.md"
        content = skill_file.read_text()

        # File should end with single newline
        assert content.endswith("\n")
        assert not content.endswith("\n\n")

    def test_save_skill_validation_error(self, skill_manager):
        """Test that save_skill raises SkillValidationError for invalid config."""
        # Create invalid skill config (mock validation failure)
        invalid_skill = Mock(spec=SkillConfig)
        invalid_skill.model_validate.side_effect = ValidationError.from_exception_data(
            "validation_error",
            [{"type": "missing", "loc": ("name",), "msg": "Field required", "input": {}}],
        )

        with pytest.raises(SkillValidationError, match="Invalid skill configuration"):
            skill_manager.save_skill(invalid_skill)

    def test_save_skill_file_write_error(self, skill_manager, sample_skill_config):
        """Test that save_skill raises SkillError on write failure."""
        with patch('lib.skill_manager.safe_write_file') as mock_write:
            mock_write.side_effect = FileWriteError("Write failed")

            with pytest.raises(SkillError, match="Failed to write skill file"):
                skill_manager.save_skill(sample_skill_config)

    def test_save_skill_yaml_formatting(self, skill_manager, sample_skill_config):
        """Test that save_skill formats YAML correctly."""
        skill_manager.save_skill(sample_skill_config)

        skill_file = skill_manager.skills_dir / "test_skill.md"
        content = skill_file.read_text()

        # Extract YAML part
        yaml_part = content.split("---\n")[1]
        parsed = yaml.safe_load(yaml_part)

        assert parsed["name"] == "test_skill"
        assert parsed["description"] == "A test skill for unit testing"
        assert parsed["version"] == "1.0.0"
        assert parsed["author"] == "Test Author"


class TestDeleteSkill:
    """Tests for delete_skill method."""

    def test_delete_existing_skill(self, skill_manager):
        """Test deleting an existing skill file."""
        # Create a skill file
        skill_file = skill_manager.skills_dir / "to_delete.md"
        skill_file.write_text(
            "---\nname: to_delete\ndescription: Test\n---\nContent",
        )

        # Delete it
        skill_manager.delete_skill("to_delete")

        # Verify it's gone
        assert not skill_file.exists()

    def test_delete_removes_from_cache(self, skill_manager):
        """Test that delete_skill removes skill from cache."""
        # Create and load skill
        skill_file = skill_manager.skills_dir / "cached.md"
        skill_file.write_text(
            "---\nname: cached\ndescription: Test\n---\nContent",
        )
        skill_manager.load_skill("cached")

        # Verify it's cached
        assert "cached" in skill_manager._skill_cache

        # Delete
        skill_manager.delete_skill("cached")

        # Verify removed from cache
        assert "cached" not in skill_manager._skill_cache

    def test_delete_nonexistent_skill(self, skill_manager):
        """Test deleting non-existent skill raises SkillNotFoundError."""
        with pytest.raises(SkillNotFoundError, match="Skill 'nonexistent' not found"):
            skill_manager.delete_skill("nonexistent")

    def test_delete_skill_file_delete_error(self, skill_manager):
        """Test that delete_skill raises SkillError on delete failure."""
        # Create skill file
        skill_file = skill_manager.skills_dir / "test.md"
        skill_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        with patch('lib.skill_manager.safe_delete_file') as mock_delete:
            mock_delete.side_effect = FileDeleteError("Delete failed")

            with pytest.raises(SkillError, match="Failed to delete skill file"):
                skill_manager.delete_skill("test")

    def test_delete_skill_not_cached(self, skill_manager):
        """Test deleting skill that isn't in cache."""
        # Create skill without loading it
        skill_file = skill_manager.skills_dir / "uncached.md"
        skill_file.write_text(
            "---\nname: uncached\ndescription: Test\n---\nContent",
        )

        # Delete should work fine
        skill_manager.delete_skill("uncached")

        assert not skill_file.exists()


class TestListSkills:
    """Tests for list_skills method."""

    def test_list_empty_directory(self, skill_manager):
        """Test listing skills in empty directory."""
        skills = skill_manager.list_skills()

        assert skills == []

    def test_list_single_skill(self, skill_manager):
        """Test listing single skill."""
        skill_file = skill_manager.skills_dir / "single.md"
        skill_file.write_text(
            "---\nname: single\ndescription: Test\n---\nContent",
        )

        skills = skill_manager.list_skills()

        assert skills == ["single"]

    def test_list_multiple_skills(self, populated_skill_manager):
        """Test listing multiple skills."""
        skills = populated_skill_manager.list_skills()

        assert len(skills) == 2
        assert "valid_skill" in skills
        assert "minimal_skill" in skills

    def test_list_returns_sorted(self, skill_manager):
        """Test that list_skills returns sorted skill names."""
        # Create skills in non-alphabetical order
        for name in ["zebra", "alpha", "middle"]:
            skill_file = skill_manager.skills_dir / f"{name}.md"
            skill_file.write_text(
                f"---\nname: {name}\ndescription: Test\n---\nContent",
            )

        skills = skill_manager.list_skills()

        assert skills == ["alpha", "middle", "zebra"]

    def test_list_ignores_non_md_files(self, skill_manager):
        """Test that list_skills ignores non-.md files."""
        # Create various files
        (skill_manager.skills_dir / "skill.md").write_text("content")
        (skill_manager.skills_dir / "readme.txt").write_text("content")
        (skill_manager.skills_dir / "data.json").write_text("content")

        skills = skill_manager.list_skills()

        assert len(skills) == 1
        assert skills == ["skill"]

    def test_list_includes_invalid_skills(self, skill_manager):
        """Test that list_skills includes all .md files, even invalid ones."""
        # Create valid and invalid skills
        (skill_manager.skills_dir / "valid.md").write_text(
            "---\nname: valid\ndescription: Test\n---\nContent",
        )
        (skill_manager.skills_dir / "invalid.md").write_text("Not a valid skill")

        skills = skill_manager.list_skills()

        # Should list both files
        assert len(skills) == 2
        assert "valid" in skills
        assert "invalid" in skills

    def test_list_does_not_load_skills(self, skill_manager):
        """Test that list_skills doesn't load or validate skills."""
        # Create skill file
        skill_file = skill_manager.skills_dir / "test.md"
        skill_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        # List skills
        skills = skill_manager.list_skills()

        # Should not be in cache
        assert "test" not in skill_manager._skill_cache
        assert skills == ["test"]


class TestGetSkill:
    """Tests for get_skill method."""

    def test_get_skill_calls_load_skill(self, skill_manager):
        """Test that get_skill is an alias for load_skill."""
        # Create skill file
        skill_file = skill_manager.skills_dir / "test.md"
        skill_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        # Get skill
        skill = skill_manager.get_skill("test")

        assert skill.name == "test"
        assert skill.description == "Test"

    def test_get_skill_returns_same_as_load_skill(self, skill_manager):
        """Test that get_skill returns same result as load_skill."""
        src = FIXTURES_DIR / "valid_skill.md"
        dst = skill_manager.skills_dir / "valid_skill.md"
        shutil.copy(src, dst)

        skill1 = skill_manager.load_skill("valid_skill")
        skill2 = skill_manager.get_skill("valid_skill")

        # Should return same cached object
        assert skill1 is skill2

    def test_get_nonexistent_skill(self, skill_manager):
        """Test that get_skill raises SkillNotFoundError for missing skill."""
        with pytest.raises(SkillNotFoundError):
            skill_manager.get_skill("nonexistent")


class TestClearCache:
    """Tests for clear_cache method."""

    def test_clear_empty_cache(self, skill_manager):
        """Test clearing empty cache."""
        skill_manager.clear_cache()

        assert len(skill_manager._skill_cache) == 0

    def test_clear_populated_cache(self, populated_skill_manager):
        """Test clearing populated cache."""
        # Load skills to populate cache
        populated_skill_manager.load_skills()
        assert len(populated_skill_manager._skill_cache) > 0

        # Clear cache
        populated_skill_manager.clear_cache()

        assert len(populated_skill_manager._skill_cache) == 0

    def test_clear_cache_forces_reload(self, skill_manager):
        """Test that clearing cache forces skills to be reloaded."""
        # Create and load skill
        skill_file = skill_manager.skills_dir / "test.md"
        skill_file.write_text(
            "---\nname: test\ndescription: Original\n---\nContent",
        )
        skill1 = skill_manager.load_skill("test")

        # Modify file
        skill_file.write_text(
            "---\nname: test\ndescription: Modified\n---\nContent",
        )

        # Without clearing cache, should get cached version
        skill2 = skill_manager.load_skill("test")
        assert skill2.description == "Original"

        # Clear cache
        skill_manager.clear_cache()

        # Should now load modified version
        skill3 = skill_manager.load_skill("test")
        assert skill3.description == "Modified"


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_unicode_in_skill_content(self, skill_manager):
        """Test handling skills with unicode characters."""
        content = """---
name: unicode_skill
description: "Skill with unicode: 你好 🚀 café"
---

# Unicode Content

This has unicode: 你好世界 🚀 café résumé
"""

        skill = skill_manager.parse_skill(content)

        assert "你好" in skill.description
        assert "🚀" in skill.description
        assert "你好世界" in skill.content
        assert "café" in skill.content

    def test_very_long_skill_content(self, skill_manager):
        """Test handling skill with very long content."""
        long_content = "# Long Content\n\n" + ("Lorem ipsum " * 10000)
        content = f"""---
name: long_skill
description: Very long skill
---

{long_content}
"""

        skill = skill_manager.parse_skill(content)

        assert len(skill.content) > 50000
        assert "Lorem ipsum" in skill.content

    def test_skill_with_special_yaml_characters(self, skill_manager):
        """Test handling skill with special YAML characters in values."""
        content = """---
name: special_chars
description: "Description with: colons and 'quotes'"
author: "Author: Test"
---

Content here.
"""

        skill = skill_manager.parse_skill(content)

        assert skill.description == "Description with: colons and 'quotes'"
        assert skill.author == "Author: Test"

    def test_empty_skills_directory_operations(self, skill_manager):
        """Test all operations work with empty skills directory."""
        assert skill_manager.list_skills() == []
        assert skill_manager.load_skills() == {}

        with pytest.raises(SkillNotFoundError):
            skill_manager.load_skill("nonexistent")

        with pytest.raises(SkillNotFoundError):
            skill_manager.delete_skill("nonexistent")

    def test_concurrent_skill_operations(self, skill_manager):
        """Test that skill operations are safe with save/load cycles."""
        # Create initial skill
        skill_v1 = SkillConfig(
            name="versioned_skill",
            description="Test skill",
            version="1.0.0",
            content="Original content",
        )

        # Save skill v1
        skill_manager.save_skill(skill_v1)

        # Load skill (gets cached)
        loaded_v1 = skill_manager.load_skill("versioned_skill")
        assert loaded_v1.version == "1.0.0"

        # Create updated version
        skill_v2 = SkillConfig(
            name="versioned_skill",
            description="Test skill",
            version="2.0.0",
            content="Updated content",
        )

        # Save updated version
        skill_manager.save_skill(skill_v2)

        # Clear cache and reload to get new version
        skill_manager.clear_cache()
        reloaded = skill_manager.load_skill("versioned_skill")

        assert reloaded.version == "2.0.0"
        assert reloaded.content == "Updated content"

    def test_skill_with_code_blocks_in_content(self, skill_manager):
        """Test parsing skill with code blocks containing YAML-like content."""
        content = """---
name: code_skill
description: Skill with code blocks
---

# Code Example

```yaml
---
name: fake_skill
description: This is in a code block
---
```

More content.
"""

        skill = skill_manager.parse_skill(content)

        assert skill.name == "code_skill"
        assert "```yaml" in skill.content
        assert "fake_skill" in skill.content

    def test_skill_file_permissions_error(self, skill_manager):
        """Test handling file permission errors."""
        skill_file = skill_manager.skills_dir / "test.md"
        skill_file.write_text(
            "---\nname: test\ndescription: Test\n---\nContent",
        )

        # Mock permission error on read
        with patch('lib.skill_manager.safe_read_file') as mock_read:
            mock_read.side_effect = FileReadError("Permission denied")

            with pytest.raises(SkillLoadError, match="Failed to read skill file"):
                skill_manager.load_skill("test")


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_crud_workflow(self, skill_manager, sample_skill_config):
        """Test complete create-read-update-delete workflow."""
        # Create
        skill_manager.save_skill(sample_skill_config)
        assert sample_skill_config.name in skill_manager.list_skills()

        # Read
        loaded = skill_manager.get_skill(sample_skill_config.name)
        assert loaded.name == sample_skill_config.name
        assert loaded.description == sample_skill_config.description

        # Update
        sample_skill_config.description = "Updated description"
        skill_manager.save_skill(sample_skill_config)
        skill_manager.clear_cache()
        updated = skill_manager.get_skill(sample_skill_config.name)
        assert updated.description == "Updated description"

        # Delete
        skill_manager.delete_skill(sample_skill_config.name)
        assert sample_skill_config.name not in skill_manager.list_skills()

    def test_load_save_round_trip(self, skill_manager):
        """Test that loading and saving preserves skill data."""
        # Copy fixture
        src = FIXTURES_DIR / "valid_skill.md"
        dst = skill_manager.skills_dir / "valid_skill.md"
        shutil.copy(src, dst)

        # Load skill
        original = skill_manager.load_skill("valid_skill")

        # Save with new name
        original.name = "copied_skill"
        skill_manager.save_skill(original)

        # Load the copy
        skill_manager.clear_cache()
        copied = skill_manager.load_skill("copied_skill")

        # Should have same content (except name)
        assert copied.description == original.description
        assert copied.version == original.version
        assert copied.author == original.author
        assert copied.content == original.content

    def test_bulk_operations(self, skill_manager):
        """Test bulk create, list, and delete operations."""
        # Create multiple skills
        skill_names = []
        for i in range(5):
            skill = SkillConfig(
                name=f"bulk_skill_{i}",
                description=f"Bulk skill {i}",
                content=f"Content {i}",
            )
            skill_manager.save_skill(skill)
            skill_names.append(skill.name)

        # List all
        listed = skill_manager.list_skills()
        assert len(listed) == 5
        assert all(name in listed for name in skill_names)

        # Load all
        loaded = skill_manager.load_skills()
        assert len(loaded) == 5

        # Delete all
        for name in skill_names:
            skill_manager.delete_skill(name)

        assert skill_manager.list_skills() == []
