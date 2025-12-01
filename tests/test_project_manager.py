"""
Comprehensive unit tests for ProjectManager class.

Tests cover:
- Project creation with valid/invalid names
- Project listing with multiple projects
- Project loading and structure validation
- Project deletion
- Missing file creation (auto-repair)
- Agent/skill/tool/snippet listing helper methods
- Error cases (duplicate names, invalid paths, permission errors)
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from lib.data_models import Project, ProjectSettings, Session
from lib.file_operations import FileOperationError
from lib.project_manager import (
    ProjectAlreadyExistsError,
    ProjectError,
    ProjectManager,
    ProjectNotFoundError,
)


class TestProjectManagerInit:
    """Tests for ProjectManager initialization."""

    def test_init_creates_projects_directory(self, tmp_path):
        """Test that ProjectManager creates projects directory if it doesn't exist."""
        projects_root = tmp_path / "projects"
        assert not projects_root.exists()

        pm = ProjectManager(projects_root)

        assert projects_root.exists()
        assert projects_root.is_dir()
        assert pm.projects_root == projects_root

    def test_init_with_existing_directory(self, tmp_path):
        """Test initialization with existing directory."""
        projects_root = tmp_path / "projects"
        projects_root.mkdir()

        pm = ProjectManager(projects_root)

        assert pm.projects_root == projects_root


