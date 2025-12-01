"""
Comprehensive unit tests for TestSimulator class.

Tests cover:
- Simulating simple test (no tools)
- Simulating test with tool calls
- Mock tool behavior
- Execute tool behavior
- Skip tool behavior
- Multi-turn simulation
- No matching test (error)
- Partial sequence match
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock

from lib.test_simulator import (
    TestSimulator,
    SimulationError,
    TestNotFoundError,
    NoMatchError,
    ToolExecutionError,
)
from lib.data_models import (
    TestConfig,
    TestCase,
    TestSequenceItem,
    TestMatch,
    TestResponse,
    Session,
    Message,
    ContentBlock,
    SystemBlock,
    ToolSchema,
)


class TestSimulatorInitialization:
    """Tests for TestSimulator initialization."""

    def test_initialize_without_tool_executor(self):
        """Test initializing TestSimulator without tool executor."""
        test_config = TestConfig(tests=[])
        simulator = TestSimulator(test_config=test_config)

        assert simulator.test_config == test_config
        assert simulator.tool_executor is None
        assert simulator.request_matcher is not None

    def test_initialize_with_tool_executor(self):
        """Test initializing TestSimulator with tool executor."""
        test_config = TestConfig(tests=[])
        mock_executor = Mock()
        simulator = TestSimulator(
            test_config=test_config,
            tool_executor=mock_executor,
        )

        assert simulator.test_config == test_config
        assert simulator.tool_executor == mock_executor
        assert simulator.request_matcher is not None


class TestFindTestCase:
    """Tests for _find_test_case method."""

    def test_find_existing_test(self):
        """Test finding an existing test case by name."""
        test_case = TestCase(
            name="test_simple",
            sequence=[],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        result = simulator._find_test_case("test_simple")
        assert result == test_case

    def test_find_nonexistent_test(self):
        """Test finding a non-existent test case returns None."""
        test_config = TestConfig(tests=[])
        simulator = TestSimulator(test_config=test_config)

        result = simulator._find_test_case("nonexistent")
        assert result is None

    def test_find_test_among_multiple(self):
        """Test finding a specific test among multiple test cases."""
        test1 = TestCase(name="test_one", sequence=[])
        test2 = TestCase(name="test_two", sequence=[])
        test3 = TestCase(name="test_three", sequence=[])
        test_config = TestConfig(tests=[test1, test2, test3])
        simulator = TestSimulator(test_config=test_config)

        result = simulator._find_test_case("test_two")
        assert result == test2


class TestSimpleSimulation:
    """Tests for simple simulation without tool calls."""

    def test_simulate_simple_text_response(self):
        """Test simulating a simple text response."""
        # Create test configuration
        test_case = TestCase(
            name="simple_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="hello",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Hello! How can I help you?",
                            ),
                        ],
                    ),
                    tool_behavior="skip",
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        # Create session
        session = Session(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="hello",
                        ),
                    ],
                ),
            ],
        )

        # Simulate
        response = simulator.simulate(session, "simple_test")

        # Verify response structure
        assert response["role"] == "assistant"
        assert response["model"] == "claude-sonnet-4-5-20250929"
        assert response["stop_reason"] == "end_turn"
        assert len(response["content"]) == 1
        assert response["content"][0]["type"] == "text"
        assert response["content"][0]["text"] == "Hello! How can I help you?"

    def test_simulate_test_not_found(self):
        """Test that simulating a non-existent test raises TestNotFoundError."""
        test_config = TestConfig(tests=[])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[],
        )

        with pytest.raises(TestNotFoundError, match="Test case 'nonexistent' not found"):
            simulator.simulate(session, "nonexistent")

    def test_simulate_no_matching_sequence(self):
        """Test that no matching sequence item raises NoMatchError."""
        test_case = TestCase(
            name="test_no_match",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="goodbye",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Goodbye!",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="hello",
                        ),
                    ],
                ),
            ],
        )

        with pytest.raises(NoMatchError, match="No sequence item in test"):
            simulator.simulate(session, "test_no_match")

    def test_simulate_with_regex_match(self):
        """Test simulation with regex pattern matching."""
        test_case = TestCase(
            name="regex_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="regex",
                        path="messages.0.content.0.text",
                        pattern=r"create.*file",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="I'll create a file for you.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="create a new file",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "regex_test")
        assert response["content"][0]["text"] == "I'll create a file for you."


class TestMockToolBehavior:
    """Tests for mock tool behavior."""

    def test_simulate_with_mock_tool_default_result(self):
        """Test mock tool execution with default result."""
        test_case = TestCase(
            name="mock_tool_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="list files",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_123",
                                name="bash",
                                input={"command": "ls"},
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                ),
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.tool_use_id",
                        value="tool_123",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Here are the files.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash commands",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="list files",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "mock_tool_test")

        # Should complete the full multi-turn conversation
        # After tool execution, it continues to next sequence item
        assert response["stop_reason"] == "end_turn"
        assert response["content"][0]["text"] == "Here are the files."

    def test_simulate_with_mock_tool_custom_result(self):
        """Test mock tool execution with custom result from config."""
        test_case = TestCase(
            name="mock_tool_custom_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="list files",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_456",
                                name="bash",
                                input={"command": "ls"},
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                    tool_results={
                        "bash": "file1.txt\nfile2.txt\nfile3.txt",
                    },
                ),
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.content",
                        value="file1.txt",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="I found 3 files.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash commands",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="list files",
                        ),
                    ],
                ),
            ],
        )

        # Should complete the full multi-turn conversation
        response = simulator.simulate(session, "mock_tool_custom_test")
        assert response["stop_reason"] == "end_turn"
        assert response["content"][0]["text"] == "I found 3 files."

    def test_simulate_with_multiple_mock_tools(self):
        """Test mock tool execution with multiple tools in one response."""
        test_case = TestCase(
            name="multi_mock_tool_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="check system",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_1",
                                name="bash",
                                input={"command": "ls"},
                            ),
                            ContentBlock(
                                type="tool_use",
                                id="tool_2",
                                name="read",
                                input={"file_path": "/etc/hosts"},
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                    tool_results={
                        "bash": "file1.txt",
                        "read": "127.0.0.1 localhost",
                    },
                ),
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.tool_use_id",
                        value="tool_1",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="System checked.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash",
                    input_schema={"type": "object"},
                ),
                ToolSchema(
                    name="read",
                    description="Read files",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="check system",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "multi_mock_tool_test")
        # Should complete the full multi-turn conversation
        assert response["stop_reason"] == "end_turn"
        assert response["content"][0]["text"] == "System checked."


class TestExecuteToolBehavior:
    """Tests for execute tool behavior."""

    def test_simulate_with_execute_tool_success(self):
        """Test real tool execution with successful result."""
        # Create mock tool executor
        mock_executor = Mock()
        mock_executor.execute_tool.return_value = "file1.txt\nfile2.txt"

        test_case = TestCase(
            name="execute_tool_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="list files",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_exec_1",
                                name="bash",
                                input={"command": "ls"},
                            ),
                        ],
                    ),
                    tool_behavior="execute",
                ),
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.content",
                        value="file1.txt",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Here are your files.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(
            test_config=test_config,
            tool_executor=mock_executor,
        )

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="list files",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "execute_tool_test")

        # Verify tool was executed
        mock_executor.execute_tool.assert_called_once_with("bash", {"command": "ls"})
        # Should complete the full multi-turn conversation
        assert response["stop_reason"] == "end_turn"
        assert response["content"][0]["text"] == "Here are your files."

    def test_simulate_with_execute_tool_error(self):
        """Test real tool execution with error result."""
        # Create mock tool executor that raises an error
        mock_executor = Mock()
        mock_executor.execute_tool.side_effect = Exception("Command failed")

        test_case = TestCase(
            name="execute_tool_error_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="run command",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_error_1",
                                name="bash",
                                input={"command": "invalid_cmd"},
                            ),
                        ],
                    ),
                    tool_behavior="execute",
                ),
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.content",
                        value="Error executing",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="I encountered an error.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(
            test_config=test_config,
            tool_executor=mock_executor,
        )

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="run command",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "execute_tool_error_test")

        # Verify tool execution was attempted
        mock_executor.execute_tool.assert_called_once()
        # Should complete the full multi-turn conversation
        assert response["stop_reason"] == "end_turn"
        assert response["content"][0]["text"] == "I encountered an error."

    def test_simulate_with_execute_but_no_executor(self):
        """Test that execute behavior without executor raises error."""
        test_case = TestCase(
            name="no_executor_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="test",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_1",
                                name="bash",
                                input={},
                            ),
                        ],
                    ),
                    tool_behavior="execute",
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        # No tool_executor provided
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="test",
                        ),
                    ],
                ),
            ],
        )

        with pytest.raises(ToolExecutionError, match="no tool_executor was provided"):
            simulator.simulate(session, "no_executor_test")


class TestSkipToolBehavior:
    """Tests for skip tool behavior."""

    def test_simulate_with_skip_tool_behavior(self):
        """Test that skip tool behavior returns response without tool results."""
        test_case = TestCase(
            name="skip_tool_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="test",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_skip_1",
                                name="bash",
                                input={"command": "ls"},
                            ),
                        ],
                    ),
                    tool_behavior="skip",
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="test",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "skip_tool_test")

        # Response should have tool_use but no tool execution happens
        assert response["stop_reason"] == "tool_use"
        assert response["content"][0]["type"] == "tool_use"


class TestMultiTurnSimulation:
    """Tests for multi-turn conversation simulation."""

    def test_simulate_multi_turn_conversation(self):
        """Test simulating a multi-turn conversation."""
        test_case = TestCase(
            name="multi_turn_test",
            sequence=[
                # First turn - user asks for files
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="list files",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="tool_use",
                                id="tool_t1",
                                name="bash",
                                input={"command": "ls"},
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                    tool_results={
                        "bash": "file1.txt\nfile2.txt",
                    },
                ),
                # Second turn - assistant responds to tool result
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.content",
                        value="file1.txt",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="I found 2 files.",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="bash",
                    description="Run bash",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="list files",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "multi_turn_test")

        # Should return final text response after tool execution
        assert response["stop_reason"] == "end_turn"
        assert response["content"][0]["text"] == "I found 2 files."

    def test_simulate_sequence_with_partial_match(self):
        """Test that simulation finds the right sequence item among multiple."""
        test_case = TestCase(
            name="partial_match_test",
            sequence=[
                # First sequence item - won't match
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="goodbye",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Goodbye!",
                            ),
                        ],
                    ),
                ),
                # Second sequence item - will match
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="hello",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Hello!",
                            ),
                        ],
                    ),
                ),
                # Third sequence item - won't be reached
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="test",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Test!",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="hello world",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "partial_match_test")

        # Should match second sequence item
        assert response["content"][0]["text"] == "Hello!"


class TestHandleTools:
    """Tests for _handle_tools method."""

    def test_handle_tools_with_empty_tool_uses(self):
        """Test _handle_tools with response containing no tool_use blocks."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        # Response without any tool_use blocks
        response = {
            "content": [
                {"type": "text", "text": "Hello"},
            ],
        }

        results = simulator._handle_tools(
            response,
            tool_behavior="mock",
            tool_results=None,
        )

        # Should return empty list
        assert results == []


