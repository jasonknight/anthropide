"""
Skill management operations for AnthropIDE.

This module provides the SkillManager class for loading, parsing, and managing
skills from markdown files with YAML frontmatter. Skills are instructional
markdown documents that teach agents how to accomplish complex workflows.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

from lib.data_models import SkillConfig
from lib.file_operations import (
    safe_read_file,
    safe_write_file,
    safe_delete_file,
    FileReadError,
    FileWriteError,
    FileDeleteError,
    FileOperationError,
)

logger = logging.getLogger(__name__)


class SkillError(Exception):
    """Base exception for skill operations."""
    pass


class SkillNotFoundError(SkillError):
    """Exception raised when skill does not exist."""
    pass


class SkillLoadError(SkillError):
    """Exception raised when skill cannot be loaded."""
    pass


class SkillValidationError(SkillError):
    """Exception raised when skill definition is invalid."""
    pass


class SkillManager:
    """
    Manages skill loading, parsing, and CRUD operations.

    Skills are markdown files with YAML frontmatter stored in the project's
    skills/ directory. This class handles parsing the YAML frontmatter,
    extracting markdown content, validation, and caching.

    Attributes:
        project_path: Path to the project directory
        skills_dir: Path to the skills/ directory within the project
        _skill_cache: Cache of loaded skills {skill_name: SkillConfig}
    """

    def __init__(self, project_path: Path):
        """
        Initialize SkillManager with project skills directory.

        Args:
            project_path: Path to the project directory

        Raises:
            FileOperationError: If skills directory cannot be accessed
        """
        self.project_path = Path(project_path)
        self.skills_dir = self.project_path / "skills"
        self._skill_cache: Dict[str, SkillConfig] = {}

        # Ensure skills directory exists
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created skills directory: {self.skills_dir}")

        logger.info(f"SkillManager initialized for project: {self.project_path}")

    def load_skills(self) -> Dict[str, SkillConfig]:
        """
        Load all skills from the skills/ directory.

        Scans the skills directory for .md files, loads each skill,
        validates it, and caches the result. Skills are loaded in alphabetical
        order for consistency.

        Returns:
            Dictionary mapping skill names to SkillConfig objects

        Raises:
            SkillError: If critical errors occur during loading
        """
        logger.info(f"Loading skills from {self.skills_dir}")

        # Clear cache to ensure fresh load
        self._skill_cache.clear()

        # Get all markdown files
        skill_files = sorted(self.skills_dir.glob("*.md"))

        loaded_count = 0
        error_count = 0

        for skill_file in skill_files:
            try:
                skill_config = self.load_skill(skill_file.stem)
                self._skill_cache[skill_config.name] = skill_config
                loaded_count += 1
                logger.debug(f"Loaded skill: {skill_config.name}")
            except SkillError as e:
                error_count += 1
                logger.warning(
                    f"Failed to load skill from {skill_file.name}: {e}",
                )

        logger.info(
            f"Loaded {loaded_count} skills successfully, "
            f"{error_count} errors",
        )

        return self._skill_cache.copy()

    def load_skill(self, name: str) -> SkillConfig:
        """
        Load a single skill by name.

        Args:
            name: Skill name (without .md extension)

        Returns:
            SkillConfig object

        Raises:
            SkillNotFoundError: If skill file does not exist
            SkillLoadError: If skill file cannot be read or parsed
            SkillValidationError: If skill structure is invalid
        """
        # Check cache first
        if name in self._skill_cache:
            logger.debug(f"Returning cached skill: {name}")
            return self._skill_cache[name]

        skill_file = self.skills_dir / f"{name}.md"

        if not skill_file.exists():
            raise SkillNotFoundError(f"Skill '{name}' not found at {skill_file}")

        try:
            content = safe_read_file(skill_file)
        except FileReadError as e:
            raise SkillLoadError(
                f"Failed to read skill file '{name}': {e}",
            ) from e

        # Parse the skill
        try:
            skill_config = self.parse_skill(content)
        except (ValueError, yaml.YAMLError) as e:
            raise SkillLoadError(
                f"Failed to parse skill '{name}': {e}",
            ) from e
        except ValidationError as e:
            raise SkillValidationError(
                f"Invalid skill structure in '{name}': {e}",
            ) from e

        # Verify the name matches the filename
        if skill_config.name != name:
            logger.warning(
                f"Skill name mismatch: filename '{name}' vs "
                f"YAML name '{skill_config.name}'. Using filename.",
            )
            # Update the name to match filename for consistency
            skill_config.name = name

        # Cache the loaded skill
        self._skill_cache[name] = skill_config

        logger.info(f"Loaded skill: {name}")
        return skill_config

    def parse_skill(self, content: str) -> SkillConfig:
        """
        Parse skill markdown content with YAML frontmatter.

        Expected format:
        ---
        name: skill-name
        description: Skill description
        version: 1.0.0
        author: Optional Author
        ---

        Markdown content here...

        Args:
            content: Raw markdown file content with YAML frontmatter

        Returns:
            SkillConfig object

        Raises:
            ValueError: If content format is invalid
            yaml.YAMLError: If YAML parsing fails
            ValidationError: If required fields are missing or invalid
        """
        # Split frontmatter and content using regex
        # Pattern matches: start of string, "---", content, "---", rest
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            raise ValueError(
                "Invalid skill format: missing YAML frontmatter. "
                "Expected format: ---\\nYAML\\n---\\nMarkdown content",
            )

        yaml_content = match.group(1)
        markdown_content = match.group(2).rstrip('\n')

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML frontmatter: {e}") from e

        if not isinstance(frontmatter, dict):
            raise ValueError(
                "YAML frontmatter must be a dictionary",
            )

        # Validate required fields
        required_fields = ['name', 'description']
        missing_fields = [
            field for field in required_fields
            if field not in frontmatter
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required fields in YAML frontmatter: "
                f"{', '.join(missing_fields)}",
            )

        # Build SkillConfig with frontmatter data and markdown content
        skill_data = {
            'name': frontmatter['name'],
            'description': frontmatter['description'],
            'version': frontmatter.get('version', '1.0.0'),
            'author': frontmatter.get('author'),
            'content': markdown_content,
        }

        # Let Pydantic validate the structure
        return SkillConfig(**skill_data)

    def save_skill(self, skill_config: SkillConfig) -> None:
        """
        Save a skill to file.

        Creates or updates a skill markdown file with YAML frontmatter.
        The skill is saved to skills/<name>.md.

        Args:
            skill_config: SkillConfig object to save

        Raises:
            SkillValidationError: If skill config is invalid
            SkillError: If file cannot be written
        """
        # Validate the skill config
        try:
            skill_config.model_validate(skill_config.model_dump())
        except ValidationError as e:
            raise SkillValidationError(
                f"Invalid skill configuration: {e}",
            ) from e

        # Build the file content
        frontmatter = {
            'name': skill_config.name,
            'description': skill_config.description,
            'version': skill_config.version,
        }

        # Add author if present
        if skill_config.author:
            frontmatter['author'] = skill_config.author

        # Convert to YAML string
        yaml_str = yaml.safe_dump(
            frontmatter,
            default_flow_style=False,
            sort_keys=False,
        ).strip()

        # Combine frontmatter and content
        # Ensure content ends with single newline for clean file formatting
        content = skill_config.content.rstrip('\n') + '\n'
        file_content = f"---\n{yaml_str}\n---\n\n{content}"

        # Write to file
        skill_file = self.skills_dir / f"{skill_config.name}.md"

        try:
            safe_write_file(skill_file, file_content)
        except FileWriteError as e:
            raise SkillError(
                f"Failed to write skill file '{skill_config.name}': {e}",
            ) from e

        # Update cache
        self._skill_cache[skill_config.name] = skill_config

        logger.info(f"Saved skill: {skill_config.name}")

    def delete_skill(self, name: str) -> None:
        """
        Delete a skill file.

        Args:
            name: Skill name (without .md extension)

        Raises:
            SkillNotFoundError: If skill file does not exist
            SkillError: If file cannot be deleted
        """
        skill_file = self.skills_dir / f"{name}.md"

        if not skill_file.exists():
            raise SkillNotFoundError(
                f"Skill '{name}' not found at {skill_file}",
            )

        try:
            safe_delete_file(skill_file)
        except FileDeleteError as e:
            raise SkillError(
                f"Failed to delete skill file '{name}': {e}",
            ) from e

        # Remove from cache
        if name in self._skill_cache:
            del self._skill_cache[name]

        logger.info(f"Deleted skill: {name}")

    def list_skills(self) -> List[str]:
        """
        List all available skill names.

        Returns list of skill names by scanning the skills/ directory
        for .md files. Does not load or validate the skills.

        Returns:
            List of skill names (without .md extension)
        """
        skill_files = sorted(self.skills_dir.glob("*.md"))
        skill_names = [f.stem for f in skill_files]

        logger.debug(f"Found {len(skill_names)} skills")
        return skill_names

    def get_skill(self, name: str) -> SkillConfig:
        """
        Get a skill by name.

        This is an alias for load_skill() that provides a more intuitive
        method name for retrieving skills.

        Args:
            name: Skill name (without .md extension)

        Returns:
            SkillConfig object

        Raises:
            SkillNotFoundError: If skill does not exist
            SkillLoadError: If skill cannot be loaded
            SkillValidationError: If skill structure is invalid
        """
        return self.load_skill(name)

    def clear_cache(self) -> None:
        """
        Clear the skill cache.

        Forces all skills to be reloaded on next access. Useful when
        skills are modified externally or during testing.
        """
        self._skill_cache.clear()
        logger.debug("Skill cache cleared")
