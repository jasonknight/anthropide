"""
Invalid Python tool - describe() returns invalid schema.

This tool's describe() returns a dictionary but with an invalid schema
(missing required 'type' field in input_schema).
"""


def describe():
    """Return invalid schema."""
    return {
        "name": "invalid_schema",
        "description": "Invalid schema tool",
        "input_schema": {
            # Missing 'type': 'object'
            "properties": {
                "param": {"type": "string"},
            },
        },
    }


def run(param):
    """Run function."""
    return f"Result: {param}"
