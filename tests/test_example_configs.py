"""
Validation tests for example project test configurations (Plan 06, Task 6.7.2).

These tests validate that the example test configurations in
projects/example_project/tests/config.json are correct and functional.
Each test case is loaded and executed through the TestSimulator to ensure:

- All test cases can be loaded successfully
- Test sequences match correctly
- Tool behaviors (skip, mock, execute) work as expected
- Multi-turn conversations flow properly
- Error handling works correctly
- All scenarios are reproducible

This is validation testing to verify the example configurations themselves,
not the simulator (which has its own unit tests in test_test_simulator.py).
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from lib.test_simulator import TestSimulator, NoMatchError, TestNotFoundError
from lib.data_models import (
    TestConfig,
    Session,
    Message,
    ContentBlock,
    SystemBlock,
)
from lib.file_operations import safe_read_json


@pytest.fixture
def example_test_config():
    """
    Load the example project test configuration.

    Returns:
        TestConfig object loaded from example project
    """
    config_path = Path("/home/vagrant/anthropide/projects/example_project/tests/config.json")

    # Verify the config file exists
    assert config_path.exists(), f"Example config not found at {config_path}"

    # Load and parse the config
    config_data = safe_read_json(config_path)
    test_config = TestConfig(**config_data)

    return test_config


@pytest.fixture
def tool_executor_mock():
    """
    Create a mock tool executor for tests that need tool execution.

    Returns:
        Mock object with execute_tool method
    """
    mock = Mock()

    # Configure default behavior for Read tool
    def read_tool_side_effect(tool_name, tool_input):
        if tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            if "config.json" in file_path:
                return '{"setting": "value"}'
            elif "README.md" in file_path:
                return "# Example Project\n\nThis is a sample README."
            elif "utils.py" in file_path:
                return "def process_data(data):\n    result = []\n    for item in data:\n        if item > 10:\n            result.append(item * 2)\n    return result"
            elif "this_file_does_not_exist.txt" in file_path:
                raise FileNotFoundError(f"File not found: {file_path}")
            else:
                return f"Content of {file_path}"
        return f"Result of {tool_name}"

    mock.execute_tool.side_effect = read_tool_side_effect

    return mock


def create_session_with_message(text: str, model: str = "claude-sonnet-4") -> Session:
    """
    Helper to create a Session with a single user message.

    Args:
        text: Text content of the user message
        model: Model name to use

    Returns:
        Session object with the message
    """
    return Session(
        model=model,
        max_tokens=4096,
        system=[SystemBlock(type="text", text="You are a helpful assistant.")],
        messages=[
            Message(
                role="user",
                content=[ContentBlock(type="text", text=text)],
            ),
        ],
    )


class TestExampleConfigLoading:
    """Test that the example config file can be loaded successfully."""

    def test_config_file_exists(self):
        """Verify the example config file exists."""
        config_path = Path("/home/vagrant/anthropide/projects/example_project/tests/config.json")
        assert config_path.exists(), "Example config file does not exist"
        assert config_path.is_file(), "Example config path is not a file"

    def test_config_is_valid_json(self):
        """Verify the config file is valid JSON."""
        config_path = Path("/home/vagrant/anthropide/projects/example_project/tests/config.json")

        with open(config_path, 'r') as f:
            config_data = json.load(f)

        assert isinstance(config_data, dict), "Config should be a JSON object"
        assert "tests" in config_data, "Config should have 'tests' key"
        assert isinstance(config_data["tests"], list), "tests should be a list"

    def test_config_loads_as_testconfig(self, example_test_config):
        """Verify the config can be parsed as TestConfig data model."""
        assert isinstance(example_test_config, TestConfig)
        assert len(example_test_config.tests) > 0, "Should have at least one test case"

    def test_all_test_cases_have_names(self, example_test_config):
        """Verify all test cases have unique names."""
        names = [test.name for test in example_test_config.tests]

        assert len(names) == len(set(names)), "Test case names should be unique"
        assert all(name for name in names), "All test cases should have non-empty names"

    def test_all_test_cases_have_sequences(self, example_test_config):
        """Verify all test cases have non-empty sequences."""
        for test_case in example_test_config.tests:
            assert len(test_case.sequence) > 0, \
                f"Test case '{test_case.name}' should have at least one sequence item"


class TestSimpleTextResponse:
    """Test the simple_text_response test case."""

    def test_simple_text_response_exists(self, example_test_config):
        """Verify the simple_text_response test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "simple_text_response" in test_names

    def test_simple_text_response_simulation(self, example_test_config):
        """Simulate the simple_text_response test case."""
        simulator = TestSimulator(test_config=example_test_config)

        # Create session with matching message
        session = create_session_with_message("What is the capital of France?")

        # Run simulation
        response = simulator.simulate(session, "simple_text_response")

        # Verify response structure
        assert response["role"] == "assistant"
        assert "content" in response
        assert len(response["content"]) > 0

        # Verify response contains expected text
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Response should have text content"
        assert "Paris" in text_blocks[0]["text"]
        assert response["stop_reason"] == "end_turn"


