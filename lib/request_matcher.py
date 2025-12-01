"""
Request matching for test simulation in AnthropIDE.

This module provides the RequestMatcher class which matches API requests
against test configuration patterns using dot notation paths and various
matching strategies (regex, contains).
"""

import re
import logging
from typing import Any, Optional, Union, List, Dict

from lib.data_models import TestMatch

logger = logging.getLogger(__name__)


class RequestMatcher:
    """
    Matches API requests against test configuration patterns.

    Supports dot notation path traversal with array indexing (including
    negative indices) and multiple matching strategies (regex, contains).

    Examples:
        >>> matcher = RequestMatcher()
        >>> request = {"messages": [{"content": [{"text": "hello"}]}]}
        >>> match_rule = TestMatch(type="contains", path="messages.0.content.0.text", value="hello")
        >>> matcher.match(request, match_rule)
        True
    """

    def match(
        self,
        request: Dict[str, Any],
        match_rule: TestMatch,
    ) -> bool:
        """
        Check if a request matches a match rule.

        Args:
            request: The API request dictionary to match against
            match_rule: The TestMatch rule defining the pattern to match

        Returns:
            True if the request matches the rule, False otherwise

        Raises:
            ValueError: If the match rule has an invalid type or missing required fields
        """
        # Validate match rule configuration first
        if match_rule.type == "regex" and not match_rule.pattern:
            raise ValueError(
                "Match rule with type='regex' requires 'pattern' field",
            )

        if match_rule.type == "contains" and match_rule.value is None:
            raise ValueError(
                "Match rule with type='contains' requires 'value' field",
            )

        if match_rule.type not in ("regex", "contains"):
            raise ValueError(
                f"Unknown match type: {match_rule.type}",
            )

        try:
            # Extract the value at the specified path
            value = self.get_value_at_path(request, match_rule.path)

            # If value is None, path doesn't exist - no match
            if value is None:
                logger.debug(
                    f"Path '{match_rule.path}' not found in request, no match",
                )
                return False

            # Apply the appropriate matching strategy
            if match_rule.type == "regex":
                return self.match_regex(value, match_rule.pattern)
            else:  # match_rule.type == "contains"
                return self.match_contains(value, match_rule.value)

        except (KeyError, IndexError, TypeError) as e:
            logger.debug(
                f"Error accessing path '{match_rule.path}': {e}",
            )
            return False

    def get_value_at_path(
        self,
        obj: Any,
        path: str,
    ) -> Optional[Any]:
        """
        Extract a value from an object using dot notation path.

        Supports:
        - Dot notation for nested objects: "messages.content"
        - Array indexing: "messages.0.content"
        - Negative array indices: "messages.-1.content"

        Args:
            obj: The object to extract the value from
            path: Dot-separated path to the value

        Returns:
            The value at the specified path, or None if the path is invalid

        Examples:
            >>> matcher = RequestMatcher()
            >>> obj = {"messages": [{"content": [{"text": "hello"}]}]}
            >>> matcher.get_value_at_path(obj, "messages.0.content.0.text")
            'hello'
            >>> matcher.get_value_at_path(obj, "messages.-1.content.0.text")
            'hello'
            >>> matcher.get_value_at_path(obj, "messages.0.nonexistent")
            None
        """
        if not path:
            return obj

        # Split path into parts
        parts = path.split('.')

        current = obj

        for part in parts:
            if current is None:
                return None

            # Check if part looks like a number AND current is a list/tuple
            # This way, numeric keys in dicts are treated as keys, not indices
            if part.lstrip('-').isdigit() and isinstance(current, (list, tuple)):
                # It's an array index
                try:
                    index = int(part)
                    current = current[index]
                except (IndexError, TypeError, ValueError) as e:
                    logger.debug(
                        f"Error accessing index '{part}': {e}",
                    )
                    return None
            elif isinstance(current, dict):
                # It's an object key (including numeric string keys in dicts)
                if part not in current:
                    logger.debug(
                        f"Key '{part}' not found in dict",
                    )
                    return None
                current = current[part]
            else:
                # Current is neither list/tuple nor dict
                logger.debug(
                    f"Cannot access path part '{part}' on type {type(current).__name__}",
                )
                return None

        return current

    def match_regex(
        self,
        value: Any,
        pattern: str,
    ) -> bool:
        """
        Check if a value matches a regex pattern.

        Converts the value to a string before matching.

        Args:
            value: The value to match against
            pattern: The regex pattern to match

        Returns:
            True if the value matches the pattern, False otherwise

        Raises:
            ValueError: If the regex pattern is invalid
        """
        try:
            # Convert value to string for matching
            value_str = str(value) if value is not None else ""

            # Compile and search
            regex = re.compile(pattern)
            match = regex.search(value_str)

            if match:
                logger.debug(
                    f"Regex pattern '{pattern}' matched value: {value_str[:100]}",
                )
                return True
            else:
                logger.debug(
                    f"Regex pattern '{pattern}' did not match value: {value_str[:100]}",
                )
                return False

        except re.error as e:
            raise ValueError(
                f"Invalid regex pattern '{pattern}': {e}",
            ) from e

    def match_contains(
        self,
        value: Any,
        substring: Any,
    ) -> bool:
        """
        Check if a value contains a substring.

        Handles different types:
        - Strings: checks if substring is in value
        - Lists/tuples: checks if substring is an element
        - Other types: converts both to strings and checks substring

        Args:
            value: The value to check
            substring: The substring/element to look for

        Returns:
            True if value contains substring, False otherwise
        """
        try:
            # Handle list/tuple - check membership
            if isinstance(value, (list, tuple)):
                contains = substring in value
                logger.debug(
                    f"Checking if {substring} is in list of length {len(value)}: {contains}",
                )
                return contains

            # Handle string - check substring
            if isinstance(value, str):
                contains = str(substring) in value
                logger.debug(
                    f"Checking if '{substring}' is in string: {contains}",
                )
                return contains

            # Handle dict - check if substring is a key
            if isinstance(value, dict):
                contains = substring in value
                logger.debug(
                    f"Checking if '{substring}' is a key in dict: {contains}",
                )
                return contains

            # For other types, convert to string and check
            value_str = str(value)
            substring_str = str(substring)
            contains = substring_str in value_str
            logger.debug(
                f"Checking if '{substring_str}' is in converted string: {contains}",
            )
            return contains

        except Exception as e:
            logger.debug(
                f"Error checking contains: {e}",
            )
            return False
