# Test Fixtures for ToolManager

This directory contains test fixtures for testing the ToolManager class.

## Files

### Valid Tools

- **valid_json_tool.json**: A properly formatted JSON tool definition
- **valid_python_tool.py**: A properly formatted Python tool with describe() and run()

### Invalid Tools

- **invalid_json_tool.json**: JSON tool with invalid schema (missing 'type' in input_schema)
- **missing_describe.py**: Python tool without describe() function
- **bad_return_type.py**: Python tool where describe() returns string instead of dict
- **invalid_schema.py**: Python tool where describe() returns dict with invalid schema

## Usage

These fixtures are used by `tests/test_tool_manager.py` to test various error
conditions and validation scenarios in the ToolManager class.