class TestHasToolUses:
    """Tests for _has_tool_uses method."""

    def test_has_tool_uses_with_tool_use(self):
        """Test detecting tool_use blocks in response."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "content": [
                {"type": "tool_use", "id": "1", "name": "bash", "input": {}},
            ],
        }

        assert simulator._has_tool_uses(response) is True

    def test_has_tool_uses_without_tool_use(self):
        """Test response without tool_use blocks."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "content": [
                {"type": "text", "text": "Hello"},
            ],
        }

        assert simulator._has_tool_uses(response) is False

    def test_has_tool_uses_empty_content(self):
        """Test response with empty content."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "content": [],
        }

        assert simulator._has_tool_uses(response) is False

    def test_has_tool_uses_mixed_content(self):
        """Test response with mixed content including tool_use."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "tool_use", "id": "1", "name": "bash", "input": {}},
                {"type": "text", "text": "More text"},
            ],
        }

        assert simulator._has_tool_uses(response) is True


class TestFormatApiResponse:
    """Tests for _format_api_response method."""

    def test_format_response_with_text(self):
        """Test formatting a text-only response."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello!"},
            ],
        }

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[],
        )

        result = simulator._format_api_response(response, session)

        assert result["role"] == "assistant"
        assert result["model"] == "claude-sonnet-4-5-20250929"
        assert result["stop_reason"] == "end_turn"
        assert result["type"] == "message"
        assert "usage" in result

    def test_format_response_with_tool_use(self):
        """Test formatting a response with tool_use."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "1", "name": "bash", "input": {}},
            ],
        }

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[],
        )

        result = simulator._format_api_response(response, session)

        assert result["stop_reason"] == "tool_use"


