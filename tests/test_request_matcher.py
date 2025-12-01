"""
Comprehensive unit tests for RequestMatcher class.

Tests cover:
- Path extraction with dot notation
- Array indexing (positive and negative)
- Nested object traversal
- Regex matching
- Contains matching
- Full request matching
- Error handling for invalid paths
- Edge cases (empty values, special characters, complex structures)
"""

import pytest

from lib.data_models import TestMatch
from lib.request_matcher import RequestMatcher


class TestGetValueAtPath:
    """Tests for get_value_at_path method."""

    def test_simple_key_access(self):
        """Test accessing a simple top-level key."""
        matcher = RequestMatcher()
        obj = {"model": "claude-sonnet-4-5-20250929", "max_tokens": 8192}

        assert matcher.get_value_at_path(obj, "model") == "claude-sonnet-4-5-20250929"
        assert matcher.get_value_at_path(obj, "max_tokens") == 8192

    def test_nested_key_access(self):
        """Test accessing nested keys."""
        matcher = RequestMatcher()
        obj = {
            "settings": {
                "display": {
                    "theme": "dark",
                },
            },
        }

        assert matcher.get_value_at_path(obj, "settings.display.theme") == "dark"

    def test_array_index_access(self):
        """Test accessing array elements by index."""
        matcher = RequestMatcher()
        obj = {
            "messages": [
                {"role": "user", "text": "first"},
                {"role": "assistant", "text": "second"},
                {"role": "user", "text": "third"},
            ],
        }

        assert matcher.get_value_at_path(obj, "messages.0.role") == "user"
        assert matcher.get_value_at_path(obj, "messages.1.role") == "assistant"
        assert matcher.get_value_at_path(obj, "messages.2.text") == "third"

    def test_negative_array_index(self):
        """Test accessing array elements with negative indices."""
        matcher = RequestMatcher()
        obj = {
            "messages": [
                {"role": "user", "text": "first"},
                {"role": "assistant", "text": "second"},
                {"role": "user", "text": "third"},
            ],
        }

        assert matcher.get_value_at_path(obj, "messages.-1.text") == "third"
        assert matcher.get_value_at_path(obj, "messages.-2.role") == "assistant"
        assert matcher.get_value_at_path(obj, "messages.-3.role") == "user"

    def test_nested_content_blocks(self):
        """Test accessing nested content blocks like in API requests."""
        matcher = RequestMatcher()
        obj = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello world"},
                        {"type": "text", "text": "how are you"},
                    ],
                },
            ],
        }

        assert matcher.get_value_at_path(obj, "messages.0.content.0.text") == "hello world"
        assert matcher.get_value_at_path(obj, "messages.0.content.1.text") == "how are you"
        assert matcher.get_value_at_path(obj, "messages.0.content.0.type") == "text"

    def test_system_block_access(self):
        """Test accessing system block content."""
        matcher = RequestMatcher()
        obj = {
            "system": [
                {"type": "text", "text": "You are a helpful assistant."},
            ],
        }

        assert matcher.get_value_at_path(obj, "system.0.text") == "You are a helpful assistant."
        assert matcher.get_value_at_path(obj, "system.0.type") == "text"

    def test_tool_access(self):
        """Test accessing tool definitions."""
        matcher = RequestMatcher()
        obj = {
            "tools": [
                {"name": "bash", "description": "Run bash commands"},
                {"name": "read", "description": "Read files"},
            ],
        }

        assert matcher.get_value_at_path(obj, "tools.0.name") == "bash"
        assert matcher.get_value_at_path(obj, "tools.1.name") == "read"
        assert matcher.get_value_at_path(obj, "tools.0.description") == "Run bash commands"

    def test_invalid_path_returns_none(self):
        """Test that invalid paths return None."""
        matcher = RequestMatcher()
        obj = {"model": "claude-sonnet-4-5-20250929"}

        assert matcher.get_value_at_path(obj, "nonexistent") is None
        assert matcher.get_value_at_path(obj, "model.nonexistent") is None
        assert matcher.get_value_at_path(obj, "messages.0.content") is None

    def test_out_of_bounds_index_returns_none(self):
        """Test that out-of-bounds array indices return None."""
        matcher = RequestMatcher()
        obj = {"messages": [{"role": "user"}]}

        assert matcher.get_value_at_path(obj, "messages.5") is None
        assert matcher.get_value_at_path(obj, "messages.-10") is None

    def test_accessing_key_on_non_dict_returns_none(self):
        """Test that accessing a key on a non-dict returns None."""
        matcher = RequestMatcher()
        obj = {"value": "string"}

        assert matcher.get_value_at_path(obj, "value.key") is None

    def test_accessing_index_on_non_list_returns_none(self):
        """Test that accessing an index on a non-list returns None."""
        matcher = RequestMatcher()
        obj = {"value": {"key": "val"}}

        assert matcher.get_value_at_path(obj, "value.0") is None

    def test_empty_path_returns_object(self):
        """Test that empty path returns the object itself."""
        matcher = RequestMatcher()
        obj = {"model": "claude-sonnet-4-5-20250929"}

        assert matcher.get_value_at_path(obj, "") == obj

    def test_accessing_none_value(self):
        """Test accessing path through None values."""
        matcher = RequestMatcher()
        obj = {"messages": None}

        assert matcher.get_value_at_path(obj, "messages.0") is None

    def test_complex_api_request(self):
        """Test accessing values in a complex API request structure."""
        matcher = RequestMatcher()
        obj = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 8192,
            "temperature": 1.0,
            "system": [
                {"type": "text", "text": "You are a helpful assistant."},
            ],
            "tools": [
                {"name": "bash", "description": "Run bash"},
                {"name": "read", "description": "Read files"},
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello world"},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Hi there!"},
                        {
                            "type": "tool_use",
                            "id": "tool_123",
                            "name": "bash",
                            "input": {"command": "ls"},
                        },
                    ],
                },
            ],
        }

        # Test various paths
        assert matcher.get_value_at_path(obj, "model") == "claude-sonnet-4-5-20250929"
        assert matcher.get_value_at_path(obj, "messages.-1.role") == "assistant"
        assert matcher.get_value_at_path(obj, "messages.-1.content.0.text") == "Hi there!"
        assert matcher.get_value_at_path(obj, "messages.-1.content.1.type") == "tool_use"
        assert matcher.get_value_at_path(obj, "messages.-1.content.1.name") == "bash"
        assert matcher.get_value_at_path(obj, "system.0.text") == "You are a helpful assistant."
        assert matcher.get_value_at_path(obj, "tools.0.name") == "bash"


