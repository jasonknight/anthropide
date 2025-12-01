"""
Project management operations for AnthropIDE.

This module provides the ProjectManager class for CRUD operations on projects,
including creating project structure, listing projects, loading/validating projects,
and managing project directories.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from lib.data_models import Project, ProjectSettings, Session, SystemBlock
from lib.file_operations import (
    safe_read_json,
    safe_write_json,
    ensure_directory,
    FileReadError,
    FileWriteError,
    FileOperationError,
)

logger = logging.getLogger(__name__)


class ProjectError(Exception):
    """Base exception for project operations."""
    pass


class ProjectNotFoundError(ProjectError):
    """Exception raised when project does not exist."""
    pass


class ProjectAlreadyExistsError(ProjectError):
    """Exception raised when attempting to create duplicate project."""
    pass


class ProjectValidationError(ProjectError):
    """Exception raised when project structure is invalid."""
    pass


class ProjectManager:
    """
    Manages project CRUD operations.

    This class handles creating, reading, updating, and deleting projects,
    as well as validating project structure and managing project metadata.

    Attributes:
        projects_root: Path to the root directory containing all projects
    """

    def __init__(self, projects_root: Path):
        """
        Initialize ProjectManager with projects directory.

        Args:
            projects_root: Path to directory containing all projects

        Raises:
            FileOperationError: If projects root cannot be created or accessed
        """
        self.projects_root = Path(projects_root)
        ensure_directory(self.projects_root)
        logger.info(f"ProjectManager initialized with root: {self.projects_root}")

    def list_projects(self) -> List[Project]:
        """
        List all projects in the projects directory.

        Returns:
            List of Project objects sorted by name

        Raises:
            ProjectError: If project metadata cannot be loaded
        """
        projects = []

        # Iterate through all directories in projects root
        for project_dir in sorted(self.projects_root.iterdir()):
            if not project_dir.is_dir():
                continue

            # Skip hidden directories
            if project_dir.name.startswith('.'):
                continue

            try:
                # Load project metadata
                project = self.load_project_metadata(project_dir.name)
                projects.append(project)
            except ProjectError as e:
                logger.warning(
                    f"Skipping project {project_dir.name}: {e}",
                )
                continue

        logger.info(f"Listed {len(projects)} projects")
        return projects

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Project:
        """
        Create a new project with complete directory structure.

        Creates:
        - Project directory
        - project.json with metadata
        - current_session.json with minimal valid session
        - requirements.txt with default dependencies
        - agents/ directory
        - skills/ directory
        - tools/ directory
        - snippets/ directory
        - tests/ directory

        Args:
            name: Project name (must be unique and valid)
            description: Optional project description

        Returns:
            Created Project object

        Raises:
            ProjectAlreadyExistsError: If project already exists
            ProjectError: If project cannot be created
        """
        # Validate project name using Project model
        now = datetime.now()
        try:
            project = Project(
                name=name,
                description=description,
                created=now,
                modified=now,
                settings=ProjectSettings(),
            )
        except ValueError as e:
            raise ProjectError(f"Invalid project name: {e}") from e

        project_path = self.projects_root / name

        # Check if project already exists
        if project_path.exists():
            raise ProjectAlreadyExistsError(
                f"Project '{name}' already exists",
            )

        logger.info(f"Creating project: {name}")

        try:
            # Create project directory
            ensure_directory(project_path)

            # Create subdirectories
            ensure_directory(project_path / 'agents')
            ensure_directory(project_path / 'skills')
            ensure_directory(project_path / 'tools')
            ensure_directory(project_path / 'snippets')
            ensure_directory(project_path / 'tests')

            # Create project.json
            project_data = project.model_dump(mode='json')
            safe_write_json(
                path=project_path / 'project.json',
                data=project_data,
            )

            # Create default current_session.json
            default_session = Session(
                model=project.settings.default_model,
                max_tokens=8192,
                temperature=1.0,
                system=[],
                tools=[],
                messages=[],
            )
            safe_write_json(
                path=project_path / 'current_session.json',
                data=default_session.model_dump(mode='json'),
            )

            # Create default requirements.txt
            requirements_content = "anthropic>=0.18.0\n"
            requirements_path = project_path / 'requirements.txt'
            requirements_path.write_text(
                requirements_content,
                encoding='utf-8',
            )

            logger.info(f"Successfully created project: {name}")
            return project

        except (FileOperationError, OSError, IOError) as e:
            # Clean up on failure
            if project_path.exists():
                try:
                    shutil.rmtree(project_path)
                    logger.warning(
                        f"Cleaned up failed project creation: {project_path}",
                    )
                except (OSError, IOError) as cleanup_error:
                    logger.error(
                        f"Failed to clean up project directory: {cleanup_error}",
                    )

            raise ProjectError(
                f"Failed to create project '{name}': {e}",
            ) from e

    def load_project(self, name: str) -> Project:
        """
        Load project and validate its structure.

        Validates that all required directories and files exist.
        If any are missing, they will be created.

        Args:
            name: Project name

        Returns:
            Loaded and validated Project object

        Raises:
            ProjectNotFoundError: If project does not exist
            ProjectError: If project cannot be loaded or validated
        """
        project_path = self.projects_root / name

        if not project_path.exists():
            raise ProjectNotFoundError(f"Project '{name}' does not exist")

        if not project_path.is_dir():
            raise ProjectError(f"Project '{name}' is not a directory")

        logger.info(f"Loading project: {name}")

        # Load project metadata
        project = self.load_project_metadata(name)

        # Validate project structure
        missing = self._validate_project_structure(project_path)

        if missing:
            logger.warning(
                f"Project '{name}' has missing files/directories: {missing}",
            )
            # Create missing files and directories
            self._create_missing_files(project_path, missing)

        return project

    def load_project_metadata(self, name: str) -> Project:
        """
        Load project metadata from project.json.

        Args:
            name: Project name

        Returns:
            Project object

        Raises:
            ProjectNotFoundError: If project does not exist
            ProjectError: If metadata cannot be loaded or is invalid
        """
        project_path = self.projects_root / name

        if not project_path.exists():
            raise ProjectNotFoundError(f"Project '{name}' does not exist")

        metadata_path = project_path / 'project.json'

        if not metadata_path.exists():
            raise ProjectError(
                f"Project '{name}' is missing project.json",
            )

        try:
            data = safe_read_json(metadata_path)
            if data is None:
                raise ProjectError(
                    f"Project '{name}' has empty or invalid project.json",
                )

            # Parse with Pydantic for validation
            project = Project(**data)

            logger.debug(f"Loaded project metadata: {name}")
            return project

        except FileReadError as e:
            raise ProjectError(
                f"Failed to read project metadata for '{name}': {e}",
            ) from e
        except ValueError as e:
            raise ProjectError(
                f"Invalid project metadata for '{name}': {e}",
            ) from e

    def delete_project(self, name: str) -> None:
        """
        Delete a project and all its contents.

        Args:
            name: Project name

        Raises:
            ProjectNotFoundError: If project does not exist
            ProjectError: If project cannot be deleted
        """
        project_path = self.projects_root / name

        if not project_path.exists():
            raise ProjectNotFoundError(f"Project '{name}' does not exist")

        logger.info(f"Deleting project: {name}")

        try:
            shutil.rmtree(project_path)
            logger.info(f"Successfully deleted project: {name}")
        except (OSError, IOError) as e:
            raise ProjectError(
                f"Failed to delete project '{name}': {e}",
            ) from e

    def _validate_project_structure(self, project_path: Path) -> List[str]:
        """
        Validate project structure and return list of missing items.

        Args:
            project_path: Path to project directory

        Returns:
            List of missing file/directory paths (relative to project root)
        """
        missing = []

        # Required directories
        required_dirs = [
            'agents',
            'skills',
            'tools',
            'snippets',
            'tests',
        ]

        for dir_name in required_dirs:
            dir_path = project_path / dir_name
            if not dir_path.exists():
                missing.append(dir_name)

        # Required files
        required_files = [
            'project.json',
            'current_session.json',
            'requirements.txt',
        ]

        for file_name in required_files:
            file_path = project_path / file_name
            if not file_path.exists():
                missing.append(file_name)

        return missing

    def _create_missing_files(
        self,
        project_path: Path,
        missing: List[str],
    ) -> None:
        """
        Create missing files and directories in project structure.

        Args:
            project_path: Path to project directory
            missing: List of missing file/directory paths

        Raises:
            ProjectError: If missing items cannot be created
        """
        logger.info(
            f"Creating missing items for {project_path.name}: {missing}",
        )

        try:
            for item in missing:
                item_path = project_path / item

                # Check if it's a directory (no extension)
                if '.' not in item:
                    ensure_directory(item_path)
                    logger.debug(f"Created directory: {item}")

                elif item == 'project.json':
                    # Create minimal project.json
                    now = datetime.now()
                    project = Project(
                        name=project_path.name,
                        description=None,
                        created=now,
                        modified=now,
                        settings=ProjectSettings(),
                    )
                    safe_write_json(
                        path=item_path,
                        data=project.model_dump(mode='json'),
                    )
                    logger.debug(f"Created file: {item}")

                elif item == 'current_session.json':
                    # Create minimal session with model from project settings
                    # Load project metadata to get default model
                    project_json_path = project_path / 'project.json'
                    model = 'claude-sonnet-4-5-20250929'  # fallback
                    if project_json_path.exists():
                        try:
                            project_data = safe_read_json(project_json_path)
                            if project_data and 'settings' in project_data:
                                model = project_data['settings'].get(
                                    'default_model',
                                    'claude-sonnet-4-5-20250929',
                                )
                        except Exception as e:
                            logger.warning(
                                f"Could not load project settings for model: {e}, "
                                f"using default model",
                            )

                    default_session = Session(
                        model=model,
                        max_tokens=8192,
                        temperature=1.0,
                        system=[],
                        tools=[],
                        messages=[],
                    )
                    safe_write_json(
                        path=item_path,
                        data=default_session.model_dump(mode='json'),
                    )
                    logger.debug(f"Created file: {item}")

                elif item == 'requirements.txt':
                    # Create default requirements.txt
                    requirements_content = "anthropic>=0.18.0\n"
                    item_path.write_text(
                        requirements_content,
                        encoding='utf-8',
                    )
                    logger.debug(f"Created file: {item}")

        except (FileOperationError, OSError, IOError) as e:
            raise ProjectError(
                f"Failed to create missing items: {e}",
            ) from e

    def _list_agents(self, project_path: Path) -> List[str]:
        """
        List all agent names in project.

        Args:
            project_path: Path to project directory

        Returns:
            List of agent names (without .md extension), sorted
        """
        agents_dir = project_path / 'agents'

        if not agents_dir.exists():
            return []

        agents = []
        for agent_file in agents_dir.glob('*.md'):
            agents.append(agent_file.stem)

        return sorted(agents)

    def _list_skills(self, project_path: Path) -> List[str]:
        """
        List all skill names in project.

        Args:
            project_path: Path to project directory

        Returns:
            List of skill names (without .md extension), sorted
        """
        skills_dir = project_path / 'skills'

        if not skills_dir.exists():
            return []

        skills = []
        for skill_file in skills_dir.glob('*.md'):
            skills.append(skill_file.stem)

        return sorted(skills)

    def _list_tools(self, project_path: Path) -> List[str]:
        """
        List all tool names in project.

        Args:
            project_path: Path to project directory

        Returns:
            List of tool names (without extension), sorted
        """
        tools_dir = project_path / 'tools'

        if not tools_dir.exists():
            return []

        tools = []

        # Find both .json and .py files
        for tool_file in tools_dir.glob('*'):
            if tool_file.suffix in ['.json', '.py']:
                tools.append(tool_file.stem)

        # Remove duplicates and sort
        return sorted(set(tools))

    def _list_snippet_categories(self, project_path: Path) -> List[str]:
        """
        List all snippet categories (directory paths) in project.

        Returns categories as relative paths from snippets/ directory.
        Supports nested categories up to 2 levels deep.

        Args:
            project_path: Path to project directory

        Returns:
            List of category paths (e.g., ['prompts', 'tools/bash', 'tools/python']), sorted
        """
        snippets_dir = project_path / 'snippets'

        if not snippets_dir.exists():
            return []

        categories = set()

        # Walk through snippets directory
        for item in snippets_dir.rglob('*'):
            if item.is_dir():
                # Get relative path from snippets directory
                rel_path = item.relative_to(snippets_dir)
                categories.add(str(rel_path))

        return sorted(categories)
