# AnthropIDE

A web-based context/prompt engineering platform for designing, testing, and packaging sophisticated AI prompts as distributable products.

## Overview

AnthropIDE enables prompt engineers to create general-purpose or domain-specific AI workflows complete with custom tools, skills, and agents. It provides fine-grained control over Anthropic API requests and allows you to package your prompts for distribution as standalone CLI applications.

### Key Features

- **Prompts as Products**: Package prompts with tools and skills for distribution
- **Maximum Control**: Edit every aspect of Anthropic API requests
- **Test Before Deploy**: Simulate model responses for workflow validation
- **Portable**: Export projects as standalone CLI applications
- **Web-Based UI**: Intuitive interface built with jQuery and CodeMirror

### Technology Stack

- **Backend**: Python 3.12+ with Bottle framework
- **Frontend**: jQuery with jQuery UI components
- **Text Editor**: CodeMirror with markdown mode
- **Data Storage**: File-based JSON storage
- **API**: Anthropic SDK for Python

## Quick Start

### Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- An Anthropic API key

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd anthropide
```

2. Create and activate a virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your Anthropic API key:

```bash
# On Linux/Mac:
export ANTHROPIC_API_KEY='your-api-key-here'

# On Windows:
set ANTHROPIC_API_KEY=your-api-key-here
```

### Running the Application

1. Start the development server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:8080
```

3. The application will automatically create the necessary directory structure on first run.

## Project Structure

```
anthropide/
├── app.py                          # Main Bottle application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
│
├── lib/                            # Core library modules
│   ├── __init__.py
│   ├── project_manager.py          # Project CRUD operations
│   ├── session_manager.py          # Session persistence
│   ├── agent_manager.py            # Agent CRUD operations
│   ├── skill_manager.py            # Skill CRUD operations
│   ├── tool_manager.py             # Tool loading and execution
│   ├── snippet_manager.py          # Snippet CRUD operations
│   ├── test_simulator.py           # Test simulation engine
│   ├── validator.py                # JSON schema validation
│   ├── packager.py                 # Project packaging to zip
│   └── data_models.py              # Pydantic data models
│
├── cli/                            # Standalone CLI runner
│   ├── __init__.py
│   ├── main.py                     # CLI entry point
│   ├── runner.py                   # Execution engine
│   ├── plugin_loader.py            # Tool plugin system
│   └── history.py                  # Conversation history
│
├── static/                         # Frontend assets
│   ├── css/
│   │   ├── main.css
│   │   ├── widgets.css
│   │   └── themes/
│   ├── js/
│   │   ├── app.js                  # Main application logic
│   │   ├── project.js              # Project management
│   │   ├── session.js              # Session editor
│   │   ├── agents.js               # Agent editor
│   │   ├── skills.js               # Skill editor
│   │   ├── tools.js                # Tool editor
│   │   ├── snippets.js             # Snippet browser
│   │   ├── modal.js                # Modal dialog system
│   │   └── utils.js                # Utility functions
│   └── lib/                        # Third-party libraries
│       ├── jquery/
│       ├── jquery-ui/
│       ├── codemirror/
│       └── marked/                 # Markdown rendering
│
├── templates/                      # Jinja2 templates
│   ├── base.html                   # Base template
│   ├── index.html                  # Main application view
│   └── partials/
│       ├── project_selector.html
│       ├── session_editor.html
│       ├── snippet_browser.html
│       └── modals.html
│
├── projects/                       # User projects (created at runtime)
│   └── example_project/
│       ├── agents/                 # Agent definitions (*.md)
│       ├── skills/                 # Skill definitions (*.md)
│       ├── tools/                  # Tool definitions (*.json, *.py)
│       ├── snippets/               # Reusable snippets (**/*.md)
│       ├── tests/                  # Test configuration
│       │   └── config.json
│       ├── current_session.json    # Current API request state
│       ├── project.json            # Project metadata
│       └── requirements.txt        # Python dependencies for tools
│
├── tests/                          # Application tests
│
└── state.json                      # Global UI state (created at runtime)
```

## Configuration

The application can be configured via environment variables or by editing `config.py`:

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `ANTHROPIDE_HOST`: Server host (default: 127.0.0.1)
- `ANTHROPIDE_PORT`: Server port (default: 8080)
- `ANTHROPIDE_DEBUG`: Enable debug mode (default: true)
- `ANTHROPIDE_LOG_LEVEL`: Logging level (default: INFO)

### Configuration File

Edit `config.py` to customize:

- Directory paths
- API settings
- Default model configurations
- Session backup settings
- File size limits
- Editor preferences

## Usage

### Creating a Project

1. Click "New Project" in the main interface
2. Enter a project name (alphanumeric, underscores, and hyphens only)
3. Configure project metadata (description, default model, etc.)
4. Click "Create"

### Managing Sessions

Sessions represent the complete state of an Anthropic API request, including:

- System prompt
- Messages (conversation history)
- Tools and tool choice
- Model parameters (temperature, max_tokens, etc.)

Sessions are automatically saved to `current_session.json` with timestamped backups.

### Working with Agents

Agents are reusable system prompt templates stored as markdown files in the `agents/` directory. Use them to define different AI personas or specialized behaviors.

### Working with Skills

Skills are smaller, composable prompt fragments that can be loaded dynamically by agents. They're stored as markdown files in the `skills/` directory.

### Working with Tools

Tools are function definitions that the AI can call. Each tool consists of:

- A JSON schema file (`.json`) defining the tool's interface
- An optional Python implementation file (`.py`) for execution

### Snippets

Snippets are reusable text fragments organized in a hierarchical structure. Use them to quickly insert common prompt patterns, instructions, or examples.

### Testing and Simulation

Use the test simulator to validate your workflows without making actual API calls:

1. Configure test responses in `tests/config.json`
2. Enable test mode in the session editor
3. Run your workflow to see simulated responses

### Exporting Projects

Export your project as a standalone CLI application:

1. Click "Export" in the project menu
2. Download the generated ZIP file
3. Extract and run the CLI tool on any machine with Python installed

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lib --cov=cli

# Run specific test file
pytest tests/test_project_manager.py
```

### Code Style

This project follows PEP 8 style guidelines with the following conventions:

- Use type hints for all function signatures
- Maximum line length: 88 characters (Black formatter standard)
- Use trailing commas in multi-line collections
- Docstrings for all public functions and classes

### Adding New Features

1. Create feature branch from main
2. Implement changes with tests
3. Run test suite and ensure coverage
4. Submit pull request with description

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change the port via environment variable
export ANTHROPIDE_PORT=8081
python app.py
```

**API key not found:**
```bash
# Ensure your API key is set
echo $ANTHROPIC_API_KEY

# If empty, set it:
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Module not found errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Permission errors on directories:**
```bash
# Ensure project directory is writable
chmod -R u+w anthropide/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues, questions, or feature requests, please use the GitHub issue tracker.

## Acknowledgments

- Built with the Anthropic API
- Uses CodeMirror for text editing
- UI components from jQuery UI
- Markdown rendering by Marked

## Roadmap

- [ ] Multi-user support with authentication
- [ ] Version control for prompts and sessions
- [ ] Collaborative editing features
- [ ] Plugin marketplace for tools and skills
- [ ] Integration with version control systems
- [ ] Advanced analytics and prompt optimization
- [ ] Cloud deployment options
