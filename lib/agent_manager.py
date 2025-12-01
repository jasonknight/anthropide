"""
Agent management operations for AnthropIDE.

This module provides the AgentManager class for loading, parsing, and managing
agents from markdown files with YAML frontmatter. Agents are specialized AI
assistants that can be spawned dynamically during execution with their own
system prompts, tools, and skills.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
from pydantic import ValidationError

from lib.data_models import AgentConfig
from lib.file_operations import (
    safe_read_file,
    safe_write_file,
    safe_delete_file,
    FileReadError,
    FileWriteError,
    FileDeleteError,
    FileOperationError,
)
import config

logger = logging.getLogger(__name__)


# Valid Claude model IDs (as of January 2025)
VALID_MODELS = {
    'claude-sonnet-4-5-20250929',
    'claude-3-5-sonnet-20241022',
    'claude-3-opus-20240229',
    'claude-3-haiku-20240307',
    'inherit',  # Special value to inherit from parent session
}


class AgentError(Exception):
    """Base exception for agent operations."""
    pass


class AgentNotFoundError(AgentError):
    """Exception raised when agent does not exist."""
    pass


class AgentLoadError(AgentError):
    """Exception raised when agent cannot be loaded."""
    pass


class AgentValidationError(AgentError):
    """Exception raised when agent definition is invalid."""
    pass


class AgentManager:
    """
    Manages agent loading, parsing, validation, and CRUD operations.

    Agents are markdown files with YAML frontmatter stored in the project's
    agents/ directory. This class handles parsing the YAML frontmatter,
    extracting markdown content, validation (including tool/skill references),
    and caching.

    Attributes:
        project_path: Path to the project directory
        agents_dir: Path to the agents/ directory within the project
        skill_manager: SkillManager instance for validating skill references
        tool_manager: ToolManager instance for validating tool references
        _agent_cache: Cache of loaded agents {agent_name: AgentConfig}
    """

    def __init__(
        self,
        project_path: Path,
        skill_manager,
        tool_manager,
    ):
        """
        Initialize AgentManager with project agents directory and managers.

        Args:
            project_path: Path to the project directory
            skill_manager: SkillManager instance for validating skill references
            tool_manager: ToolManager instance for validating tool references

        Raises:
            FileOperationError: If agents directory cannot be accessed
        """
        self.project_path = Path(project_path)
        self.agents_dir = self.project_path / "agents"
        self.skill_manager = skill_manager
        self.tool_manager = tool_manager
        self._agent_cache: Dict[str, AgentConfig] = {}

        # Ensure agents directory exists
        if not self.agents_dir.exists():
            self.agents_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created agents directory: {self.agents_dir}")

        logger.info(f"AgentManager initialized for project: {self.project_path}")

    def load_agents(self) -> Dict[str, AgentConfig]:
        """
        Load all agents from the agents/ directory.

        Scans the agents directory for .md files, loads each agent,
        validates it (including tool/skill references), and caches the result.
        Agents are loaded in alphabetical order for consistency.

        Returns:
            Dictionary mapping agent names to AgentConfig objects

        Raises:
            AgentError: If critical errors occur during loading
        """
        logger.info(f"Loading agents from {self.agents_dir}")

        # Clear cache to ensure fresh load
        self._agent_cache.clear()

        # Get all markdown files
        agent_files = sorted(self.agents_dir.glob(f"*{config.AGENT_EXT}"))

        loaded_count = 0
        error_count = 0

        for agent_file in agent_files:
            try:
                agent_config = self.load_agent(agent_file.stem)
                self._agent_cache[agent_config.name] = agent_config
                loaded_count += 1
                logger.debug(f"Loaded agent: {agent_config.name}")
            except AgentError as e:
                error_count += 1
                logger.warning(
                    f"Failed to load agent from {agent_file.name}: {e}",
                )

        logger.info(
            f"Loaded {loaded_count} agents successfully, "
            f"{error_count} errors",
        )

        return self._agent_cache.copy()

    def load_agent(self, name: str) -> AgentConfig:
        """
        Load a single agent by name.

        Args:
            name: Agent name (without .md extension)

        Returns:
            AgentConfig object

        Raises:
            AgentNotFoundError: If agent file does not exist
            AgentLoadError: If agent file cannot be read or parsed
            AgentValidationError: If agent structure is invalid
        """
        # Check cache first
        if name in self._agent_cache:
            logger.debug(f"Returning cached agent: {name}")
            return self._agent_cache[name]

        agent_file = self.agents_dir / f"{name}{config.AGENT_EXT}"

        if not agent_file.exists():
            raise AgentNotFoundError(f"Agent '{name}' not found at {agent_file}")

        try:
            content = safe_read_file(agent_file)
        except FileReadError as e:
            raise AgentLoadError(
                f"Failed to read agent file '{name}': {e}",
            ) from e

        # Parse the agent
        try:
            agent_config = self.parse_agent(content)
        except (ValueError, yaml.YAMLError) as e:
            raise AgentLoadError(
                f"Failed to parse agent '{name}': {e}",
            ) from e
        except ValidationError as e:
            raise AgentValidationError(
                f"Invalid agent structure in '{name}': {e}",
            ) from e

        # Verify the name matches the filename
        if agent_config.name != name:
            logger.warning(
                f"Agent name mismatch: filename '{name}' vs "
                f"YAML name '{agent_config.name}'. Using filename.",
            )
            # Update the name to match filename for consistency
            agent_config.name = name

        # Validate the agent references (tools and skills)
        try:
            self.validate_agent(agent_config)
        except AgentValidationError as e:
            raise AgentValidationError(
                f"Validation failed for agent '{name}': {e}",
            ) from e

        # Cache the loaded agent
        self._agent_cache[name] = agent_config

        logger.info(f"Loaded agent: {name}")
        return agent_config

    def parse_agent(self, content: str) -> AgentConfig:
        """
        Parse agent markdown content with YAML frontmatter.

        Expected format:
        ---
        name: agent-name
        description: |
          Multi-line description of when and why to use this agent.
          Invoke after completing a significant piece of code.
        model: inherit
        tools: Read, Grep, Glob
        skills: code-analysis, security-scan
        color: blue
        ---

        Agent system prompt markdown content here...

        Args:
            content: Raw markdown file content with YAML frontmatter

        Returns:
            AgentConfig object

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
                "Invalid agent format: missing YAML frontmatter. "
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

        # Parse tools field (comma-separated string to list)
        tools_str = frontmatter.get('tools', '')
        if isinstance(tools_str, str):
            # Split by comma and strip whitespace
            tools = [
                tool.strip()
                for tool in tools_str.split(',')
                if tool.strip()
            ]
        elif isinstance(tools_str, list):
            # Already a list
            tools = [str(tool).strip() for tool in tools_str if tool]
        else:
            tools = []

        # Parse skills field (comma-separated string to list)
        skills_str = frontmatter.get('skills', '')
        if isinstance(skills_str, str):
            # Split by comma and strip whitespace
            skills = [
                skill.strip()
                for skill in skills_str.split(',')
                if skill.strip()
            ]
        elif isinstance(skills_str, list):
            # Already a list
            skills = [str(skill).strip() for skill in skills_str if skill]
        else:
            skills = []

        # Build AgentConfig with frontmatter data and markdown content
        agent_data = {
            'name': frontmatter['name'],
            'description': frontmatter['description'],
            'model': frontmatter.get('model', 'inherit'),
            'tools': tools,
            'skills': skills,
            'color': frontmatter.get('color', 'blue'),
            'prompt': markdown_content,
        }

        # Let Pydantic validate the structure
        return AgentConfig(**agent_data)

    def save_agent(self, agent_config: AgentConfig) -> None:
        """
        Save an agent to file.

        Creates or updates an agent markdown file with YAML frontmatter.
        The agent is saved to agents/<name>.md. Validates the agent
        configuration including tool and skill references.

        Args:
            agent_config: AgentConfig object to save

        Raises:
            AgentValidationError: If agent config is invalid
            AgentError: If file cannot be written
        """
        # Validate the agent config
        try:
            agent_config.model_validate(agent_config.model_dump())
        except ValidationError as e:
            raise AgentValidationError(
                f"Invalid agent configuration: {e}",
            ) from e

        # Validate agent references (tools and skills)
        self.validate_agent(agent_config)

        # Build the file content
        frontmatter = {
            'name': agent_config.name,
            'description': agent_config.description,
            'model': agent_config.model,
            'tools': ', '.join(agent_config.tools),
            'skills': ', '.join(agent_config.skills),
            'color': agent_config.color,
        }

        # Convert to YAML string
        yaml_str = yaml.safe_dump(
            frontmatter,
            default_flow_style=False,
            sort_keys=False,
        ).strip()

        # Combine frontmatter and content
        # Ensure content ends with single newline for clean file formatting
        content = agent_config.prompt.rstrip('\n') + '\n'
        file_content = f"---\n{yaml_str}\n---\n\n{content}"

        # Write to file
        agent_file = self.agents_dir / f"{agent_config.name}{config.AGENT_EXT}"

        try:
            safe_write_file(agent_file, file_content)
        except FileWriteError as e:
            raise AgentError(
                f"Failed to write agent file '{agent_config.name}': {e}",
            ) from e

        # Update cache
        self._agent_cache[agent_config.name] = agent_config

        logger.info(f"Saved agent: {agent_config.name}")

    def delete_agent(self, name: str) -> None:
        """
        Delete an agent file.

        Args:
            name: Agent name (without .md extension)

        Raises:
            AgentNotFoundError: If agent file does not exist
            AgentError: If file cannot be deleted
        """
        agent_file = self.agents_dir / f"{name}{config.AGENT_EXT}"

        if not agent_file.exists():
            raise AgentNotFoundError(
                f"Agent '{name}' not found at {agent_file}",
            )

        try:
            safe_delete_file(agent_file)
        except FileDeleteError as e:
            raise AgentError(
                f"Failed to delete agent file '{name}': {e}",
            ) from e

        # Remove from cache
        if name in self._agent_cache:
            del self._agent_cache[name]

        logger.info(f"Deleted agent: {name}")

    def list_agents(self) -> List[str]:
        """
        List all available agent names.

        Returns list of agent names by scanning the agents/ directory
        for .md files. Does not load or validate the agents.

        Returns:
            List of agent names (without .md extension)
        """
        agent_files = sorted(self.agents_dir.glob(f"*{config.AGENT_EXT}"))
        agent_names = [f.stem for f in agent_files]

        logger.debug(f"Found {len(agent_names)} agents")
        return agent_names

    def get_agent(self, name: str) -> AgentConfig:
        """
        Get an agent by name.

        This is an alias for load_agent() that provides a more intuitive
        method name for retrieving agents.

        Args:
            name: Agent name (without .md extension)

        Returns:
            AgentConfig object

        Raises:
            AgentNotFoundError: If agent does not exist
            AgentLoadError: If agent cannot be loaded
            AgentValidationError: If agent structure is invalid
        """
        return self.load_agent(name)

    def validate_agent(self, agent_config: AgentConfig) -> None:
        """
        Validate an agent configuration.

        Validates that:
        - All referenced tools exist in the project
        - All referenced skills exist in the project
        - Model is valid (either "inherit" or a valid Claude model ID)

        Args:
            agent_config: AgentConfig object to validate

        Raises:
            AgentValidationError: If validation fails
        """
        errors = []

        # Validate model
        if agent_config.model not in VALID_MODELS:
            errors.append(
                f"Invalid model '{agent_config.model}'. Must be one of: "
                f"{', '.join(sorted(VALID_MODELS))}",
            )

        # Validate tools exist
        available_tools = set(self.tool_manager.list_tools())
        for tool_name in agent_config.tools:
            if tool_name not in available_tools:
                errors.append(
                    f"Tool '{tool_name}' referenced by agent but not found in project",
                )

        # Validate skills exist
        available_skills = set(self.skill_manager.list_skills())
        for skill_name in agent_config.skills:
            if skill_name not in available_skills:
                errors.append(
                    f"Skill '{skill_name}' referenced by agent but not found in project",
                )

        # Raise validation error if any issues found
        if errors:
            raise AgentValidationError(
                f"Agent validation failed:\n" + "\n".join(f"  - {err}" for err in errors),
            )

        logger.debug(f"Agent '{agent_config.name}' validation passed")

    def clear_cache(self) -> None:
        """
        Clear the agent cache.

        Forces all agents to be reloaded on next access. Useful when
        agents are modified externally or during testing.
        """
        self._agent_cache.clear()
        logger.debug("Agent cache cleared")