class TestSingleToolCallRead:
    """Test the single_tool_call_read test case."""

    def test_single_tool_call_exists(self, example_test_config):
        """Verify the single_tool_call_read test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "single_tool_call_read" in test_names

    def test_single_tool_call_first_turn(self, example_test_config, tool_executor_mock):
        """Simulate first turn of single_tool_call_read (tool execution).

        Note: With tool_behavior="execute", the simulator automatically executes
        the tool and continues to the next sequence item, so we get the final
        response after tool execution, not the tool_use itself.
        """
        simulator = TestSimulator(
            test_config=example_test_config,
            tool_executor=tool_executor_mock,
        )

        # Create session with matching message
        session = create_session_with_message("Please read the config file")

        # Run simulation - should complete the full sequence including tool execution
        response = simulator.simulate(session, "single_tool_call_read")

        # With tool_behavior="execute", the simulator executes tools and continues,
        # so we should get the final text response after tool execution
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Response should have final text"
        assert "config" in text_blocks[0]["text"].lower()
        assert response["stop_reason"] == "end_turn"

        # Verify tool was executed
        tool_executor_mock.execute_tool.assert_called_once()

    def test_single_tool_call_second_turn(self, example_test_config, tool_executor_mock):
        """Simulate second turn of single_tool_call_read (after tool result)."""
        simulator = TestSimulator(
            test_config=example_test_config,
            tool_executor=tool_executor_mock,
        )

        # Create session with tool result message
        session = Session(
            model="claude-sonnet-4",
            max_tokens=4096,
            system=[SystemBlock(type="text", text="You are a helpful assistant.")],
            messages=[
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="Please read the config file")],
                ),
                Message(
                    role="assistant",
                    content=[
                        ContentBlock(type="text", text="I'll read the configuration file for you."),
                        ContentBlock(
                            type="tool_use",
                            id="toolu_01A1B2C3D4E5F6",
                            name="Read",
                            input={"file_path": "/home/vagrant/anthropide/projects/example_project/config.json"},
                        ),
                    ],
                ),
                Message(
                    role="user",
                    content=[
                        ContentBlock(
                            type="tool_result",
                            tool_use_id="toolu_01A1B2C3D4E5F6",
                            content='{"setting": "value"}',
                        ),
                    ],
                ),
            ],
        )

        # Run simulation - second turn should return text response
        response = simulator.simulate(session, "single_tool_call_read")

        # Verify response is text
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Response should have text content"
        assert "config.json" in text_blocks[0]["text"]
        assert response["stop_reason"] == "end_turn"


class TestMultipleToolCalls:
    """Test the multiple_tool_calls_read_edit test case."""

    def test_multiple_tool_calls_exists(self, example_test_config):
        """Verify the multiple_tool_calls_read_edit test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "multiple_tool_calls_read_edit" in test_names

    def test_multiple_tool_calls_full_sequence(self, example_test_config, tool_executor_mock):
        """Simulate complete multiple_tool_calls_read_edit sequence.

        This test uses a 3-step sequence with mixed tool behaviors.
        The simulator will execute through all steps automatically.
        """
        simulator = TestSimulator(
            test_config=example_test_config,
            tool_executor=tool_executor_mock,
        )

        # Run simulation with initial request
        session = create_session_with_message("update the README and add a description")
        response = simulator.simulate(session, "multiple_tool_calls_read_edit")

        # The simulator will execute through the full sequence, so we should
        # get the final response after all tool executions
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Should have final text response"
        # Verify it's the final step by checking for confirmation message
        assert "updated" in text_blocks[0]["text"].lower() or \
               "successfully" in text_blocks[0]["text"].lower()


