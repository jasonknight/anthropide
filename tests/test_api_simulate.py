"""
Integration tests for simulate API endpoint (Task 6.4.2).

Tests cover:
- Simulating with specific test name
- Simulating with auto-match (no test_name)
- Simulating with streaming
- Tool execution in simulation
- Error cases:
  - Project not found
  - Test not found
  - No test config
  - No matching sequence
  - Invalid session data

Uses webtest for Bottle application testing with isolated file system.
"""

import json
from pathlib import Path

import pytest
from webtest import TestApp

import config
from app import app
from lib.data_models import Session, Message, ContentBlock
from lib.project_manager import ProjectManager


@pytest.fixture
def test_app(tmp_path, monkeypatch):
    """
    Create a TestApp instance with isolated projects directory.

    Uses tmp_path to ensure tests don't interfere with each other
    or with actual project data.
    """
    # Use tmp_path for projects directory
    projects_root = tmp_path / "projects"
    projects_root.mkdir(exist_ok=True)

    # Monkey patch config.PROJECT_ROOT
    monkeypatch.setattr(config, 'PROJECT_ROOT', projects_root)

    # Recreate project manager with new projects root
    import app as app_module
    app_module.project_manager = ProjectManager(projects_root)

    # Create WebTest TestApp
    return TestApp(app)


@pytest.fixture
def project_with_test_config(test_app, tmp_path, monkeypatch):
    """
    Create a test project with test configuration.

    Returns the project name for use in tests.
    """
    # Get the projects root from the monkeypatched config
    projects_root = config.PROJECT_ROOT

    # Create project via API
    project_data = {
        'name': 'test-project',
        'description': 'Test project with test config',
    }
    response = test_app.post_json('/api/projects', project_data)
    assert response.status_code == 201

    project_name = 'test-project'
    project_path = projects_root / project_name

    # Create tests directory
    tests_dir = project_path / 'tests'
    tests_dir.mkdir(exist_ok=True)

    # Create test configuration with multiple test cases
    test_config = {
        "tests": [
            {
                "name": "simple_greeting",
                "description": "Simple greeting test",
                "sequence": [
                    {
                        "match": {
                            "type": "contains",
                            "path": "messages.-1.content.0.text",
                            "value": "hello",
                        },
                        "response": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Hello! How can I help you today?",
                                },
                            ],
                        },
                        "tool_behavior": "skip",
                    },
                ],
            },
            {
                "name": "tool_test",
                "description": "Test with tool execution",
                "sequence": [
                    {
                        "match": {
                            "type": "contains",
                            "path": "messages.-1.content.0.text",
                            "value": "list files",
                        },
                        "response": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "tool_123",
                                    "name": "bash",
                                    "input": {"command": "ls"},
                                },
                            ],
                        },
                        "tool_behavior": "mock",
                        "tool_results": {
                            "bash": "file1.txt\nfile2.txt",
                        },
                    },
                    {
                        "match": {
                            "type": "contains",
                            "path": "messages.-1.content.0.content",
                            "value": "file1.txt",
                        },
                        "response": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "I found 2 files.",
                                },
                            ],
                        },
                        "tool_behavior": "skip",
                    },
                ],
            },
            {
                "name": "no_match_test",
                "description": "Test that requires specific input",
                "sequence": [
                    {
                        "match": {
                            "type": "contains",
                            "path": "messages.-1.content.0.text",
                            "value": "very_specific_phrase",
                        },
                        "response": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Matched!",
                                },
                            ],
                        },
                        "tool_behavior": "skip",
                    },
                ],
            },
        ],
    }

    # Write test config
    config_path = tests_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)

    return project_name


# ============================================================================
# Basic Simulation Tests
# ============================================================================

