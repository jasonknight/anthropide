"""
Pydantic data models for AnthropIDE.

This module defines all data structures used throughout the application,
including project settings, sessions, messages, agents, skills, and testing.
All models use Pydantic v2 for validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime


class ProjectSettings(BaseModel):
    """
    Settings for a project.

    Attributes:
        max_session_backups: Maximum number of session backups to keep
        auto_save: Whether to automatically save sessions on changes
        default_model: Default Claude model to use for new sessions
    """
    max_session_backups: int = 20
    auto_save: bool = True
    default_model: str = "claude-sonnet-4-5-20250929"


class Project(BaseModel):
    """
    Project metadata.

    Attributes:
        name: Unique project identifier
        description: Optional project description
        created: Timestamp when project was created
        modified: Timestamp when project was last modified
        settings: Project-specific settings
    """
    name: str
    description: Optional[str] = None
    created: datetime
    modified: datetime
    settings: ProjectSettings = Field(default_factory=ProjectSettings)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate project name.

        Args:
            v: Project name to validate

        Returns:
            Validated project name

        Raises:
            ValueError: If name is invalid
        """
        if not v:
            raise ValueError("Project name cannot be empty")
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(
                "Project name must contain only alphanumeric characters, hyphens, and underscores"
            )
        if len(v) > 100:
            raise ValueError("Project name must be 100 characters or less")
        return v


class SystemBlock(BaseModel):
    """
    System prompt block for Anthropic API.

    Attributes:
        type: Block type (text or image)
        text: Text content (required for type="text")
        source: Image source data (required for type="image")
        cache_control: Optional cache control settings
    """
    type: Literal["text", "image"]
    text: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    cache_control: Optional[Dict[str, str]] = None

    @model_validator(mode='after')
    def validate_required_fields(self):
        """Validate that required fields are provided based on type."""
        if self.type == 'text' and not self.text:
            raise ValueError("text field is required when type is 'text'")
        if self.type == 'image' and not self.source:
            raise ValueError("source field is required when type is 'image'")
        return self


class ToolSchema(BaseModel):
    """
    Tool schema definition for Anthropic API.

    Attributes:
        name: Unique tool identifier
        description: Human-readable description of what the tool does
        input_schema: JSON schema defining the tool's input parameters
    """
    name: str
    description: str
    input_schema: Dict[str, Any]


class ContentBlock(BaseModel):
    """
    Content block in a message.

    Can be one of:
    - text: Plain text content
    - image: Image content with source
    - tool_use: Tool invocation by assistant
    - tool_result: Tool execution result from user

    Attributes:
        type: Block type
        text: Text content (for type="text")
        source: Image source (for type="image")
        id: Unique ID (for type="tool_use")
        name: Tool name (for type="tool_use")
        input: Tool parameters (for type="tool_use")
        tool_use_id: ID of tool_use block (for type="tool_result")
        content: Result content (for type="tool_result")
        is_error: Whether result is an error (for type="tool_result")
    """
    type: Literal["text", "image", "tool_use", "tool_result"]

    # Fields for type="text"
    text: Optional[str] = None

    # Fields for type="image"
    source: Optional[Dict[str, Any]] = None

    # Fields for type="tool_use"
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None

    # Fields for type="tool_result"
    tool_use_id: Optional[str] = None
    content: Optional[Union[str, List[Dict[str, Any]]]] = None
    is_error: Optional[bool] = None

    @model_validator(mode='after')
    def validate_required_fields(self):
        """Validate that required fields are provided based on type."""
        if self.type == 'text' and self.text is None:
            raise ValueError("text field is required when type is 'text'")

        if self.type == 'image' and not self.source:
            raise ValueError("source field is required when type is 'image'")

        if self.type == 'tool_use':
            if not self.id:
                raise ValueError("id field is required when type is 'tool_use'")
            if not self.name:
                raise ValueError("name field is required when type is 'tool_use'")
            if self.input is None:
                raise ValueError("input field is required when type is 'tool_use'")

        if self.type == 'tool_result':
            if not self.tool_use_id:
                raise ValueError("tool_use_id field is required when type is 'tool_result'")
            if self.content is None:
                raise ValueError("content field is required when type is 'tool_result'")

        return self


class Message(BaseModel):
    """
    Message in a conversation.

    Attributes:
        role: Message role (user or assistant)
        content: List of content blocks in the message
    """
    role: Literal["user", "assistant"]
    content: List[ContentBlock]