class TestAgentSpawning:
    """Test the agent_spawning_task_tool test case."""

    def test_agent_spawning_exists(self, example_test_config):
        """Verify the agent_spawning_task_tool test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "agent_spawning_task_tool" in test_names

    def test_agent_spawning_first_turn(self, example_test_config):
        """Simulate agent spawning with Task tool (mock behavior).

        With tool_behavior="mock", the simulator executes the mock and continues
        through the sequence, returning the final response.
        """
        simulator = TestSimulator(test_config=example_test_config)

        # Create session with matching message
        session = create_session_with_message("Please analyze the codebase for security issues")

        # Run simulation - with mock behavior, completes full sequence
        response = simulator.simulate(session, "agent_spawning_task_tool")

        # Should get final text response with security analysis results
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Should have final text response"
        assert "security" in text_blocks[0]["text"].lower()
        assert response["stop_reason"] == "end_turn"


class TestMultiTurnConversation:
    """Test the multi_turn_conversation test case."""

    def test_multi_turn_exists(self, example_test_config):
        """Verify the multi_turn_conversation test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "multi_turn_conversation" in test_names

    def test_multi_turn_first_message(self, example_test_config):
        """Test first turn of multi-turn conversation."""
        simulator = TestSimulator(test_config=example_test_config)

        # First turn: Ask for fibonacci function
        session = create_session_with_message("create a Python function to calculate fibonacci")
        response = simulator.simulate(session, "multi_turn_conversation")

        # Verify response contains code
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0
        assert "fibonacci" in text_blocks[0]["text"].lower()
        assert "def " in text_blocks[0]["text"]

    def test_multi_turn_second_message(self, example_test_config):
        """Test second turn of multi-turn conversation."""
        simulator = TestSimulator(test_config=example_test_config)

        # Create session with conversation history
        session = Session(
            model="claude-sonnet-4",
            max_tokens=4096,
            system=[SystemBlock(type="text", text="You are a helpful assistant.")],
            messages=[
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="create a Python function to calculate fibonacci")],
                ),
                Message(
                    role="assistant",
                    content=[ContentBlock(type="text", text="I'll create a Python function... def fibonacci(n)...")],
                ),
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="what's the time complexity")],
                ),
            ],
        )

        # Second turn: Ask about complexity
        response = simulator.simulate(session, "multi_turn_conversation")

        # Verify response discusses complexity
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0
        assert "O(n)" in text_blocks[0]["text"]

    def test_multi_turn_third_message(self, example_test_config):
        """Test third turn of multi-turn conversation."""
        simulator = TestSimulator(test_config=example_test_config)

        # Create session with full conversation history
        session = Session(
            model="claude-sonnet-4",
            max_tokens=4096,
            system=[SystemBlock(type="text", text="You are a helpful assistant.")],
            messages=[
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="create a Python function to calculate fibonacci")],
                ),
                Message(
                    role="assistant",
                    content=[ContentBlock(type="text", text="def fibonacci(n)...")],
                ),
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="what's the time complexity")],
                ),
                Message(
                    role="assistant",
                    content=[ContentBlock(type="text", text="Time Complexity: O(n)...")],
                ),
                Message(
                    role="user",
                    content=[ContentBlock(type="text", text="show me the iterative version")],
                ),
            ],
        )

        # Third turn: Ask for iterative version
        response = simulator.simulate(session, "multi_turn_conversation")

        # Verify response contains iterative implementation
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0
        assert "iterative" in text_blocks[0]["text"].lower()


