"""
Test simulation engine for AnthropIDE.

This module provides the TestSimulator class which simulates session execution
without making real API calls. It uses test configuration to match requests
against patterns and return canned responses, enabling deterministic testing
of prompt workflows.
"""

import logging
from typing import Dict, Any, Optional, List
from copy import deepcopy

from lib.data_models import (
    TestConfig,
    TestCase,
    TestSequenceItem,
    Session,
    Message,
    ContentBlock,
)
from lib.request_matcher import RequestMatcher

logger = logging.getLogger(__name__)


class SimulationError(Exception):
    """Base exception for simulation errors."""
    pass


class TestNotFoundError(SimulationError):
    """Exception raised when test case is not found."""
    pass


class NoMatchError(SimulationError):
    """Exception raised when no sequence item matches the request."""
    pass


class ToolExecutionError(SimulationError):
    """Exception raised when tool execution fails during simulation."""
    pass


class TestSimulator:
    """
    Simulates session execution using test configurations.

    This class processes API requests through a test sequence, matching
    requests against configured patterns and returning canned responses.
    Supports multi-turn conversations, tool execution (mock, execute, skip),
    and maintains conversation state.

    Attributes:
        test_config: TestConfig object containing test cases
        tool_executor: Tool executor instance for executing real tools
        request_matcher: RequestMatcher instance for matching logic
    """

    def __init__(
        self,
        test_config: TestConfig,
        tool_executor: Optional[Any] = None,
    ):
        """
        Initialize TestSimulator with test configuration and tool executor.

        Args:
            test_config: TestConfig object containing test cases
            tool_executor: Optional tool executor instance with execute_tool method.
                          Required if any test uses tool_behavior="execute".

        Note:
            The tool_executor should have an execute_tool(tool_name, parameters)
            method that returns the tool execution result as a string.
        """
        self.test_config = test_config
        self.tool_executor = tool_executor
        self.request_matcher = RequestMatcher()

        logger.info(
            f"TestSimulator initialized with {len(test_config.tests)} test cases",
        )

    def simulate(
        self,
        session: Session,
        test_name: str,
    ) -> Dict[str, Any]:
        """
        Simulate session execution using a named test case.

        Finds the matching test case by name, then iterates through the test
        sequence. For each sequence item, checks if the current session state
        matches the match rule. If it matches, applies the canned response
        and handles any tool execution according to the tool_behavior setting.

        Args:
            session: Session object representing the current API request state
            test_name: Name of the test case to use for simulation

        Returns:
            Dictionary containing the simulated API response with structure:
            {
                "role": "assistant",
                "content": [...],  # List of ContentBlock objects
                "model": "...",
                "stop_reason": "end_turn" | "tool_use",
                "usage": {...}
            }

        Raises:
            TestNotFoundError: If test_name is not found in test_config
            NoMatchError: If no sequence item matches the current request
            ToolExecutionError: If tool execution fails
            SimulationError: For other simulation errors
        """
        logger.info(f"Starting simulation for test: {test_name}")

        # Find the test case
        test_case = self._find_test_case(test_name)
        if not test_case:
            raise TestNotFoundError(
                f"Test case '{test_name}' not found in configuration",
            )

        logger.debug(
            f"Found test case '{test_name}' with {len(test_case.sequence)} sequence items",
        )

        # Create a working copy of the session to maintain state
        working_session = Session(**session.model_dump())

        # Iterate through the test sequence
        sequence_index = 0
        while sequence_index < len(test_case.sequence):
            sequence_item = test_case.sequence[sequence_index]

            logger.debug(
                f"Processing sequence item {sequence_index + 1}/{len(test_case.sequence)}",
            )

            # Convert session to request dictionary for matching
            request = working_session.model_dump()

            # Check if current request matches this sequence item
            if self._match_request(request, sequence_item):
                logger.info(
                    f"Match found at sequence item {sequence_index + 1}",
                )

                # Apply the canned response
                response = self._apply_response(
                    sequence_item.response,
                    working_session,
                )

                # Handle tool execution if response contains tool_use blocks
                if self._has_tool_uses(response):
                    tool_results = self._handle_tools(
                        response,
                        sequence_item.tool_behavior,
                        sequence_item.tool_results,
                    )

                    # Add tool results to session as a user message
                    if tool_results:
                        tool_result_blocks = [
                            ContentBlock(
                                type="tool_result",
                                tool_use_id=result["tool_use_id"],
                                content=result["content"],
                                is_error=result.get("is_error", False),
                            )
                            for result in tool_results
                        ]

                        working_session.messages.append(
                            Message(
                                role="user",
                                content=tool_result_blocks,
                            )
                        )

                        logger.debug(
                            f"Added {len(tool_results)} tool results to session",
                        )

                        # Continue to next sequence item to process tool results
                        sequence_index += 1
                        continue

                # Return final response
                logger.info(
                    f"Simulation complete at sequence item {sequence_index + 1}",
                )
                return self._format_api_response(response, working_session)

            else:
                logger.debug(
                    f"No match at sequence item {sequence_index + 1}, trying next",
                )
                sequence_index += 1

        # If we get here, no sequence item matched
        raise NoMatchError(
            f"No sequence item in test '{test_name}' matches the current request",
        )

    def _find_test_case(self, test_name: str) -> Optional[TestCase]:
        """
        Find a test case by name in the test configuration.

        Args:
            test_name: Name of the test case to find

        Returns:
            TestCase object if found, None otherwise
        """
        for test_case in self.test_config.tests:
            if test_case.name == test_name:
                return test_case
        return None

    def _match_request(
        self,
        request: Dict[str, Any],
        sequence_item: TestSequenceItem,
    ) -> bool:
        """
        Check if a request matches a sequence item's match rule.

        Uses RequestMatcher to evaluate the match rule against the request.

        Args:
            request: Dictionary representation of the session/request
            sequence_item: TestSequenceItem containing the match rule

        Returns:
            True if the request matches the rule, False otherwise
        """
        try:
            return self.request_matcher.match(request, sequence_item.match)
        except Exception as e:
            logger.error(f"Error matching request: {e}")
            return False

    def _apply_response(
        self,
        test_response: Any,
        session: Session,
    ) -> Dict[str, Any]:
        """
        Apply a canned response from the test configuration.

        Converts the TestResponse to a dictionary format and adds it to
        the session's message history.

        Args:
            test_response: TestResponse object from the sequence item
            session: Current session to update

        Returns:
            Dictionary representation of the response
        """
        # Convert TestResponse to dict
        response_dict = test_response.model_dump()

        # Add response to session messages
        session.messages.append(
            Message(
                role=response_dict["role"],
                content=[
                    ContentBlock(**block) for block in response_dict["content"]
                ],
            )
        )

        logger.debug(
            f"Applied canned response with {len(response_dict['content'])} content blocks",
        )

        return response_dict

    def _has_tool_uses(self, response: Dict[str, Any]) -> bool:
        """
        Check if a response contains any tool_use blocks.

        Args:
            response: Response dictionary

        Returns:
            True if response contains tool_use blocks, False otherwise
        """
        content = response.get("content", [])
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                return True
        return False

    def _handle_tools(
        self,
        response: Dict[str, Any],
        tool_behavior: str,
        tool_results: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Handle tool execution based on tool_behavior setting.

        Processes tool_use blocks in the response according to the specified
        behavior mode:
        - mock: Returns mock tool results from test configuration
        - execute: Executes real tools using the tool_executor
        - skip: No tool execution, returns empty list

        Args:
            response: Response dictionary containing tool_use blocks
            tool_behavior: One of "mock", "execute", or "skip"
            tool_results: Mock tool results from test config (for mock mode)

        Returns:
            List of tool result dictionaries with structure:
            [
                {
                    "tool_use_id": "...",
                    "content": "...",
                    "is_error": False
                },
                ...
            ]

        Raises:
            ToolExecutionError: If tool execution fails in execute mode
        """
        logger.debug(f"Handling tools with behavior: {tool_behavior}")

        # Extract tool_use blocks
        tool_uses = []
        content = response.get("content", [])
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_uses.append(block)

        if not tool_uses:
            return []

        logger.debug(f"Found {len(tool_uses)} tool_use blocks")

        # Handle based on behavior
        if tool_behavior == "skip":
            logger.debug("Skipping tool execution")
            return []

        elif tool_behavior == "mock":
            return self._handle_mock_tools(tool_uses, tool_results)

        elif tool_behavior == "execute":
            return self._handle_execute_tools(tool_uses)

        else:
            logger.warning(
                f"Unknown tool_behavior '{tool_behavior}', treating as skip",
            )
            return []

    def _handle_mock_tools(
        self,
        tool_uses: List[Dict[str, Any]],
        tool_results: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Handle mock tool execution using configured results.

        Args:
            tool_uses: List of tool_use blocks
            tool_results: Mock results from test config

        Returns:
            List of tool result dictionaries
        """
        logger.debug("Using mock tool results")

        results = []
        for tool_use in tool_uses:
            tool_id = tool_use.get("id")
            tool_name = tool_use.get("name")

            # Look up mock result for this tool
            if tool_results and tool_name in tool_results:
                result_content = tool_results[tool_name]
                logger.debug(f"Found mock result for tool '{tool_name}'")
            else:
                # Default mock result if not specified
                result_content = f"Mock result for {tool_name}"
                logger.debug(
                    f"No mock result configured for '{tool_name}', using default",
                )

            results.append(
                {
                    "tool_use_id": tool_id,
                    "content": result_content,
                    "is_error": False,
                }
            )

        return results

    def _handle_execute_tools(
        self,
        tool_uses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Handle real tool execution using the tool_executor.

        Args:
            tool_uses: List of tool_use blocks

        Returns:
            List of tool result dictionaries

        Raises:
            ToolExecutionError: If tool_executor is not configured or execution fails
        """
        logger.debug("Executing real tools")

        if not self.tool_executor:
            raise ToolExecutionError(
                "tool_behavior is 'execute' but no tool_executor was provided",
            )

        results = []
        for tool_use in tool_uses:
            tool_id = tool_use.get("id")
            tool_name = tool_use.get("name")
            tool_input = tool_use.get("input", {})

            logger.debug(f"Executing tool '{tool_name}' with input: {tool_input}")

            try:
                # Execute the tool
                result_content = self.tool_executor.execute_tool(
                    tool_name,
                    tool_input,
                )

                results.append(
                    {
                        "tool_use_id": tool_id,
                        "content": str(result_content),
                        "is_error": False,
                    }
                )

                logger.debug(f"Tool '{tool_name}' executed successfully")

            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}")

                results.append(
                    {
                        "tool_use_id": tool_id,
                        "content": f"Error executing {tool_name}: {str(e)}",
                        "is_error": True,
                    }
                )

        return results

    def _format_api_response(
        self,
        response: Dict[str, Any],
        session: Session,
    ) -> Dict[str, Any]:
        """
        Format the response to match Anthropic API response structure.

        Args:
            response: Response dictionary from test configuration
            session: Current session state

        Returns:
            Dictionary matching Anthropic API response format
        """
        # Determine stop_reason
        stop_reason = "end_turn"
        if self._has_tool_uses(response):
            stop_reason = "tool_use"

        # Create API response structure
        api_response = {
            "id": "sim_response",
            "type": "message",
            "role": response.get("role", "assistant"),
            "content": response.get("content", []),
            "model": session.model,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
            },
        }

        return api_response