class TestMatchRegex:
    """Tests for match_regex method."""

    def test_simple_regex_match(self):
        """Test simple regex pattern matching."""
        matcher = RequestMatcher()

        assert matcher.match_regex("hello world", "hello") is True
        assert matcher.match_regex("hello world", "world") is True
        assert matcher.match_regex("hello world", "hello world") is True

    def test_regex_no_match(self):
        """Test regex patterns that don't match."""
        matcher = RequestMatcher()

        assert matcher.match_regex("hello world", "goodbye") is False
        assert matcher.match_regex("hello world", "^world") is False
        assert matcher.match_regex("hello world", "xyz") is False

    def test_complex_regex_patterns(self):
        """Test complex regex patterns."""
        matcher = RequestMatcher()

        assert matcher.match_regex("create a file", r"create.*file") is True
        assert matcher.match_regex("create a file", r"^create") is True
        assert matcher.match_regex("create a file", r"file$") is True
        assert matcher.match_regex("test123", r"\w+\d+") is True
        assert matcher.match_regex("test@example.com", r"\w+@\w+\.\w+") is True

    def test_regex_with_special_characters(self):
        """Test regex with special characters."""
        matcher = RequestMatcher()

        assert matcher.match_regex("test.file", r"test\.file") is True
        assert matcher.match_regex("test?query", r"test\?") is True

    def test_regex_case_sensitive(self):
        """Test that regex matching is case-sensitive by default."""
        matcher = RequestMatcher()

        assert matcher.match_regex("Hello", "hello") is False
        assert matcher.match_regex("Hello", "Hello") is True

    def test_regex_with_non_string_value(self):
        """Test regex matching with non-string values."""
        matcher = RequestMatcher()

        # Should convert to string
        assert matcher.match_regex(123, r"123") is True
        assert matcher.match_regex(123, r"\d+") is True
        assert matcher.match_regex(True, r"True") is True

    def test_regex_with_none_value(self):
        """Test regex matching with None value."""
        matcher = RequestMatcher()

        # Should convert None to empty string
        assert matcher.match_regex(None, r"^$") is True
        assert matcher.match_regex(None, r"None") is False

    def test_invalid_regex_pattern(self):
        """Test that invalid regex patterns raise ValueError."""
        matcher = RequestMatcher()

        with pytest.raises(ValueError, match="Invalid regex pattern"):
            matcher.match_regex("test", r"[invalid")