class TestParallelToolCalls:
    """Test the parallel_tool_calls test case."""

    def test_parallel_tool_calls_exists(self, example_test_config):
        """Verify the parallel_tool_calls test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "parallel_tool_calls" in test_names

    def test_parallel_tool_calls_simulation(self, example_test_config, tool_executor_mock):
        """Test parallel tool calls execution.

        With tool_behavior="execute", the simulator executes all parallel tools
        and continues to the next sequence item with the results.
        """
        simulator = TestSimulator(
            test_config=example_test_config,
            tool_executor=tool_executor_mock,
        )

        # Create session requesting parallel reads
        session = create_session_with_message("check both config files")
        response = simulator.simulate(session, "parallel_tool_calls")

        # Should complete sequence and return final text response
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Should have final text response"
        assert "config" in text_blocks[0]["text"].lower()
        assert response["stop_reason"] == "end_turn"


class TestErrorHandling:
    """Test the error_handling_tool_failure test case."""

    def test_error_handling_exists(self, example_test_config):
        """Verify the error_handling_tool_failure test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "error_handling_tool_failure" in test_names

    def test_error_handling_simulation(self, example_test_config):
        """Test error handling for tool failures.

        With tool_behavior="mock", the simulator provides a mock error result
        and continues to the next sequence item.
        """
        simulator = TestSimulator(test_config=example_test_config)

        # Request to read nonexistent file
        session = create_session_with_message("read the nonexistent file")
        response = simulator.simulate(session, "error_handling_tool_failure")

        # Should complete sequence and return final text response with error handling
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Should have final text response"
        assert "error" in text_blocks[0]["text"].lower() or \
               "not exist" in text_blocks[0]["text"].lower()
        assert response["stop_reason"] == "end_turn"