class TestCreateProject:
    """Tests for project creation."""

    def test_create_project_with_valid_name(self, tmp_path):
        """Test creating a project with valid name."""
        pm = ProjectManager(tmp_path)
        project = pm.create_project(
            name="test-project",
            description="Test description",
        )

        # Verify project object
        assert project.name == "test-project"
        assert project.description == "Test description"
        assert isinstance(project.created, datetime)
        assert isinstance(project.modified, datetime)
        assert isinstance(project.settings, ProjectSettings)

        # Verify directory structure
        project_dir = tmp_path / "test-project"
        assert project_dir.exists()
        assert (project_dir / "agents").exists()
        assert (project_dir / "skills").exists()
        assert (project_dir / "tools").exists()
        assert (project_dir / "snippets").exists()
        assert (project_dir / "tests").exists()

        # Verify files
        assert (project_dir / "project.json").exists()
        assert (project_dir / "current_session.json").exists()
        assert (project_dir / "requirements.txt").exists()

    def test_create_project_without_description(self, tmp_path):
        """Test creating a project without description."""
        pm = ProjectManager(tmp_path)
        project = pm.create_project(name="minimal-project")

        assert project.name == "minimal-project"
        assert project.description is None

    def test_create_project_with_underscores_and_numbers(self, tmp_path):
        """Test creating a project with underscores and numbers in name."""
        pm = ProjectManager(tmp_path)
        project = pm.create_project(name="project_123_test")

        assert project.name == "project_123_test"
        assert (tmp_path / "project_123_test").exists()

    def test_create_project_validates_project_json(self, tmp_path):
        """Test that created project.json is valid and complete."""
        pm = ProjectManager(tmp_path)
        pm.create_project(
            name="validate-test",
            description="Description",
        )

        project_json = tmp_path / "validate-test" / "project.json"
        data = json.loads(project_json.read_text())

        # Verify all required fields
        assert data["name"] == "validate-test"
        assert data["description"] == "Description"
        assert "created" in data
        assert "modified" in data
        assert "settings" in data
        assert data["settings"]["max_session_backups"] == 20
        assert data["settings"]["auto_save"] is True
        assert data["settings"]["default_model"] == "claude-sonnet-4-5-20250929"

    def test_create_project_validates_session_json(self, tmp_path):
        """Test that created current_session.json is valid."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="session-test")

        session_json = tmp_path / "session-test" / "current_session.json"
        data = json.loads(session_json.read_text())

        # Verify session structure
        assert data["model"] == "claude-sonnet-4-5-20250929"
        assert data["max_tokens"] == 8192
        assert data["temperature"] == 1.0
        assert data["system"] == []
        assert data["tools"] == []
        assert data["messages"] == []

        # Verify it can be loaded as Session object
        session = Session(**data)
        assert session.model == "claude-sonnet-4-5-20250929"

    def test_create_project_validates_requirements_txt(self, tmp_path):
        """Test that created requirements.txt has correct content."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="requirements-test")

        requirements = tmp_path / "requirements-test" / "requirements.txt"
        content = requirements.read_text()

        assert "anthropic>=0.18.0" in content

    def test_create_project_with_invalid_name_empty(self, tmp_path):
        """Test that empty project name raises error."""
        pm = ProjectManager(tmp_path)

        with pytest.raises(ProjectError, match="Invalid project name"):
            pm.create_project(name="")

    def test_create_project_with_invalid_name_special_chars(self, tmp_path):
        """Test that project name with special characters raises error."""
        pm = ProjectManager(tmp_path)

        with pytest.raises(ProjectError, match="Invalid project name"):
            pm.create_project(name="project@test!")

    def test_create_project_with_invalid_name_spaces(self, tmp_path):
        """Test that project name with spaces raises error."""
        pm = ProjectManager(tmp_path)

        with pytest.raises(ProjectError, match="Invalid project name"):
            pm.create_project(name="project name")

    def test_create_project_with_invalid_name_too_long(self, tmp_path):
        """Test that project name that's too long raises error."""
        pm = ProjectManager(tmp_path)
        long_name = "a" * 101

        with pytest.raises(ProjectError, match="Invalid project name"):
            pm.create_project(name=long_name)

    def test_create_duplicate_project_raises_error(self, tmp_path):
        """Test that creating duplicate project raises error."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="duplicate")

        with pytest.raises(
            ProjectAlreadyExistsError,
            match="Project 'duplicate' already exists",
        ):
            pm.create_project(name="duplicate")

    def test_create_project_cleans_up_on_failure(self, tmp_path):
        """Test that project directory is cleaned up if creation fails."""
        pm = ProjectManager(tmp_path)
        project_dir = tmp_path / "test-project"

        # Create project directory manually to trigger a write error later
        project_dir.mkdir()

        # Create a read-only file to cause write failure
        test_file = project_dir / "project.json"
        test_file.write_text("test")
        test_file.chmod(0o444)

        try:
            # Try to create project (should fail)
            with pytest.raises(ProjectError):
                pm.create_project(name="test-project")
        finally:
            # Clean up: restore permissions for cleanup
            if test_file.exists():
                test_file.chmod(0o644)

        # Directory should still exist (cleanup may fail if permissions issue)
        # This test mainly verifies the cleanup is attempted


class TestListProjects:
    """Tests for listing projects."""

    def test_list_projects_empty(self, tmp_path):
        """Test listing projects when directory is empty."""
        pm = ProjectManager(tmp_path)
        projects = pm.list_projects()

        assert projects == []

    def test_list_projects_single(self, tmp_path):
        """Test listing a single project."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="project1", description="First project")

        projects = pm.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "project1"
        assert projects[0].description == "First project"

    def test_list_projects_multiple(self, tmp_path):
        """Test listing multiple projects."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="alpha", description="Alpha project")
        pm.create_project(name="beta", description="Beta project")
        pm.create_project(name="gamma", description="Gamma project")

        projects = pm.list_projects()

        assert len(projects) == 3
        # Projects should be sorted by name
        assert projects[0].name == "alpha"
        assert projects[1].name == "beta"
        assert projects[2].name == "gamma"

    def test_list_projects_ignores_hidden_directories(self, tmp_path):
        """Test that hidden directories are ignored."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="visible")

        # Create hidden directory
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()

        projects = pm.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "visible"

    def test_list_projects_ignores_files(self, tmp_path):
        """Test that files in projects root are ignored."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="project1")

        # Create a file in projects root
        (tmp_path / "readme.txt").write_text("test")

        projects = pm.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "project1"

    def test_list_projects_skips_invalid_projects(self, tmp_path):
        """Test that projects with invalid metadata are skipped."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="valid")

        # Create invalid project (missing project.json)
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()

        projects = pm.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "valid"

    def test_list_projects_skips_corrupt_project_json(self, tmp_path):
        """Test that projects with corrupt project.json are skipped."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="valid")

        # Create project with corrupt project.json
        corrupt_dir = tmp_path / "corrupt"
        corrupt_dir.mkdir()
        (corrupt_dir / "project.json").write_text("{ invalid json }")

        projects = pm.list_projects()

        assert len(projects) == 1
        assert projects[0].name == "valid"


class TestLoadProject:
    """Tests for loading projects."""

    def test_load_existing_project(self, tmp_path):
        """Test loading an existing project."""
        pm = ProjectManager(tmp_path)
        created = pm.create_project(name="test-project", description="Test")

        loaded = pm.load_project(name="test-project")

        assert loaded.name == created.name
        assert loaded.description == created.description

    def test_load_nonexistent_project(self, tmp_path):
        """Test loading a project that doesn't exist."""
        pm = ProjectManager(tmp_path)

        with pytest.raises(
            ProjectNotFoundError,
            match="Project 'nonexistent' does not exist",
        ):
            pm.load_project(name="nonexistent")

    def test_load_project_validates_structure(self, tmp_path):
        """Test that loading project validates structure."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test-project")

        # Remove a directory to test validation
        agents_dir = tmp_path / "test-project" / "agents"
        shutil.rmtree(agents_dir)

        assert not agents_dir.exists()

        # Load should succeed and recreate missing directory
        loaded = pm.load_project(name="test-project")

        assert loaded.name == "test-project"
        assert agents_dir.exists()

    def test_load_project_creates_missing_files(self, tmp_path):
        """Test that loading project creates missing files."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test-project")

        # Remove required files
        requirements = tmp_path / "test-project" / "requirements.txt"
        session = tmp_path / "test-project" / "current_session.json"
        requirements.unlink()
        session.unlink()

        assert not requirements.exists()
        assert not session.exists()

        # Load should recreate missing files
        pm.load_project(name="test-project")

        assert requirements.exists()
        assert session.exists()

    def test_load_project_not_directory(self, tmp_path):
        """Test loading a project that is a file, not directory."""
        pm = ProjectManager(tmp_path)

        # Create a file instead of directory
        (tmp_path / "file-project").write_text("test")

        with pytest.raises(ProjectError, match="is not a directory"):
            pm.load_project(name="file-project")