class Session(BaseModel):
    """
    Complete session state representing an Anthropic API request.

    Attributes:
        model: Claude model identifier
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0-1)
        system: System prompt blocks
        tools: Available tool schemas
        messages: Conversation messages
    """
    model: str
    max_tokens: int = 8192
    temperature: Optional[float] = 1.0
    system: List[SystemBlock] = Field(default_factory=list)
    tools: List[ToolSchema] = Field(default_factory=list)
    messages: List[Message] = Field(default_factory=list)

    def validate(self) -> None:
        """
        Validate session can be sent to Anthropic API.

        Raises:
            ValueError: If session has validation errors

        Validates:
        - Model name is valid
        - max_tokens is positive and within limits (0 < max_tokens <= 200000)
        - temperature is within range (0 <= temp <= 1)
        - Messages alternate between user/assistant roles
        - tool_use_id references in tool_result blocks match existing tool_use blocks
        - Tool names in messages exist in the tools list
        - System blocks have required fields
        """
        # Validate max_tokens
        if self.max_tokens <= 0 or self.max_tokens > 200000:
            raise ValueError(
                f"max_tokens must be between 1 and 200000, got {self.max_tokens}"
            )

        # Validate temperature
        if self.temperature is not None and (self.temperature < 0 or self.temperature > 1):
            raise ValueError(
                f"temperature must be between 0 and 1, got {self.temperature}"
            )

        # Validate message role alternation
        prev_role = None
        for i, msg in enumerate(self.messages):
            if prev_role == msg.role and prev_role is not None:
                # Allow consecutive user messages (for tool results)
                # but disallow consecutive assistant messages
                if msg.role == 'assistant':
                    raise ValueError(
                        f"Message {i}: consecutive assistant messages not allowed"
                    )
            prev_role = msg.role

        # Collect tool_use IDs and validate tool_result references
        tool_use_ids = set()
        tool_names_in_session = {tool.name for tool in self.tools}

        for i, msg in enumerate(self.messages):
            for j, block in enumerate(msg.content):
                if block.type == 'tool_use':
                    # Add tool_use ID to set
                    tool_use_ids.add(block.id)

                    # Validate tool name exists in session
                    if block.name not in tool_names_in_session:
                        raise ValueError(
                            f"Message {i}, block {j}: tool_use references "
                            f"unknown tool '{block.name}'"
                        )

                elif block.type == 'tool_result':
                    # Validate tool_use_id references an existing tool_use
                    if block.tool_use_id not in tool_use_ids:
                        raise ValueError(
                            f"Message {i}, block {j}: tool_result references "
                            f"unknown tool_use_id '{block.tool_use_id}'"
                        )


class AgentConfig(BaseModel):
    """
    Agent definition configuration.

    Agents are spawned dynamically during execution using a Task tool.
    They have their own system prompt, tools, and skills.

    Attributes:
        name: Unique agent identifier
        description: When and why to use this agent
        model: Model to use ("inherit" or specific model ID)
        tools: List of tool names available to this agent
        skills: List of skill names available to this agent
        color: UI color for visual identification
        prompt: The markdown content after YAML frontmatter
    """
    name: str
    description: str
    model: str = "inherit"
    tools: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    color: str = "blue"
    prompt: str


class SkillConfig(BaseModel):
    """
    Skill definition configuration.

    Skills are instructional markdown files that get added to the system
    prompt (with caching) when an agent uses them. They teach the model
    how to use tools to accomplish complex workflows.

    Attributes:
        name: Unique skill identifier
        description: What this skill teaches
        version: Skill version
        author: Optional author name
        content: The markdown content after YAML frontmatter
    """
    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    content: str


class TestMatch(BaseModel):
    """
    Pattern matching configuration for test assertions.

    Attributes:
        type: Match type (regex or contains)
        path: Dot notation JSON path to field to match
        pattern: Regex pattern (for type="regex")
        value: Value to match (for type="contains")
    """
    type: Literal["regex", "contains"]
    path: str
    pattern: Optional[str] = None
    value: Optional[Any] = None

    @model_validator(mode='after')
    def validate_required_fields(self):
        """Validate that required fields are provided based on type."""
        if self.type == 'regex' and not self.pattern:
            raise ValueError("pattern field is required when type is 'regex'")
        if self.type == 'contains' and self.value is None:
            raise ValueError("value field is required when type is 'contains'")
        return self


class TestResponse(BaseModel):
    """
    Simulated response in a test sequence.

    Attributes:
        role: Response role (user or assistant)
        content: List of content blocks in the response
    """
    role: Literal["user", "assistant"]
    content: List[ContentBlock]


class TestSequenceItem(BaseModel):
    """
    Single item in a test sequence.

    Attributes:
        match: Pattern to match in the request
        response: Response to return when pattern matches
        tool_behavior: How to handle tool calls (mock, execute, or skip)
        tool_results: Mock tool results if tool_behavior="mock"
    """
    match: TestMatch
    response: TestResponse
    tool_behavior: Literal["mock", "execute", "skip"] = "mock"
    tool_results: Optional[Dict[str, Any]] = None


class TestCase(BaseModel):
    """
    Test case definition.

    Attributes:
        name: Test case name
        sequence: List of match/response pairs in order
    """
    name: str
    sequence: List[TestSequenceItem]


class TestConfig(BaseModel):
    """
    Test configuration for simulation mode.

    Attributes:
        tests: List of test cases
    """
    tests: List[TestCase]


class UIState(BaseModel):
    """
    UI state persistence.

    Attributes:
        version: State format version
        selected_project: Currently selected project name
        ui: Arbitrary UI state data
        last_modified: Timestamp of last modification
    """
    version: str = "1.0"
    selected_project: Optional[str] = None
    ui: Dict[str, Any] = Field(default_factory=dict)
    last_modified: datetime
