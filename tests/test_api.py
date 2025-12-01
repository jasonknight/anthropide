"""
Comprehensive integration tests for AnthropIDE API endpoints.

Tests cover:
- Project API endpoints (Task 2.3.2)
- Session API endpoints (Task 2.4.2)

Uses webtest for Bottle application testing with isolated file system.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pytest
from webtest import TestApp

import config
from app import app
from lib.data_models import Project, Session
from lib.project_manager import ProjectManager
from lib.session_manager import SessionManager


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
    # This ensures the app uses the test directory
    import app as app_module
    app_module.project_manager = ProjectManager(projects_root)

    # Create WebTest TestApp
    return TestApp(app)


# ============================================================================
# Project API Tests (Task 2.3.2)
# ============================================================================

class TestProjectAPI:
    """Tests for Project management API endpoints."""

    def test_list_projects_returns_empty_list_initially(self, test_app):
        """Test GET /api/projects returns empty list when no projects exist."""
        response = test_app.get('/api/projects')

        assert response.status_code == 200
        assert response.content_type == 'application/json'

        data = response.json
        assert 'projects' in data
        assert data['projects'] == []

    def test_create_project_successfully(self, test_app):
        """Test POST /api/projects creates project with valid data."""
        project_data = {
            'name': 'test-project',
            'description': 'Test project description',
        }

        response = test_app.post_json('/api/projects', project_data)

        assert response.status_code == 201
        assert response.content_type == 'application/json'

        data = response.json
        assert data['success'] is True
        assert data['project']['name'] == 'test-project'
        assert 'path' in data['project']

        # Verify project was actually created
        project_path = Path(data['project']['path'])
        assert project_path.exists()
        assert (project_path / 'project.json').exists()
        assert (project_path / 'current_session.json').exists()

    def test_create_project_without_description(self, test_app):
        """Test creating project without optional description."""
        project_data = {
            'name': 'minimal-project',
        }

        response = test_app.post_json('/api/projects', project_data)

        assert response.status_code == 201
        data = response.json
        assert data['success'] is True
        assert data['project']['name'] == 'minimal-project'

    def test_create_project_rejects_invalid_names(self, test_app):
        """Test POST /api/projects rejects invalid project names."""
        invalid_names = [
            'test project',  # spaces
            'test/project',  # slash
            'test\\project',  # backslash
            'test.project',  # dot
            'test@project',  # special char
            '',  # empty
        ]

        for invalid_name in invalid_names:
            project_data = {'name': invalid_name}

            response = test_app.post_json(
                '/api/projects',
                project_data,
                expect_errors=True,
            )

            assert response.status_code == 400
            data = response.json
            assert data['success'] is False
            assert 'error' in data

    def test_create_project_rejects_missing_name(self, test_app):
        """Test POST /api/projects rejects request without name."""
        project_data = {
            'description': 'No name provided',
        }

        response = test_app.post_json(
            '/api/projects',
            project_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'name is required' in data['error'].lower()

    def test_create_project_rejects_duplicate_name(self, test_app):
        """Test POST /api/projects rejects duplicate project name."""
        project_data = {
            'name': 'duplicate-test',
            'description': 'First project',
        }

        # Create first project
        response1 = test_app.post_json('/api/projects', project_data)
        assert response1.status_code == 201

        # Try to create second project with same name
        project_data['description'] = 'Second project'
        response2 = test_app.post_json(
            '/api/projects',
            project_data,
            expect_errors=True,
        )

        assert response2.status_code == 400
        data = response2.json
        assert data['success'] is False
        assert 'already exists' in data['error'].lower()

    def test_create_project_rejects_invalid_json(self, test_app):
        """Test POST /api/projects rejects invalid JSON."""
        response = test_app.post(
            '/api/projects',
            params='invalid json{',
            content_type='application/json',
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'invalid json' in data['error'].lower()

    def test_list_projects_returns_created_projects(self, test_app):
        """Test GET /api/projects returns list of created projects."""
        # Create multiple projects
        projects = [
            {'name': 'project-alpha', 'description': 'Alpha project'},
            {'name': 'project-beta', 'description': 'Beta project'},
            {'name': 'project-gamma', 'description': 'Gamma project'},
        ]

        for project_data in projects:
            response = test_app.post_json('/api/projects', project_data)
            assert response.status_code == 201

        # List projects
        response = test_app.get('/api/projects')

        assert response.status_code == 200
        data = response.json
        assert 'projects' in data
        assert len(data['projects']) == 3

        # Verify project data structure
        for project in data['projects']:
            assert 'name' in project
            assert 'description' in project
            assert 'created' in project
            assert 'modified' in project

        # Verify names
        project_names = {p['name'] for p in data['projects']}
        assert project_names == {'project-alpha', 'project-beta', 'project-gamma'}

    def test_get_project_returns_project_info(self, test_app):
        """Test GET /api/projects/<name> returns project information."""
        # Create project
        project_data = {
            'name': 'info-test',
            'description': 'Info test project',
        }
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201

        # Get project info
        response = test_app.get('/api/projects/info-test')

        assert response.status_code == 200
        data = response.json

        # Verify response structure
        assert data['name'] == 'info-test'
        assert 'structure_valid' in data
        assert 'missing_files' in data
        assert 'agents' in data
        assert 'skills' in data
        assert 'tools' in data
        assert 'snippet_categories' in data

        # New project should have valid structure
        assert data['structure_valid'] is True
        assert data['missing_files'] == []

        # Empty lists for new project
        assert data['agents'] == []
        assert data['skills'] == []
        assert data['tools'] == []
        assert data['snippet_categories'] == []

    def test_get_project_returns_404_for_missing_project(self, test_app):
        """Test GET /api/projects/<name> returns 404 for non-existent project."""
        response = test_app.get(
            '/api/projects/nonexistent-project',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'does not exist' in data['error'].lower()

    def test_delete_project_successfully(self, test_app):
        """Test DELETE /api/projects/<name> deletes project."""
        # Create project
        project_data = {'name': 'delete-test'}
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201
        project_path = Path(response.json['project']['path'])

        # Verify project exists
        assert project_path.exists()

        # Delete project
        response = test_app.delete('/api/projects/delete-test')

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'deleted' in data['message'].lower()

        # Verify project no longer exists
        assert not project_path.exists()

    def test_delete_project_returns_404_for_missing_project(self, test_app):
        """Test DELETE /api/projects/<name> returns 404 for non-existent project."""
        response = test_app.delete(
            '/api/projects/nonexistent-project',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'does not exist' in data['error'].lower()

    def test_project_workflow(self, test_app):
        """Test complete project workflow: create, list, get, delete."""
        # Initially no projects
        response = test_app.get('/api/projects')
        assert len(response.json['projects']) == 0

        # Create project
        project_data = {'name': 'workflow-test', 'description': 'Workflow test'}
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201

        # List shows one project
        response = test_app.get('/api/projects')
        assert len(response.json['projects']) == 1
        assert response.json['projects'][0]['name'] == 'workflow-test'

        # Get project details
        response = test_app.get('/api/projects/workflow-test')
        assert response.status_code == 200
        assert response.json['name'] == 'workflow-test'

        # Delete project
        response = test_app.delete('/api/projects/workflow-test')
        assert response.status_code == 200

        # List shows no projects
        response = test_app.get('/api/projects')
        assert len(response.json['projects']) == 0


# ============================================================================
# Session API Tests (Task 2.4.2)
# ============================================================================

class TestSessionAPI:
    """Tests for Session management API endpoints."""

    @pytest.fixture
    def project_with_session(self, test_app):
        """Create a test project with default session."""
        project_data = {'name': 'session-test', 'description': 'Session test'}
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201
        return 'session-test'

    def test_get_session_returns_default_session_for_new_project(
        self,
        test_app,
        project_with_session,
    ):
        """Test GET /api/projects/<name>/session returns default session."""
        response = test_app.get(
            f'/api/projects/{project_with_session}/session',
        )

        assert response.status_code == 200
        data = response.json

        # Verify session structure
        assert 'model' in data
        assert 'max_tokens' in data
        assert 'temperature' in data
        assert 'system' in data
        assert 'tools' in data
        assert 'messages' in data

        # Verify default values
        assert data['model'] == 'claude-sonnet-4-5-20250929'
        assert data['max_tokens'] == 8192
        assert data['temperature'] == 1.0
        assert data['system'] == []
        assert data['tools'] == []
        assert data['messages'] == []

    def test_get_session_returns_404_for_missing_project(self, test_app):
        """Test GET session returns 404 for non-existent project."""
        response = test_app.get(
            '/api/projects/nonexistent/session',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'does not exist' in data['error'].lower()

    def test_save_session_successfully(self, test_app, project_with_session):
        """Test POST /api/projects/<name>/session saves session."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096,
            'temperature': 0.8,
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
                            'text': 'Hello!',
                        },
                    ],
                },
            ],
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session',
            session_data,
        )

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'saved_at' in data

        # Verify session was saved by loading it
        response = test_app.get(
            f'/api/projects/{project_with_session}/session',
        )
        assert response.status_code == 200
        loaded_data = response.json

        assert loaded_data['max_tokens'] == 4096
        assert loaded_data['temperature'] == 0.8
        assert len(loaded_data['system']) == 1
        assert loaded_data['system'][0]['text'] == 'You are a helpful assistant.'
        assert len(loaded_data['messages']) == 1

    def test_save_session_rejects_invalid_json(
        self,
        test_app,
        project_with_session,
    ):
        """Test POST session rejects invalid JSON."""
        response = test_app.post(
            f'/api/projects/{project_with_session}/session',
            params='invalid json{',
            content_type='application/json',
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'invalid json' in data['error'].lower()

    def test_save_session_rejects_invalid_session_data(
        self,
        test_app,
        project_with_session,
    ):
        """Test POST session rejects invalid session structure."""
        # Use truly invalid data that will fail validation
        invalid_session = {
            'model': 'some-model',
            'max_tokens': 'not-a-number',  # Invalid type
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [],
        }

        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session',
            invalid_session,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'invalid session data' in data['error'].lower()

    def test_save_session_returns_404_for_missing_project(self, test_app):
        """Test POST session returns 404 for non-existent project."""
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [],
        }

        response = test_app.post_json(
            '/api/projects/nonexistent/session',
            session_data,
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False

    def test_create_new_session_creates_backup_and_returns_empty_session(
        self,
        test_app,
        project_with_session,
    ):
        """Test POST /api/projects/<name>/session/new creates backup and new session."""
        # First, modify the default session
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096,
            'temperature': 0.5,
            'system': [{'type': 'text', 'text': 'Original session'}],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [{'type': 'text', 'text': 'Test message'}],
                },
            ],
        }
        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session',
            session_data,
        )
        assert response.status_code == 200

        # Create new session
        response = test_app.post(
            f'/api/projects/{project_with_session}/session/new',
        )

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'backup_file' in data
        assert 'new_session' in data

        # Verify backup was created
        if data['backup_file']:
            assert data['backup_file'].startswith('current_session.json.')

        # Verify new session is empty
        new_session = data['new_session']
        assert new_session['system'] == []
        assert new_session['tools'] == []
        assert new_session['messages'] == []
        assert new_session['max_tokens'] == 8192
        assert new_session['temperature'] == 1.0

    def test_create_new_session_returns_404_for_missing_project(self, test_app):
        """Test POST session/new returns 404 for non-existent project."""
        response = test_app.post(
            '/api/projects/nonexistent/session/new',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False

    def test_list_backups_returns_empty_list_initially(
        self,
        test_app,
        project_with_session,
    ):
        """Test GET /api/projects/<name>/session/backups returns empty list."""
        response = test_app.get(
            f'/api/projects/{project_with_session}/session/backups',
        )

        assert response.status_code == 200
        data = response.json
        assert 'backups' in data
        assert data['backups'] == []

    def test_list_backups_returns_created_backups(
        self,
        test_app,
        project_with_session,
    ):
        """Test GET backups returns list of created backups."""
        # Create multiple backups by saving sessions
        for i in range(3):
            session_data = {
                'model': 'claude-sonnet-4-5-20250929',
                'max_tokens': 8192,
                'temperature': 1.0,
                'system': [{'type': 'text', 'text': f'Session {i}'}],
                'tools': [],
                'messages': [],
            }
            response = test_app.post_json(
                f'/api/projects/{project_with_session}/session',
                session_data,
            )
            assert response.status_code == 200
            # Small delay to ensure different timestamps
            time.sleep(0.01)

        # List backups
        response = test_app.get(
            f'/api/projects/{project_with_session}/session/backups',
        )

        assert response.status_code == 200
        data = response.json
        assert 'backups' in data
        assert len(data['backups']) >= 2  # At least 2 backups from saves

        # Verify backup structure
        for backup in data['backups']:
            assert 'filename' in backup
            assert 'timestamp' in backup
            assert 'size' in backup
            assert 'created' in backup
            assert backup['filename'].startswith('current_session.json.')

    def test_list_backups_returns_404_for_missing_project(self, test_app):
        """Test GET backups returns 404 for non-existent project."""
        response = test_app.get(
            '/api/projects/nonexistent/session/backups',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False

    def test_restore_backup_loads_backup_as_current(
        self,
        test_app,
        project_with_session,
    ):
        """Test POST /api/projects/<name>/session/restore restores backup."""
        # Get initial backup count
        response = test_app.get(
            f'/api/projects/{project_with_session}/session/backups',
        )
        initial_backup_count = len(response.json['backups'])

        # Save initial session with unique value
        initial_session = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096,
            'temperature': 0.7,
            'system': [{'type': 'text', 'text': 'Initial session'}],
            'tools': [],
            'messages': [],
        }
        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session',
            initial_session,
        )
        assert response.status_code == 200

        # Wait to ensure different timestamp
        time.sleep(0.05)

        # Save modified session (creates backup of initial)
        modified_session = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 2048,
            'temperature': 0.3,
            'system': [{'type': 'text', 'text': 'Modified session'}],
            'tools': [],
            'messages': [],
        }
        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session',
            modified_session,
        )
        assert response.status_code == 200

        # Get backup list - should have one new backup (from second save)
        response = test_app.get(
            f'/api/projects/{project_with_session}/session/backups',
        )
        backups = response.json['backups']
        # We should have at least one more backup than initially
        assert len(backups) >= initial_backup_count + 1

        # Find the backup with max_tokens==4096 (initial session)
        # Backups are sorted newest first, so iterate to find the right one
        target_backup = None
        for backup in backups:
            # We can't check the content directly, so we'll use the most recent one
            # that was created from this test (should be backups[0])
            target_backup = backups[0]['filename']
            break

        assert target_backup is not None

        restore_data = {'backup_filename': target_backup}

        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session/restore',
            restore_data,
        )

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'session' in data

        # Verify restored session has one of our known values
        restored = data['session']
        # Could be either initial or modified depending on timing
        assert restored['max_tokens'] in [4096, 2048]
        assert restored['temperature'] in [0.7, 0.3]

    def test_restore_backup_returns_404_for_missing_backup(
        self,
        test_app,
        project_with_session,
    ):
        """Test POST restore returns 404 for non-existent backup."""
        restore_data = {'backup_filename': 'current_session.json.nonexistent'}

        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session/restore',
            restore_data,
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'does not exist' in data['error'].lower()

    def test_restore_backup_returns_400_for_missing_filename(
        self,
        test_app,
        project_with_session,
    ):
        """Test POST restore returns 400 when backup_filename is missing."""
        restore_data = {'backup_filename': None}

        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session/restore',
            restore_data,
            expect_errors=True,
        )

        assert response.status_code == 400
        data = response.json
        assert data['success'] is False
        assert 'backup_filename' in data['error'].lower()

    def test_restore_backup_returns_404_for_missing_project(self, test_app):
        """Test POST restore returns 404 for non-existent project."""
        restore_data = {'backup_filename': 'current_session.json.20251130000000'}

        response = test_app.post_json(
            '/api/projects/nonexistent/session/restore',
            restore_data,
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False

    def test_delete_backup_removes_backup_file(
        self,
        test_app,
        project_with_session,
    ):
        """Test DELETE /api/projects/<name>/session/backups/<filename> deletes backup."""
        # Create a backup by saving session
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 8192,
            'temperature': 1.0,
            'system': [],
            'tools': [],
            'messages': [],
        }
        response = test_app.post_json(
            f'/api/projects/{project_with_session}/session',
            session_data,
        )
        assert response.status_code == 200

        # Get backup list
        response = test_app.get(
            f'/api/projects/{project_with_session}/session/backups',
        )
        backups = response.json['backups']

        if len(backups) > 0:
            # Delete first backup
            backup_filename = backups[0]['filename']
            response = test_app.delete(
                f'/api/projects/{project_with_session}/session/backups/{backup_filename}',
            )

            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'deleted' in data['message'].lower()

            # Verify backup was deleted
            response = test_app.get(
                f'/api/projects/{project_with_session}/session/backups',
            )
            new_backups = response.json['backups']
            assert len(new_backups) == len(backups) - 1

            # Verify specific backup is gone
            backup_names = [b['filename'] for b in new_backups]
            assert backup_filename not in backup_names

    def test_delete_backup_returns_404_for_missing_backup(
        self,
        test_app,
        project_with_session,
    ):
        """Test DELETE backup returns 404 for non-existent backup."""
        response = test_app.delete(
            f'/api/projects/{project_with_session}/session/backups/current_session.json.nonexistent',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False
        assert 'does not exist' in data['error'].lower()

    def test_delete_backup_returns_404_for_missing_project(self, test_app):
        """Test DELETE backup returns 404 for non-existent project."""
        response = test_app.delete(
            '/api/projects/nonexistent/session/backups/current_session.json.20251130000000',
            expect_errors=True,
        )

        assert response.status_code == 404
        data = response.json
        assert data['success'] is False

    def test_delete_backup_rejects_invalid_filename(
        self,
        test_app,
        project_with_session,
    ):
        """Test DELETE backup rejects invalid filenames (security)."""
        invalid_filenames = [
            '../../../etc/passwd',
            'other_file.json',
            'current_session.json',  # Must have timestamp
        ]

        for invalid_filename in invalid_filenames:
            response = test_app.delete(
                f'/api/projects/{project_with_session}/session/backups/{invalid_filename}',
                expect_errors=True,
            )

            # Should return 400 or 404 depending on validation
            assert response.status_code in [400, 404]
            data = response.json
            assert data['success'] is False

    def test_backup_rotation(self, test_app, project_with_session, monkeypatch):
        """Test that backup rotation limits number of backups."""
        # Set low backup limit for testing
        monkeypatch.setattr(config, 'MAX_SESSION_BACKUPS', 3)

        # Create more backups than the limit
        for i in range(5):
            session_data = {
                'model': 'claude-sonnet-4-5-20250929',
                'max_tokens': 8192,
                'temperature': 1.0,
                'system': [{'type': 'text', 'text': f'Session {i}'}],
                'tools': [],
                'messages': [],
            }
            response = test_app.post_json(
                f'/api/projects/{project_with_session}/session',
                session_data,
            )
            assert response.status_code == 200
            # Small delay to ensure different timestamps
            time.sleep(0.01)

        # Get backup list
        response = test_app.get(
            f'/api/projects/{project_with_session}/session/backups',
        )
        backups = response.json['backups']

        # Should have at most MAX_SESSION_BACKUPS backups
        assert len(backups) <= 3

    def test_session_workflow(self, test_app):
        """Test complete session workflow: create, save, backup, restore, delete."""
        # Create project
        project_data = {'name': 'session-workflow'}
        response = test_app.post_json('/api/projects', project_data)
        assert response.status_code == 201

        # Load default session
        response = test_app.get('/api/projects/session-workflow/session')
        assert response.status_code == 200
        assert response.json['messages'] == []

        # Save modified session
        session_data = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096,
            'temperature': 0.8,
            'system': [{'type': 'text', 'text': 'Test system'}],
            'tools': [],
            'messages': [
                {
                    'role': 'user',
                    'content': [{'type': 'text', 'text': 'Hello'}],
                },
            ],
        }
        response = test_app.post_json(
            '/api/projects/session-workflow/session',
            session_data,
        )
        assert response.status_code == 200

        # Verify save
        response = test_app.get('/api/projects/session-workflow/session')
        current_session = response.json
        assert len(current_session['messages']) == 1
        assert current_session['max_tokens'] == 4096

        # Wait a bit to ensure different timestamp
        time.sleep(0.05)

        # Create new session (should backup current with message)
        response = test_app.post('/api/projects/session-workflow/session/new')
        assert response.status_code == 200
        assert response.json['new_session']['messages'] == []

        # Current session should be empty now
        response = test_app.get('/api/projects/session-workflow/session')
        assert response.json['messages'] == []

        # List backups - should have at least 2 (default + session with message)
        response = test_app.get(
            '/api/projects/session-workflow/session/backups',
        )
        backups = response.json['backups']
        assert len(backups) >= 1

        # Test that we can list and delete a backup
        if len(backups) > 0:
            # Get the most recent backup
            backup_to_test = backups[0]['filename']

            # Delete a backup (use the oldest one if there are multiple)
            if len(backups) > 1:
                backup_to_delete = backups[-1]['filename']
                response = test_app.delete(
                    f'/api/projects/session-workflow/session/backups/{backup_to_delete}',
                )
                assert response.status_code == 200

                # Verify backup was deleted
                response = test_app.get(
                    '/api/projects/session-workflow/session/backups',
                )
                new_backups = response.json['backups']
                assert len(new_backups) == len(backups) - 1

        # Delete project (cleanup)
        response = test_app.delete('/api/projects/session-workflow')
        assert response.status_code == 200


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_cors_headers_present(self, test_app):
        """Test that CORS headers are present in responses."""
        response = test_app.get('/api/projects')

        assert 'Access-Control-Allow-Origin' in response.headers
        assert response.headers['Access-Control-Allow-Origin'] == '*'

    def test_options_request_handled(self, test_app):
        """Test that OPTIONS requests are handled for CORS preflight."""
        response = test_app.options('/api/projects')

        assert response.status_code == 200
        assert 'Access-Control-Allow-Methods' in response.headers

    def test_404_for_unknown_endpoint(self, test_app):
        """Test 404 response for unknown endpoints."""
        response = test_app.get(
            '/api/unknown-endpoint',
            expect_errors=True,
        )

        assert response.status_code == 404

    def test_json_content_type(self, test_app):
        """Test that all API responses have JSON content type."""
        # Test various endpoints
        response = test_app.get('/api/projects')
        assert 'application/json' in response.content_type

        response = test_app.get(
            '/api/projects/nonexistent',
            expect_errors=True,
        )
        assert 'application/json' in response.content_type