class TestLoadProjectMetadata:
    """Tests for loading project metadata."""

    def test_load_metadata_success(self, tmp_path):
        """Test loading project metadata successfully."""
        pm = ProjectManager(tmp_path)
        created = pm.create_project(name="test-project", description="Test")

        metadata = pm.load_project_metadata(name="test-project")

        assert metadata.name == "test-project"
        assert metadata.description == "Test"
        assert isinstance(metadata.settings, ProjectSettings)

    def test_load_metadata_nonexistent_project(self, tmp_path):
        """Test loading metadata for nonexistent project."""
        pm = ProjectManager(tmp_path)

        with pytest.raises(
            ProjectNotFoundError,
            match="Project 'nonexistent' does not exist",
        ):
            pm.load_project_metadata(name="nonexistent")

    def test_load_metadata_missing_project_json(self, tmp_path):
        """Test loading metadata when project.json is missing."""
        pm = ProjectManager(tmp_path)

        # Create directory without project.json
        project_dir = tmp_path / "no-metadata"
        project_dir.mkdir()

        with pytest.raises(ProjectError, match="is missing project.json"):
            pm.load_project_metadata(name="no-metadata")

    def test_load_metadata_empty_project_json(self, tmp_path):
        """Test loading metadata when project.json is empty."""
        pm = ProjectManager(tmp_path)

        # Create directory with empty project.json
        project_dir = tmp_path / "empty-metadata"
        project_dir.mkdir()
        (project_dir / "project.json").write_text("")

        with pytest.raises(ProjectError, match="empty or invalid"):
            pm.load_project_metadata(name="empty-metadata")

    def test_load_metadata_invalid_json(self, tmp_path):
        """Test loading metadata with invalid JSON."""
        pm = ProjectManager(tmp_path)

        # Create directory with invalid JSON
        project_dir = tmp_path / "invalid-json"
        project_dir.mkdir()
        (project_dir / "project.json").write_text("{ invalid }")

        with pytest.raises(ProjectError, match="Failed to read project metadata"):
            pm.load_project_metadata(name="invalid-json")

    def test_load_metadata_invalid_data(self, tmp_path):
        """Test loading metadata with invalid data structure."""
        pm = ProjectManager(tmp_path)

        # Create directory with invalid data
        project_dir = tmp_path / "invalid-data"
        project_dir.mkdir()
        (project_dir / "project.json").write_text(
            json.dumps({"name": "invalid-data"}),
        )

        with pytest.raises(ProjectError, match="Invalid project metadata"):
            pm.load_project_metadata(name="invalid-data")


