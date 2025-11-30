# AnthropIDE

This application is a web-app in python, using Bottle, that presents the user with an interface for maximum control of context and requests made to an anthropic model, in order for you to engineer prompts to the nth degree. You can then run the prompts yourself, or package them up to be run by customers, essentially 'prompts-as-a-product'. 
 
With this app you can define and design prompts that are general enough to be widely distributed, or specific enough that they can satisfy a single private companies internal workflow. You can also package your prompt with runnable skill scripts that will be accessible through the skill interface, and custom designed tools in python that will also be runnable by the model on the target system.
## Features

This application keeps (and initializes if missing) a app/projects/ subfolder where each subdirectory is a named project. Users can add a project through a webform that requests a name, if they create a project, the directory structure is automatically created for them, and all necessary files for the project are made.

They also have the option of choosing an existing project, which will load up the various parts of the project into the interface, and also checks that the folder structure is correct, including creating missing files based on a default template.

App structure

```
app/
  projects/
     example_project
       agents/
         agent-one.md <-- saved as .md file with a yaml header
       skills/
          skill-name/
            main.md
            additional.py
       tools/
         edit.json <- tool defined with a webform, compiled to correct json
         bash.json
         custom.py <-- tool defined in python which exports a dict definition from a `describe` function, and implements a `run` function that executes when the Model calls it.
       snippets/
         category-1/ <-- can create categories, and sub categories to organize snippets
           example_snippet.md
       tests/
         config.json <- a custom json object with rules for matching request data (system info, model, agent, message content) and returning pre-canned responses to facilitate testing of a workflow before trying it out on a real model. Can trigger skills, tools etc.
       current_session.json <- the current session
       current_session.json.202511231830 <- a previous session backend up when the user clicked "new session"
       state.json <- captures state of the project ui, which boxes checked, which widgets expanded
       
```

## Current Session Storage

Stores a `current_session.json` file with a complete representation of an Anthropic API call, and presents a UI to edit each part of the request with styled, responsive widgets.

Example:
```
{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 8192,

    "system": [
      {
        "type": "text",
        "text": "You are Claude Code, Anthropic's official CLI...\n\n# Tone and style\n- Be concise...\n\n<env>\nWorking directory: /home/user/myproject\nIs
  directory a git repo: Yes\nPlatform: linux\nToday's date: 2025-11-28\n</env>\n\ngitStatus: Current branch: main\nStatus:\nM  src/app.py\n?? README.md"
      },
      {
        "type": "text",
        "text": "Contents of /home/user/.claude/CLAUDE.md:\n- Use snake_case for variables...",
        "cache_control": {"type": "ephemeral"}
      }
    ],

    "tools": [
      {
        "name": "Read",
        "description": "Reads a file from the filesystem...",
        "input_schema": {
          "type": "object",
          "properties": {
            "file_path": {"type": "string", "description": "Absolute path"}
          },
          "required": ["file_path"]
        }
      },
      {
        "name": "Edit",
        "description": "Performs exact string replacements...",
        "input_schema": {
          "type": "object",
          "properties": {
            "file_path": {"type": "string"},
            "old_string": {"type": "string"},
            "new_string": {"type": "string"}
          },
          "required": ["file_path", "old_string", "new_string"]
        }
      },
      {
        "name": "Bash",
        "description": "Executes bash commands...",
        "input_schema": {
          "type": "object",
          "properties": {
            "command": {"type": "string"}
          },
          "required": ["command"]
        }
      }
    ],

    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Fix the typo in src/app.py where 'conection' should be 'connection'"
          }
        ]
      }
    ]
  }
```

The tools and messages sections are editable via webforms, with dropdown selects for restricted values, and text inputs for "content" additions and deletions.

Messages can be added, deleted, and re-ordered through drag and drop. By clicking on a header for the widget, the widget for any message, or section of the json can be collapsed, and shows a sample of the text, info, or type of data in the collapsed widget. Clicking a collapsed widget's header expands it again.

# Context Snippets

AnthropIDE also provides a sidebar to the left of the main widget that allows the user to create, edit, and delete Snippets of text that can be added to the messages portion of the main request as text. Snippets are edited in a large, wide Modale window with a rich text editor to the left, and a live update preview of the markdown text on the right. Users can name their snippets, and they are saved to a projects subfolder

Subcategories can be created, which are stored as subdirectories under snippets/ only two levels are supported

```
app/
  projects/
    <project name>
       current_sesson.json
       snippets/
          cat-1/
            snippet1
          cat-2/
            snippet2
         snippet2 <- is not categorized, category is optional
```

Context snippets are displayed in a collapsing/expanding menu. The state of expansion of the menu is saved in `state.json`

## Agents

Agents can be created via a webform and are saved in json on the disk in the agents/ subfolder. The format is like so:


```yaml
---
name: agent-identifier
description: Clear description of when and why to use this agent...
model: inherit
tools: tool1, tool2, tool3
skills: skill1, skill2
color: red
permissionMode: default
---
```

After the yaml header there will be the prompt that will be used when spawning the agent. The yaml fields will be edited via a modal webform, but the webform will also include a rich text edit and a preview diff to the right for editing the final prompt text that will be used for spawing the agent. The tools field will be a dropdown sourced from the project's tools section. 

## Skills

Skills can be created in much the same way as other things in the app, they have a yaml header that can be edited in a webform. The one additional feature of skills is that a user can click to edit a skill, and then there will be a button to add additional files. The main modal will edit `main.md` which the system uses to save the main skill information, but additional files in the directory will form tabs on the modal, these tabs will only show a rich text edit with no preview and will also require a filename. The content can be markdown, or executable scripts (bash, python, any language). On each tab there will be a save button and a delete button. Deleting should also remove the tab, and reactivate the main table. The main tab will have a create button for new skills, and also an Add file button, that will add a tab, show the table, and focus the rich edit. Clicking save on any tab saves everything in the modal. When creating a new skill AND a new file, the button should read "create" and there should be no delet button, but a cancel button. Clicking the cancel button on the new file tab only cancels the new file, deletes the new file tab, and returns the user to the main tab. clicking cancel on the main tab cancels everything and closes the modal.

## Simulation Endpoint

In order to facilitate developing this application, a submodule will be built that runs a simple, headless API server that given a project test description, will interact with any request by feeding back defined seed input to validate that the service sending requests is functioning. The testing api server can engage in multiple request response interactions in a threaded way to maximize performance.

## Prompts as a Product

You will be able to compress the filesystem for a project and port it to other systems, install it and run it from there. You will also be able to sell it, or deliver it as a deliverable to a client.

### Key Features

* a standalone cli module using the same libraries as AnthropIDE that can load packaged projects and run them in a headless AI agent for fully automated model usage.
* the ability to customize a model interaction context, tokens used, skills etc
* standalone cli module will also be able to test against the simulation service to run tests in the package.