class TestSimulateBasic:
    """Tests for basic simulation functionality."""

    def test_simulate_with_specific_test_name(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating with a specific test name."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'stream': False,
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        data = response.json

        # Verify response structure
        assert data['role'] == 'assistant'
        assert data['model'] == 'claude-sonnet-4-5-20250929'
        assert data['stop_reason'] == 'end_turn'
        assert data['type'] == 'message'
        assert 'usage' in data
        assert 'id' in data

        # Verify content
        assert len(data['content']) == 1
        assert data['content'][0]['type'] == 'text'
        assert data['content'][0]['text'] == 'Hello! How can I help you today?'

    def test_simulate_with_auto_match(self, test_app, project_with_test_config):
        """Test simulating without test_name (auto-match to first test)."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'stream': False,
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        data = response.json

        # Should auto-match to first test (simple_greeting)
        assert data['role'] == 'assistant'
        assert data['stop_reason'] == 'end_turn'
        assert len(data['content']) == 1
        assert data['content'][0]['text'] == 'Hello! How can I help you today?'

    def test_simulate_returns_complete_api_response_format(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test that simulate returns complete Anthropic API response format."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        data = response.json

        # Verify all required API response fields
        assert 'id' in data
        assert 'type' in data
        assert data['type'] == 'message'
        assert 'role' in data
        assert data['role'] == 'assistant'
        assert 'content' in data
        assert isinstance(data['content'], list)
        assert 'model' in data
        assert 'stop_reason' in data
        assert 'stop_sequence' in data
        assert 'usage' in data
        assert 'input_tokens' in data['usage']
        assert 'output_tokens' in data['usage']


# ============================================================================
# Streaming Tests
# ============================================================================

class TestSimulateStreaming:
    """Tests for streaming simulation."""

    def test_simulate_with_streaming(self, test_app, project_with_test_config):
        """Test simulating with streaming enabled."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'stream': True,
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        data = response.json

        # Verify streaming response structure
        assert 'chunks' in data
        assert 'simulated' in data
        assert data['simulated'] is True
        assert isinstance(data['chunks'], list)
        assert len(data['chunks']) > 0

        # Verify chunk types
        chunk_types = [chunk['type'] for chunk in data['chunks']]
        assert 'message_start' in chunk_types
        assert 'content_block_start' in chunk_types
        assert 'content_block_delta' in chunk_types
        assert 'content_block_stop' in chunk_types
        assert 'message_delta' in chunk_types
        assert 'message_stop' in chunk_types

    def test_streaming_text_response_structure(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test streaming response structure for text content."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'stream': True,
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        chunks = response.json['chunks']

        # Find message_start chunk
        message_start = next(c for c in chunks if c['type'] == 'message_start')
        assert 'message' in message_start
        assert message_start['message']['role'] == 'assistant'
        assert message_start['message']['model'] == 'claude-sonnet-4-5-20250929'

        # Find content_block_start chunk
        block_start = next(c for c in chunks if c['type'] == 'content_block_start')
        assert 'index' in block_start
        assert 'content_block' in block_start
        assert block_start['content_block']['type'] == 'text'

        # Find content_block_delta chunks
        deltas = [c for c in chunks if c['type'] == 'content_block_delta']
        assert len(deltas) > 0
        for delta in deltas:
            assert 'index' in delta
            assert 'delta' in delta
            assert delta['delta']['type'] == 'text_delta'
            assert 'text' in delta['delta']

        # Find message_delta chunk
        message_delta = next(c for c in chunks if c['type'] == 'message_delta')
        assert 'delta' in message_delta
        assert 'stop_reason' in message_delta['delta']
        assert message_delta['delta']['stop_reason'] == 'end_turn'


# ============================================================================
# Tool Execution Tests
# ============================================================================

class TestSimulateToolExecution:
    """Tests for tool execution in simulation."""

    def test_simulate_with_tool_execution(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating with tool execution (mock behavior)."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [
                {
                    'name': 'bash',
                    'description': 'Run bash commands',
                    'input_schema': {
                        'type': 'object',
                        'properties': {
                            'command': {'type': 'string'},
                        },
                    },
                },
            ],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'list files',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'tool_test',
            'stream': False,
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        data = response.json

        # Should complete the full multi-turn conversation
        assert data['role'] == 'assistant'
        assert data['stop_reason'] == 'end_turn'
        assert len(data['content']) == 1
        assert data['content'][0]['type'] == 'text'
        assert data['content'][0]['text'] == 'I found 2 files.'

    def test_streaming_with_tool_use(self, test_app, project_with_test_config):
        """Test streaming response with tool_use content."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [
                {
                    'name': 'bash',
                    'description': 'Run bash commands',
                    'input_schema': {
                        'type': 'object',
                        'properties': {
                            'command': {'type': 'string'},
                        },
                    },
                },
            ],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'list files',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'tool_test',
            'stream': True,
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        data = response.json

        # Verify streaming response
        assert 'chunks' in data
        chunks = data['chunks']

        # Should have chunks for the final text response after tool execution
        chunk_types = [chunk['type'] for chunk in chunks]
        assert 'message_start' in chunk_types
        assert 'message_stop' in chunk_types


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestSimulateErrors:
    """Tests for error handling in simulate endpoint."""

    def test_simulate_project_not_found(self, test_app):
        """Test simulating with non-existent project returns 404."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': session_data,
        }

        response = test_app.post_json(
            '/api/projects/nonexistent-project/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'does not exist' in data['error'].lower()

    def test_simulate_test_not_found(self, test_app, project_with_test_config):
        """Test simulating with non-existent test name returns 400."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'nonexistent_test',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
        assert 'nonexistent_test' in data['error']

    def test_simulate_no_test_config(self, test_app):
        """Test simulating project without test config returns 400.

        Note: TestConfigManager creates an empty config if none exists,
        so this test verifies the behavior when config exists but is empty.
        """
        # Create project without test config
        project_data = {
            'name': 'no-config-project',
            'description': 'Project without test config',
        }
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201

        # Note: TestConfigManager auto-creates empty config.json if it doesn't exist
        # So when we try to simulate, it will create an empty config and return
        # "No tests found in test configuration"

        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_test',
            'session': session_data,
        }

        response = test_app.post_json(
            '/api/projects/no-config-project/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        # TestConfigManager auto-creates empty config, so we get this error
        assert 'no tests found' in data['error'].lower()

    def test_simulate_no_matching_sequence(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating with no matching sequence returns 400."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'this will not match',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'no_match_test',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        # Should mention no matching sequence
        assert 'no' in data['error'].lower()
        assert 'match' in data['error'].lower()

    def test_simulate_invalid_session_data(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating with invalid session data returns 400."""
        # Invalid session - max_tokens must be integer, not string
        invalid_session = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 'not-a-number',  # Invalid type
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': invalid_session,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'invalid session data' in data['error'].lower()

    def test_simulate_missing_session_data(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating without session data returns 400."""
        request_data = {
            'test_name': 'simple_greeting',
            # No session field
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'session' in data['error'].lower()
        assert 'required' in data['error'].lower()

    def test_simulate_invalid_json(self, test_app, project_with_test_config):
        """Test simulating with invalid JSON returns 400."""
        response = test_app.post(
            f'/api/projects/{project_with_test_config}/simulate',
            params='invalid json{',
            content_type='application/json',
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'invalid json' in data['error'].lower()

    def test_simulate_empty_test_config(self, test_app, tmp_path, monkeypatch):
        """Test simulating with empty test config returns 400."""
        # Get the projects root
        projects_root = config.PROJECT_ROOT

        # Create project
        project_data = {
            'name': 'empty-config-project',
            'description': 'Project with empty test config',
        }
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201

        project_path = projects_root / 'empty-config-project'
        tests_dir = project_path / 'tests'
        tests_dir.mkdir(exist_ok=True)

        # Create empty test config
        empty_config = {"tests": []}
        config_path = tests_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(empty_config, f)

        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'session': session_data,
        }

        response = test_app.post_json(
            '/api/projects/empty-config-project/simulate',
            request_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'no tests' in data['error'].lower()


# ============================================================================
# Edge Cases and Additional Tests
# ============================================================================

class TestSimulateEdgeCases:
    """Tests for edge cases in simulate endpoint."""

    def test_simulate_with_empty_request_body(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating with empty request body returns 400."""
        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            {},
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False

    def test_simulate_preserves_session_model(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test that simulate response uses session's model."""
        custom_model = 'claude-3-opus-20240229'
        session_data = {
            'model': custom_model,
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        data = response.json
        assert data['model'] == custom_model

    def test_simulate_with_system_prompt(self, test_app, project_with_test_config):
        """Test simulating with system prompt in session."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [
                {
                    'type': 'text',
                    'text': 'You are a helpful assistant.',
                },
            ],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        # Should succeed even with system prompt

    def test_simulate_with_multiple_messages(
        self,
        test_app,
        project_with_test_config,
    ):
        """Test simulating with multiple messages in conversation."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
                {
                    'role': 'assistant',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Hello! How can I help?',
                        },
                    ],
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello again',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert response.status_code == 200
        # Should match on the last message

    def test_simulate_cors_headers(self, test_app, project_with_test_config):
        """Test that CORS headers are present in simulate response."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'hello',
                        },
                    ],
                },
            ],
        }

        request_data = {
            'test_name': 'simple_greeting',
            'session': session_data,
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_test_config}/simulate',
            request_data,
        )

        assert 'Access-Control-Allow-Origin' in response.headers
        assert response.headers['Access-Control-Allow-Origin'] == '*'

    def test_simulate_options_request(self, test_app, project_with_test_config):
        """Test OPTIONS request for simulate endpoint."""
        response = test_app.options(
            f'/api/projects/{project_with_test_config}/simulate',
        )

        assert response.status_code == 200
        assert 'Access-Control-Allow-Methods' in response.headers
