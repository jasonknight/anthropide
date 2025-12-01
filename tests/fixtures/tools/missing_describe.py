"""
Invalid Python tool - missing describe() function.

This tool only has a run() function, which violates the required structure.
"""


def run(param):
    """
    This tool has no describe() function.

    Args:
        param: Some parameter

    Returns:
        Some result
    """
    return f"Result: {param}"