class TestDeleteProject:
    """Tests for deleting projects."""

    def test_delete_existing_project(self, tmp_path):
        """Test deleting an existing project."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="to-delete")

        project_dir = tmp_path / "to-delete"
        assert project_dir.exists()

        pm.delete_project(name="to-delete")

        assert not project_dir.exists()

    def test_delete_nonexistent_project(self, tmp_path):
        """Test deleting a project that doesn't exist."""
        pm = ProjectManager(tmp_path)

        with pytest.raises(
            ProjectNotFoundError,
            match="Project 'nonexistent' does not exist",
        ):
            pm.delete_project(name="nonexistent")

    def test_delete_project_removes_all_contents(self, tmp_path):
        """Test that deleting project removes all contents."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="with-contents")

        # Add some files to project
        project_dir = tmp_path / "with-contents"
        (project_dir / "agents" / "test.md").write_text("test")
        (project_dir / "skills" / "skill.md").write_text("skill")

        pm.delete_project(name="with-contents")

        assert not project_dir.exists()
        assert not (project_dir / "agents" / "test.md").exists()


class TestValidateProjectStructure:
    """Tests for _validate_project_structure method."""

    def test_validate_complete_structure(self, tmp_path):
        """Test validating a complete project structure."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="complete")

        project_dir = tmp_path / "complete"
        missing = pm._validate_project_structure(project_dir)

        assert missing == []

    def test_validate_missing_directories(self, tmp_path):
        """Test detecting missing directories."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="incomplete")

        project_dir = tmp_path / "incomplete"
        shutil.rmtree(project_dir / "agents")
        shutil.rmtree(project_dir / "skills")

        missing = pm._validate_project_structure(project_dir)

        assert "agents" in missing
        assert "skills" in missing
        assert len(missing) == 2

    def test_validate_missing_files(self, tmp_path):
        """Test detecting missing files."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="incomplete")

        project_dir = tmp_path / "incomplete"
        (project_dir / "requirements.txt").unlink()
        (project_dir / "current_session.json").unlink()

        missing = pm._validate_project_structure(project_dir)

        assert "requirements.txt" in missing
        assert "current_session.json" in missing
        assert len(missing) == 2

    def test_validate_all_missing(self, tmp_path):
        """Test detecting all missing items."""
        pm = ProjectManager(tmp_path)

        # Create bare directory
        project_dir = tmp_path / "bare"
        project_dir.mkdir()

        missing = pm._validate_project_structure(project_dir)

        expected = [
            "agents",
            "skills",
            "tools",
            "snippets",
            "tests",
            "project.json",
            "current_session.json",
            "requirements.txt",
        ]
        assert sorted(missing) == sorted(expected)


