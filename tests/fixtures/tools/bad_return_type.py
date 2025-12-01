"""
Invalid Python tool - describe() returns wrong type.

This tool's describe() function returns a string instead of a dictionary.
"""


def describe():
    """Return wrong type - should return dict but returns string."""
    return "This should be a dictionary"


def run(param):
    """Run function."""
    return f"Result: {param}"