class TestMatchContains:
    """Tests for match_contains method."""

    def test_string_contains_substring(self):
        """Test substring matching in strings."""
        matcher = RequestMatcher()

        assert matcher.match_contains("hello world", "hello") is True
        assert matcher.match_contains("hello world", "world") is True
        assert matcher.match_contains("hello world", "lo wo") is True

    def test_string_no_substring(self):
        """Test strings that don't contain substring."""
        matcher = RequestMatcher()

        assert matcher.match_contains("hello world", "goodbye") is False
        assert matcher.match_contains("hello world", "xyz") is False

    def test_list_contains_element(self):
        """Test element membership in lists."""
        matcher = RequestMatcher()

        assert matcher.match_contains([1, 2, 3], 2) is True
        assert matcher.match_contains(["a", "b", "c"], "b") is True
        assert matcher.match_contains([1, 2, 3], 4) is False

    def test_tuple_contains_element(self):
        """Test element membership in tuples."""
        matcher = RequestMatcher()

        assert matcher.match_contains((1, 2, 3), 2) is True
        assert matcher.match_contains(("a", "b", "c"), "b") is True
        assert matcher.match_contains((1, 2, 3), 4) is False

    def test_dict_contains_key(self):
        """Test key membership in dictionaries."""
        matcher = RequestMatcher()

        assert matcher.match_contains({"a": 1, "b": 2}, "a") is True
        assert matcher.match_contains({"a": 1, "b": 2}, "b") is True
        assert matcher.match_contains({"a": 1, "b": 2}, "c") is False

    def test_contains_with_non_string_values(self):
        """Test contains matching with non-string values."""
        matcher = RequestMatcher()

        # Converts to string for comparison
        assert matcher.match_contains(12345, "23") is True
        assert matcher.match_contains(12345, "67") is False

    def test_contains_case_sensitive(self):
        """Test that contains matching is case-sensitive."""
        matcher = RequestMatcher()

        assert matcher.match_contains("Hello World", "Hello") is True
        assert matcher.match_contains("Hello World", "hello") is False

    def test_contains_with_empty_string(self):
        """Test contains with empty string."""
        matcher = RequestMatcher()

        # Empty string is in any string
        assert matcher.match_contains("hello", "") is True
        assert matcher.match_contains("", "") is True