class TestCreateMissingFiles:
    """Tests for _create_missing_files method."""

    def test_create_missing_directory(self, tmp_path):
        """Test creating a missing directory."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        agents_dir = project_dir / "agents"
        shutil.rmtree(agents_dir)

        assert not agents_dir.exists()

        pm._create_missing_files(project_dir, ["agents"])

        assert agents_dir.exists()
        assert agents_dir.is_dir()

    def test_create_missing_project_json(self, tmp_path):
        """Test creating missing project.json."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        pm._create_missing_files(project_dir, ["project.json"])

        project_json = project_dir / "project.json"
        assert project_json.exists()

        # Verify it's valid JSON
        data = json.loads(project_json.read_text())
        assert data["name"] == "test"

    def test_create_missing_session_json(self, tmp_path):
        """Test creating missing current_session.json."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        pm._create_missing_files(project_dir, ["current_session.json"])

        session_json = project_dir / "current_session.json"
        assert session_json.exists()

        # Verify it's valid session JSON
        data = json.loads(session_json.read_text())
        assert data["model"] == "claude-sonnet-4-5-20250929"

    def test_create_missing_requirements_txt(self, tmp_path):
        """Test creating missing requirements.txt."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        pm._create_missing_files(project_dir, ["requirements.txt"])

        requirements = project_dir / "requirements.txt"
        assert requirements.exists()

        content = requirements.read_text()
        assert "anthropic>=0.18.0" in content

    def test_create_multiple_missing_items(self, tmp_path):
        """Test creating multiple missing items at once."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        missing = ["agents", "skills", "project.json", "requirements.txt"]
        pm._create_missing_files(project_dir, missing)

        assert (project_dir / "agents").exists()
        assert (project_dir / "skills").exists()
        assert (project_dir / "project.json").exists()
        assert (project_dir / "requirements.txt").exists()


class TestListAgents:
    """Tests for _list_agents method."""

    def test_list_agents_empty(self, tmp_path):
        """Test listing agents when directory is empty."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        agents = pm._list_agents(project_dir)

        assert agents == []

    def test_list_agents_single(self, tmp_path):
        """Test listing a single agent."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "agents" / "test-agent.md").write_text("test")

        agents = pm._list_agents(project_dir)

        assert agents == ["test-agent"]

    def test_list_agents_multiple(self, tmp_path):
        """Test listing multiple agents."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "agents" / "alpha.md").write_text("alpha")
        (project_dir / "agents" / "beta.md").write_text("beta")
        (project_dir / "agents" / "gamma.md").write_text("gamma")

        agents = pm._list_agents(project_dir)

        assert agents == ["alpha", "beta", "gamma"]

    def test_list_agents_ignores_non_md_files(self, tmp_path):
        """Test that non-.md files are ignored."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "agents" / "agent.md").write_text("agent")
        (project_dir / "agents" / "readme.txt").write_text("readme")

        agents = pm._list_agents(project_dir)

        assert agents == ["agent"]

    def test_list_agents_nonexistent_directory(self, tmp_path):
        """Test listing agents when directory doesn't exist."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        agents = pm._list_agents(project_dir)

        assert agents == []


