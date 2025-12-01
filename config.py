"""
AnthropIDE Configuration

This module contains all configuration settings for the AnthropIDE application.
Settings can be overridden via environment variables.
"""

import os
from pathlib import Path

# Application settings
APP_ROOT = Path(__file__).parent
PROJECT_ROOT = APP_ROOT / 'projects'
STATIC_ROOT = APP_ROOT / 'static'
TEMPLATE_ROOT = APP_ROOT / 'templates'

# API settings
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DEFAULT_MODEL = 'claude-sonnet-4-5-20250929'

# Project settings
MAX_SESSION_BACKUPS = 20  # Default, user-configurable per project
AUTO_SAVE = True
SESSION_BACKUP_FORMAT = 'current_session.json.%Y%m%d%H%M%S%f'  # Added %f (microseconds) to prevent collisions

# File extensions
AGENT_EXT = '.md'
SKILL_EXT = '.md'
TOOL_JSON_EXT = '.json'
TOOL_PY_EXT = '.py'
SNIPPET_EXT = '.md'

# Validation
MAX_PROJECT_NAME_LENGTH = 50
ALLOWED_PROJECT_NAME_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
MAX_SNIPPET_CATEGORIES = 2  # Only two levels of nesting

# Server settings
HOST = os.getenv('ANTHROPIDE_HOST', '127.0.0.1')
PORT = int(os.getenv('ANTHROPIDE_PORT', '8080'))
DEBUG = os.getenv('ANTHROPIDE_DEBUG', 'true').lower() == 'true'
RELOADER = DEBUG
LOG_LEVEL = os.getenv('ANTHROPIDE_LOG_LEVEL', 'INFO')

# Ensure required directories exist
PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)
