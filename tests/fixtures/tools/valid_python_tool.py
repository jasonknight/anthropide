"""
Valid Python tool fixture for testing.

This tool follows the required structure with both describe() and run() functions.
"""


def describe():
    """
    Return tool definition.

    Returns:
        Dictionary containing tool name, description, and input schema
    """
    return {
        "name": "valid_python_tool",
        "description": "A valid Python tool fixture for testing",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to process",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of times to repeat",
                },
            },
            "required": ["text"],
        },
    }


def run(text, count=1):
    """
    Run the tool.

    Args:
        text: Text to process
        count: Number of times to repeat (default 1)

    Returns:
        Processed result as string
    """
    return f"Processed: {text * count}"