class TestComplexWorkflow:
    """Test the complex_workflow_with_validation test case."""

    def test_complex_workflow_exists(self, example_test_config):
        """Verify the complex_workflow_with_validation test case exists."""
        test_names = [test.name for test in example_test_config.tests]
        assert "complex_workflow_with_validation" in test_names

    def test_complex_workflow_simulation(self, example_test_config, tool_executor_mock):
        """Test complex workflow with multiple steps.

        This is a 3-step sequence that reads, edits, and provides final feedback.
        The simulator executes the full workflow automatically.
        """
        simulator = TestSimulator(
            test_config=example_test_config,
            tool_executor=tool_executor_mock,
        )

        # Create session with refactoring request
        session = create_session_with_message("refactor the function to improve code quality")
        response = simulator.simulate(session, "complex_workflow_with_validation")

        # Should complete the full workflow and return final confirmation
        text_blocks = [
            block for block in response["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        assert len(text_blocks) > 0, "Should have final text response"
        assert "refactor" in text_blocks[0]["text"].lower() or \
               "improve" in text_blocks[0]["text"].lower()
        assert response["stop_reason"] == "end_turn"


class TestAllTestCasesAreReachable:
    """Verify all test cases in the config can be simulated successfully."""

    def test_all_test_cases_can_be_found(self, example_test_config):
        """Verify simulator can find all test cases by name."""
        simulator = TestSimulator(test_config=example_test_config)

        for test_case in example_test_config.tests:
            found_test = simulator._find_test_case(test_case.name)
            assert found_test is not None, f"Could not find test case '{test_case.name}'"
            assert found_test.name == test_case.name

    def test_nonexistent_test_raises_error(self, example_test_config):
        """Verify requesting nonexistent test raises appropriate error."""
        simulator = TestSimulator(test_config=example_test_config)
        session = create_session_with_message("test message")

        with pytest.raises(TestNotFoundError):
            simulator.simulate(session, "nonexistent_test_name")


class TestTestCaseNamesDocumentation:
    """Document all test cases available in the example config."""

    def test_list_all_test_cases(self, example_test_config):
        """List all test cases with their descriptions for documentation."""
        expected_tests = [
            "simple_text_response",
            "single_tool_call_read",
            "multiple_tool_calls_read_edit",
            "agent_spawning_task_tool",
            "multi_turn_conversation",
            "parallel_tool_calls",
            "error_handling_tool_failure",
            "complex_workflow_with_validation",
        ]

        actual_test_names = [test.name for test in example_test_config.tests]

        # Verify all expected tests exist
        for expected_test in expected_tests:
            assert expected_test in actual_test_names, \
                f"Expected test '{expected_test}' not found in config"

        # Log test case information for documentation
        print("\nExample Test Cases:")
        for test_case in example_test_config.tests:
            sequence_count = len(test_case.sequence)
            print(f"  - {test_case.name} ({sequence_count} sequence items)")


class TestReproducibility:
    """Verify tests are reproducible and deterministic."""

    def test_simple_response_is_reproducible(self, example_test_config):
        """Verify running the same test twice produces identical results."""
        simulator = TestSimulator(test_config=example_test_config)

        # Run simulation twice with same input
        session1 = create_session_with_message("What is the capital of France?")
        response1 = simulator.simulate(session1, "simple_text_response")

        session2 = create_session_with_message("What is the capital of France?")
        response2 = simulator.simulate(session2, "simple_text_response")

        # Verify responses are identical
        assert response1["role"] == response2["role"]
        assert response1["content"] == response2["content"]
        assert response1["stop_reason"] == response2["stop_reason"]

    def test_tool_execution_is_reproducible(self, example_test_config):
        """Verify tool execution produces consistent results."""
        # Create consistent mock
        mock1 = Mock()
        mock1.execute_tool.return_value = "consistent result"

        mock2 = Mock()
        mock2.execute_tool.return_value = "consistent result"

        simulator1 = TestSimulator(
            test_config=example_test_config,
            tool_executor=mock1,
        )
        simulator2 = TestSimulator(
            test_config=example_test_config,
            tool_executor=mock2,
        )

        # Run same test twice
        session1 = create_session_with_message("Please read the config file")
        response1 = simulator1.simulate(session1, "single_tool_call_read")

        session2 = create_session_with_message("Please read the config file")
        response2 = simulator2.simulate(session2, "single_tool_call_read")

        # Verify responses are consistent
        assert response1["stop_reason"] == response2["stop_reason"]


class TestCoverageOfScenarios:
    """Verify example tests cover main scenarios."""

    def test_covers_simple_text_response(self, example_test_config):
        """Verify config includes simple text response scenario."""
        test_names = [test.name for test in example_test_config.tests]
        assert "simple_text_response" in test_names

    def test_covers_tool_execution(self, example_test_config):
        """Verify config includes tool execution scenarios."""
        # Check for tests with tool_use in their sequences
        has_tool_test = False
        for test_case in example_test_config.tests:
            for sequence_item in test_case.sequence:
                response_content = sequence_item.response.content
                for block in response_content:
                    if block.type == "tool_use":
                        has_tool_test = True
                        break

        assert has_tool_test, "Config should include at least one test with tool execution"

    def test_covers_multi_turn_conversations(self, example_test_config):
        """Verify config includes multi-turn conversation scenarios."""
        # Check for tests with multiple sequence items
        multi_turn_tests = [
            test for test in example_test_config.tests
            if len(test.sequence) > 2
        ]

        assert len(multi_turn_tests) > 0, \
            "Config should include at least one multi-turn conversation test"

    def test_covers_error_handling(self, example_test_config):
        """Verify config includes error handling scenarios."""
        test_names = [test.name for test in example_test_config.tests]
        error_test_exists = any("error" in name.lower() for name in test_names)

        assert error_test_exists, "Config should include error handling test"

    def test_covers_parallel_operations(self, example_test_config):
        """Verify config includes parallel operations scenarios."""
        test_names = [test.name for test in example_test_config.tests]
        parallel_test_exists = any("parallel" in name.lower() for name in test_names)

        assert parallel_test_exists, "Config should include parallel operations test"