class TestMatchMethod:
    """Tests for the main match method."""

    def test_match_with_contains_type(self):
        """Test full matching with contains type."""
        matcher = RequestMatcher()
        request = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello world"},
                    ],
                },
            ],
        }

        match_rule = TestMatch(
            type="contains",
            path="messages.0.content.0.text",
            value="hello",
        )

        assert matcher.match(request, match_rule) is True

    def test_match_with_regex_type(self):
        """Test full matching with regex type."""
        matcher = RequestMatcher()
        request = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "create a file"},
                    ],
                },
            ],
        }

        match_rule = TestMatch(
            type="regex",
            path="messages.0.content.0.text",
            pattern=r"create.*file",
        )

        assert matcher.match(request, match_rule) is True

    def test_match_with_invalid_path(self):
        """Test matching with invalid path returns False."""
        matcher = RequestMatcher()
        request = {"messages": []}

        match_rule = TestMatch(
            type="contains",
            path="nonexistent.path",
            value="test",
        )

        assert matcher.match(request, match_rule) is False

    def test_match_with_no_match(self):
        """Test matching when pattern doesn't match."""
        matcher = RequestMatcher()
        request = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello world"},
                    ],
                },
            ],
        }

        match_rule = TestMatch(
            type="contains",
            path="messages.0.content.0.text",
            value="goodbye",
        )

        assert matcher.match(request, match_rule) is False

    def test_match_with_system_prompt(self):
        """Test matching against system prompt."""
        matcher = RequestMatcher()
        request = {
            "system": [
                {"type": "text", "text": "You are a helpful assistant."},
            ],
        }

        match_rule = TestMatch(
            type="contains",
            path="system.0.text",
            value="helpful",
        )

        assert matcher.match(request, match_rule) is True

    def test_match_with_tools(self):
        """Test matching against tools."""
        matcher = RequestMatcher()
        request = {
            "tools": [
                {"name": "bash", "description": "Run bash commands"},
            ],
        }

        match_rule = TestMatch(
            type="contains",
            path="tools.0.name",
            value="bash",
        )

        assert matcher.match(request, match_rule) is True

    def test_match_with_negative_index(self):
        """Test matching using negative array indices."""
        matcher = RequestMatcher()
        request = {
            "messages": [
                {"role": "user", "text": "first"},
                {"role": "assistant", "text": "second"},
                {"role": "user", "text": "third"},
            ],
        }

        match_rule = TestMatch(
            type="contains",
            path="messages.-1.text",
            value="third",
        )

        assert matcher.match(request, match_rule) is True

    def test_match_missing_pattern_for_regex(self):
        """Test that regex match without pattern raises error."""
        matcher = RequestMatcher()
        request = {"messages": [{"text": "hello"}]}

        # Create a match rule and manually corrupt it
        match_rule = TestMatch(
            type="contains",
            path="messages.0.text",
            value="test",
        )
        match_rule.type = "regex"
        match_rule.pattern = None

        with pytest.raises(ValueError, match="requires 'pattern' field"):
            matcher.match(request, match_rule)

    def test_match_missing_value_for_contains(self):
        """Test that contains match without value raises error."""
        matcher = RequestMatcher()
        request = {"messages": [{"text": "hello"}]}

        # Create a match rule and manually corrupt it
        match_rule = TestMatch(
            type="regex",
            path="messages.0.text",
            pattern="test",
        )
        match_rule.type = "contains"
        match_rule.value = None

        with pytest.raises(ValueError, match="requires 'value' field"):
            matcher.match(request, match_rule)

    def test_match_with_complex_api_request(self):
        """Test matching with a complete API request structure."""
        matcher = RequestMatcher()
        request = {
            "model": "claude-sonnet-4-5-20250929",
            "max_tokens": 8192,
            "temperature": 1.0,
            "system": [
                {"type": "text", "text": "You are a helpful assistant."},
            ],
            "tools": [
                {"name": "bash", "description": "Run bash"},
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hello world"},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Hi there!"},
                    ],
                },
            ],
        }

        # Test various matches
        match_rules = [
            TestMatch(type="contains", path="model", value="claude"),
            TestMatch(type="regex", path="messages.0.content.0.text", pattern=r"hello.*world"),
            TestMatch(type="contains", path="messages.-1.role", value="assistant"),
            TestMatch(type="contains", path="system.0.text", value="helpful"),
            TestMatch(type="regex", path="tools.0.name", pattern=r"^bash$"),
        ]

        for rule in match_rules:
            assert matcher.match(request, rule) is True, f"Failed to match rule: {rule}"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_object(self):
        """Test matching against empty object."""
        matcher = RequestMatcher()

        assert matcher.get_value_at_path({}, "any.path") is None

    def test_empty_list(self):
        """Test accessing elements in empty list."""
        matcher = RequestMatcher()
        obj = {"messages": []}

        assert matcher.get_value_at_path(obj, "messages.0") is None

    def test_deeply_nested_structure(self):
        """Test accessing deeply nested structures."""
        matcher = RequestMatcher()
        obj = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep",
                        },
                    },
                },
            },
        }

        assert matcher.get_value_at_path(obj, "level1.level2.level3.level4.value") == "deep"

    def test_mixed_indices_and_keys(self):
        """Test paths with mixed array indices and object keys."""
        matcher = RequestMatcher()
        obj = {
            "data": [
                {
                    "items": [
                        {"name": "first"},
                        {"name": "second"},
                    ],
                },
            ],
        }

        assert matcher.get_value_at_path(obj, "data.0.items.1.name") == "second"

    def test_special_characters_in_values(self):
        """Test matching with special characters in values."""
        matcher = RequestMatcher()

        assert matcher.match_contains("test@example.com", "@") is True
        assert matcher.match_contains("path/to/file", "/") is True
        assert matcher.match_regex("price: $100", r"\$\d+") is True

    def test_unicode_characters(self):
        """Test matching with unicode characters."""
        matcher = RequestMatcher()

        assert matcher.match_contains("Hello 世界", "世界") is True
        assert matcher.match_contains("test 🎉", "🎉") is True
        assert matcher.match_regex("café", r"café") is True

    def test_very_long_strings(self):
        """Test matching with very long strings."""
        matcher = RequestMatcher()
        long_string = "a" * 10000

        assert matcher.match_contains(long_string, "aaa") is True
        assert matcher.match_regex(long_string, r"a+") is True

    def test_numeric_string_paths(self):
        """Test that numeric strings are treated as indices."""
        matcher = RequestMatcher()
        obj = {
            "items": ["first", "second", "third"],
        }

        # "0" should be treated as index 0
        assert matcher.get_value_at_path(obj, "items.0") == "first"
        assert matcher.get_value_at_path(obj, "items.1") == "second"

    def test_path_with_trailing_dot(self):
        """Test that paths with trailing dots work correctly."""
        matcher = RequestMatcher()
        obj = {"messages": [{"text": "hello"}]}

        # Note: split('.') on "messages.0." creates ['messages', '0', '']
        # Empty string part should be handled gracefully
        # This might return None or the value at messages.0 depending on implementation
        # Our implementation will try to access an empty key, which should fail
        result = matcher.get_value_at_path(obj, "messages.0.")
        assert result is None

    def test_all_numeric_keys_in_dict(self):
        """Test that numeric keys in dicts are treated as keys, not indices."""
        matcher = RequestMatcher()
        # If we have a dict with numeric string keys, they should be accessed as keys
        obj = {"0": "zero", "1": "one"}

        # Since obj is a dict (not a list), "0" should access the string key "0"
        assert matcher.get_value_at_path(obj, "0") == "zero"
        assert matcher.get_value_at_path(obj, "1") == "one"