class TestMatchRequest:
    """Tests for _match_request method."""

    def test_match_request_with_exception(self):
        """Test that match_request handles exceptions gracefully."""
        test_config = TestConfig(tests=[])
        simulator = TestSimulator(test_config=test_config)

        # Create a request that will trigger an exception in the matcher
        # by using a malformed match rule
        request = {"messages": [{"text": "hello"}]}

        # Create a sequence item with invalid match rule that will cause exception
        sequence_item = TestSequenceItem(
            match=TestMatch(
                type="regex",
                path="messages.0.text",
                pattern="[invalid",  # Invalid regex pattern
            ),
            response=TestResponse(
                role="assistant",
                content=[
                    ContentBlock(
                        type="text",
                        text="Response",
                    ),
                ],
            ),
        )

        # Should return False instead of raising exception
        result = simulator._match_request(request, sequence_item)
        assert result is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_simulate_with_empty_messages(self):
        """Test simulation with empty message list."""
        test_case = TestCase(
            name="empty_msg_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="model",
                        value="claude",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Hello!",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[],
        )

        response = simulator.simulate(session, "empty_msg_test")
        assert response["content"][0]["text"] == "Hello!"

    def test_simulate_with_system_prompt(self):
        """Test simulation with system prompt matching."""
        test_case = TestCase(
            name="system_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="system.0.text",
                        value="helpful",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="I'm here to help!",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            system=[
                SystemBlock(
                    type="text",
                    text="You are a helpful assistant.",
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="Hello",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "system_test")
        assert response["content"][0]["text"] == "I'm here to help!"

    def test_simulate_preserves_session_state(self):
        """Test that simulation doesn't modify the original session."""
        test_case = TestCase(
            name="state_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="test",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Response",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        original_message = Message(
            role="user",
            content=[
                ContentBlock(
                    type="text",
                    text="test",
                ),
            ],
        )

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[original_message],
        )

        # Store original message count
        original_count = len(session.messages)

        # Simulate
        simulator.simulate(session, "state_test")

        # Original session should be unchanged
        assert len(session.messages) == original_count

    def test_handle_tools_with_unknown_behavior(self):
        """Test handling tools with unknown behavior defaults to skip."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        response = {
            "content": [
                {"type": "tool_use", "id": "1", "name": "bash", "input": {}},
            ],
        }

        # Use an unknown behavior
        results = simulator._handle_tools(
            response,
            tool_behavior="unknown",
            tool_results=None,
        )

        # Should return empty list (like skip)
        assert results == []

    def test_mock_tool_with_no_configured_results(self):
        """Test mock tool uses default result when not configured."""
        simulator = TestSimulator(test_config=TestConfig(tests=[]))

        tool_uses = [
            {"id": "tool_1", "name": "bash", "input": {}},
        ]

        results = simulator._handle_mock_tools(tool_uses, tool_results=None)

        assert len(results) == 1
        assert results[0]["tool_use_id"] == "tool_1"
        assert "Mock result for bash" in results[0]["content"]
        assert results[0]["is_error"] is False


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_simulate_complete_workflow(self):
        """Test a complete workflow with multiple turns and tool executions."""
        test_case = TestCase(
            name="workflow_test",
            sequence=[
                # Turn 1: User asks for file content
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.0.content.0.text",
                        value="read file",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="I'll read the file.",
                            ),
                            ContentBlock(
                                type="tool_use",
                                id="read_1",
                                name="read",
                                input={"file_path": "/test.txt"},
                            ),
                        ],
                    ),
                    tool_behavior="mock",
                    tool_results={
                        "read": "Hello World",
                    },
                ),
                # Turn 2: Assistant processes tool result
                TestSequenceItem(
                    match=TestMatch(
                        type="contains",
                        path="messages.-1.content.0.content",
                        value="Hello World",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="The file contains: Hello World",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            tools=[
                ToolSchema(
                    name="read",
                    description="Read files",
                    input_schema={"type": "object"},
                ),
            ],
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="read file",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "workflow_test")

        assert response["stop_reason"] == "end_turn"
        assert "Hello World" in response["content"][0]["text"]

    def test_simulate_with_complex_matching(self):
        """Test simulation with complex path matching including negative indices."""
        test_case = TestCase(
            name="complex_match_test",
            sequence=[
                TestSequenceItem(
                    match=TestMatch(
                        type="regex",
                        path="messages.-1.content.0.text",
                        pattern=r"test.*123",
                    ),
                    response=TestResponse(
                        role="assistant",
                        content=[
                            ContentBlock(
                                type="text",
                                text="Matched!",
                            ),
                        ],
                    ),
                ),
            ],
        )
        test_config = TestConfig(tests=[test_case])
        simulator = TestSimulator(test_config=test_config)

        session = Session(
            model="claude-sonnet-4-5-20250929",
            messages=[
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="text",
                            text="test case 123",
                        ),
                    ],
                ),
            ],
        )

        response = simulator.simulate(session, "complex_match_test")
        assert response["content"][0]["text"] == "Matched!"
