"""
Invalid Python tool - missing run() function.

This tool only has a describe() function, which violates the required structure.
"""


def describe():
    """
    Return tool definition.

    Returns:
        Dictionary containing tool name, description, and input schema
    """
    return {
        "name": "missing_run",
        "description": "Tool without run function",
        "input_schema": {
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                    "description": "Some parameter",
                },
            },
        },
    }