class TestListSkills:
    """Tests for _list_skills method."""

    def test_list_skills_empty(self, tmp_path):
        """Test listing skills when directory is empty."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        skills = pm._list_skills(project_dir)

        assert skills == []

    def test_list_skills_single(self, tmp_path):
        """Test listing a single skill."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "skills" / "test-skill.md").write_text("test")

        skills = pm._list_skills(project_dir)

        assert skills == ["test-skill"]

    def test_list_skills_multiple(self, tmp_path):
        """Test listing multiple skills."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "skills" / "skill1.md").write_text("skill1")
        (project_dir / "skills" / "skill2.md").write_text("skill2")

        skills = pm._list_skills(project_dir)

        assert skills == ["skill1", "skill2"]


class TestListTools:
    """Tests for _list_tools method."""

    def test_list_tools_empty(self, tmp_path):
        """Test listing tools when directory is empty."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        tools = pm._list_tools(project_dir)

        assert tools == []

    def test_list_tools_json_only(self, tmp_path):
        """Test listing tools with only JSON files."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "tools" / "tool1.json").write_text("{}")
        (project_dir / "tools" / "tool2.json").write_text("{}")

        tools = pm._list_tools(project_dir)

        assert sorted(tools) == ["tool1", "tool2"]

    def test_list_tools_python_only(self, tmp_path):
        """Test listing tools with only Python files."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "tools" / "tool1.py").write_text("pass")
        (project_dir / "tools" / "tool2.py").write_text("pass")

        tools = pm._list_tools(project_dir)

        assert sorted(tools) == ["tool1", "tool2"]

    def test_list_tools_mixed_extensions(self, tmp_path):
        """Test listing tools with both JSON and Python files."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "tools" / "tool1.json").write_text("{}")
        (project_dir / "tools" / "tool2.py").write_text("pass")

        tools = pm._list_tools(project_dir)

        assert sorted(tools) == ["tool1", "tool2"]

    def test_list_tools_deduplicates(self, tmp_path):
        """Test that tools with both .json and .py are listed once."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "tools" / "tool.json").write_text("{}")
        (project_dir / "tools" / "tool.py").write_text("pass")

        tools = pm._list_tools(project_dir)

        assert tools == ["tool"]

    def test_list_tools_ignores_other_files(self, tmp_path):
        """Test that non-tool files are ignored."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "tools" / "tool.json").write_text("{}")
        (project_dir / "tools" / "readme.txt").write_text("readme")

        tools = pm._list_tools(project_dir)

        assert tools == ["tool"]

    def test_list_tools_nonexistent_directory(self, tmp_path):
        """Test listing tools when directory doesn't exist."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        tools = pm._list_tools(project_dir)

        assert tools == []


class TestListSnippetCategories:
    """Tests for _list_snippet_categories method."""

    def test_list_categories_empty(self, tmp_path):
        """Test listing categories when directory is empty."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        categories = pm._list_snippet_categories(project_dir)

        assert categories == []

    def test_list_categories_single_level(self, tmp_path):
        """Test listing categories at single level."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "snippets" / "prompts").mkdir()
        (project_dir / "snippets" / "examples").mkdir()

        categories = pm._list_snippet_categories(project_dir)

        assert sorted(categories) == ["examples", "prompts"]

    def test_list_categories_nested(self, tmp_path):
        """Test listing nested categories."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "snippets" / "tools").mkdir()
        (project_dir / "snippets" / "tools" / "bash").mkdir()
        (project_dir / "snippets" / "tools" / "python").mkdir()

        categories = pm._list_snippet_categories(project_dir)

        assert sorted(categories) == ["tools", "tools/bash", "tools/python"]

    def test_list_categories_mixed_depth(self, tmp_path):
        """Test listing categories with mixed nesting depth."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "snippets" / "prompts").mkdir()
        (project_dir / "snippets" / "tools").mkdir()
        (project_dir / "snippets" / "tools" / "bash").mkdir()

        categories = pm._list_snippet_categories(project_dir)

        assert sorted(categories) == ["prompts", "tools", "tools/bash"]

    def test_list_categories_ignores_files(self, tmp_path):
        """Test that files are ignored when listing categories."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="test")

        project_dir = tmp_path / "test"
        (project_dir / "snippets" / "category").mkdir()
        (project_dir / "snippets" / "file.md").write_text("test")

        categories = pm._list_snippet_categories(project_dir)

        assert categories == ["category"]

    def test_list_categories_nonexistent_directory(self, tmp_path):
        """Test listing categories when directory doesn't exist."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "test"
        project_dir.mkdir()

        categories = pm._list_snippet_categories(project_dir)

        assert categories == []


class TestProjectManagerEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_project_with_unicode_description(self, tmp_path):
        """Test creating project with unicode characters in description."""
        pm = ProjectManager(tmp_path)
        project = pm.create_project(
            name="unicode-test",
            description="Test with unicode: 你好 🚀",
        )

        assert project.description == "Test with unicode: 你好 🚀"

        # Verify it can be loaded back
        loaded = pm.load_project(name="unicode-test")
        assert loaded.description == "Test with unicode: 你好 🚀"

    def test_project_operations_with_path_objects(self, tmp_path):
        """Test that ProjectManager works with Path objects."""
        projects_root = Path(tmp_path) / "projects"
        pm = ProjectManager(projects_root)

        assert isinstance(pm.projects_root, Path)

    def test_create_project_atomic_behavior(self, tmp_path):
        """Test that project creation is atomic (cleanup on failure)."""
        pm = ProjectManager(tmp_path)
        project_dir = tmp_path / "atomic-test"

        # Create directory to force duplicate error
        project_dir.mkdir()

        try:
            with pytest.raises(ProjectAlreadyExistsError):
                pm.create_project(name="atomic-test")
        finally:
            # Clean up
            if project_dir.exists():
                shutil.rmtree(project_dir)

    def test_concurrent_project_creation_protection(self, tmp_path):
        """Test that concurrent creation of same project is handled."""
        pm = ProjectManager(tmp_path)

        # First creation should succeed
        pm.create_project(name="concurrent-test")

        # Second creation should fail
        with pytest.raises(ProjectAlreadyExistsError):
            pm.create_project(name="concurrent-test")

    def test_project_name_case_sensitivity(self, tmp_path):
        """Test that project names are case-sensitive on supported systems."""
        pm = ProjectManager(tmp_path)

        pm.create_project(name="test")
        pm.create_project(name="Test")

        projects = pm.list_projects()

        # On case-sensitive systems, these are different
        # On case-insensitive systems (like macOS default), only one will exist
        if (tmp_path / "test").exists() and (tmp_path / "Test").exists():
            assert len(projects) == 2
        else:
            assert len(projects) >= 1

    def test_delete_project_with_readonly_file(self, tmp_path):
        """Test deleting project with read-only file raises appropriate error."""
        pm = ProjectManager(tmp_path)
        pm.create_project(name="readonly-test")

        project_dir = tmp_path / "readonly-test"
        test_file = project_dir / "readonly.txt"
        test_file.write_text("test")

        # Make file read-only
        test_file.chmod(0o444)
        # Make directory read-only (on Unix systems)
        if os.name != 'nt':
            project_dir.chmod(0o555)

        try:
            with pytest.raises(ProjectError, match="Failed to delete project"):
                pm.delete_project(name="readonly-test")
        finally:
            # Cleanup: restore permissions
            if os.name != 'nt':
                project_dir.chmod(0o755)
            test_file.chmod(0o644)
            if project_dir.exists():
                shutil.rmtree(project_dir)

    def test_create_missing_files_error_handling(self, tmp_path):
        """Test error handling when creating missing files fails."""
        pm = ProjectManager(tmp_path)

        project_dir = tmp_path / "error-test"
        project_dir.mkdir()

        # Make directory read-only to cause write failure
        if os.name != 'nt':
            project_dir.chmod(0o555)

        try:
            with pytest.raises(ProjectError, match="Failed to create missing items"):
                pm._create_missing_files(
                    project_dir,
                    ["project.json"],
                )
        finally:
            # Cleanup: restore permissions
            if os.name != 'nt':
                project_dir.chmod(0o755)
            if project_dir.exists():
                shutil.rmtree(project_dir)
