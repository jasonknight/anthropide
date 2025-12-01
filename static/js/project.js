/**
 * AnthropIDE - Project Management
 * Handles project loading, creation, deletion, and export/import
 */

(function(window, $) {
    'use strict';

    const ProjectManager = {
        currentProject: null,
        projects: [],

        /**
         * Initialize project manager
         */
        init: function() {
            this.bindEvents();
            this.loadProjects();
        },

        /**
         * Bind event handlers
         */
        bindEvents: function() {
            $('#project-dropdown').on('change', this.onProjectChange.bind(this));
            $('#btn-new-project').on('click', this.showCreateProjectModal.bind(this));
            $('#btn-import-project').on('click', this.showImportProjectModal.bind(this));
            $('#btn-export-project').on('click', this.exportProject.bind(this));
            $('#btn-package-settings').on('click', this.showPackageSettings.bind(this));
        },

        /**
         * Load projects from API
         */
        loadProjects: function() {
            Utils.showLoading();

            Utils.ajax({
                url: '/api/projects',
                method: 'GET',
            })
            .then((data) => {
                this.projects = data.projects || [];
                this.populateDropdown();

                // Load last selected project from state
                this.loadLastSelectedProject();
            })
            .catch((error) => {
                Utils.showError('Failed to load projects: ' + error.message);
            })
            .finally(() => {
                Utils.hideLoading();
            });
        },

        /**
         * Populate project dropdown
         */
        populateDropdown: function() {
            const $dropdown = $('#project-dropdown');
            $dropdown.empty();

            // Add default option
            $dropdown.append('<option value="">Select a Project...</option>');

            // Add projects
            this.projects.forEach((project) => {
                const $option = $('<option></option>')
                    .val(project.name)
                    .text(project.name + (project.description ? ' - ' + project.description : ''));
                $dropdown.append($option);
            });

            // Update selection if current project is set
            if (this.currentProject) {
                $dropdown.val(this.currentProject);
            }
        },

        /**
         * Load last selected project from state
         */
        loadLastSelectedProject: function() {
            Utils.ajax({
                url: '/api/state',
                method: 'GET',
            })
            .then((data) => {
                if (data.selected_project) {
                    this.selectProject(data.selected_project);
                }
            })
            .catch((error) => {
                console.log('No saved state found');
            });
        },

        /**
         * Handle project dropdown change
         */
        onProjectChange: function() {
            const projectName = $('#project-dropdown').val();
            if (projectName) {
                this.selectProject(projectName);
            }
        },

        /**
         * Select and load a project
         * @param {string} name - Project name
         */
        selectProject: function(name) {
            if (!name || name === this.currentProject) {
                return;
            }

            Utils.showLoading();

            Utils.ajax({
                url: `/api/projects/${name}`,
                method: 'GET',
            })
            .then((data) => {
                this.currentProject = name;
                $('#project-dropdown').val(name);

                // Save selected project to state
                this.saveSelectedProject(name);

                // Notify other components
                if (window.SessionEditor) {
                    window.SessionEditor.loadSession();
                }
                if (window.SnippetBrowser) {
                    window.SnippetBrowser.loadSnippets();
                }
                if (window.AgentManager) {
                    window.AgentManager.loadAgents();
                }
                if (window.SkillManager) {
                    window.SkillManager.loadSkills();
                }
                if (window.ToolManager) {
                    window.ToolManager.loadTools();
                }

                Utils.showSuccess(`Project "${name}" loaded successfully`);
            })
            .catch((error) => {
                Utils.showError('Failed to load project: ' + error.message);
                this.currentProject = null;
                $('#project-dropdown').val('');
            })
            .finally(() => {
                Utils.hideLoading();
            });
        },

        /**
         * Save selected project to state
         */
        saveSelectedProject: function(name) {
            Utils.ajax({
                url: '/api/state',
                method: 'POST',
                data: JSON.stringify({
                    selected_project: name,
                }),
            })
            .catch((error) => {
                console.error('Failed to save state:', error);
            });
        },

        /**
         * Show create project modal
         */
        showCreateProjectModal: function() {
            const content = `
                <div class="form-group">
                    <label for="new-project-name">Project Name:</label>
                    <input type="text" id="new-project-name" class="form-control"
                           placeholder="my_project" pattern="[a-z0-9_-]+"
                           maxlength="50" required>
                    <small class="form-text text-muted">
                        Use lowercase letters, numbers, hyphens, and underscores only (max 50 chars)
                    </small>
                </div>
                <div class="form-group mt-2">
                    <label for="new-project-description">Description (optional):</label>
                    <textarea id="new-project-description" class="form-control"
                              rows="3" placeholder="Project description..."></textarea>
                </div>
            `;

            window.Modal.show({
                title: 'Create New Project',
                content: content,
                size: 'medium',
                buttons: [
                    {
                        text: 'Cancel',
                        class: 'btn-secondary',
                        onclick: function(modal) {
                            modal.hide();
                        },
                    },
                    {
                        text: 'Create',
                        class: 'btn-primary',
                        onclick: (modal) => {
                            this.createProject(modal);
                        },
                    },
                ],
            });

            // Focus on name input
            setTimeout(() => {
                $('#new-project-name').focus();
            }, 100);
        },

        /**
         * Create new project
         */
        createProject: function(modal) {
            const name = $('#new-project-name').val().trim();
            const description = $('#new-project-description').val().trim();

            // Validation
            if (!name) {
                Utils.showError('Project name is required');
                return;
            }

            if (!/^[a-z0-9_-]+$/.test(name)) {
                Utils.showError('Project name must contain only lowercase letters, numbers, hyphens, and underscores');
                return;
            }

            if (name.length > 50) {
                Utils.showError('Project name must be 50 characters or less');
                return;
            }

            // Check if project already exists
            if (this.projects.find(p => p.name === name)) {
                Utils.showError('A project with this name already exists');
                return;
            }

            Utils.showLoading();

            Utils.ajax({
                url: '/api/projects',
                method: 'POST',
                data: JSON.stringify({
                    name: name,
                    description: description || undefined,
                }),
            })
            .then((data) => {
                Utils.showSuccess(`Project "${name}" created successfully`);
                modal.hide();
                this.loadProjects();

                // Auto-select new project
                setTimeout(() => {
                    this.selectProject(name);
                }, 500);
            })
            .catch((error) => {
                Utils.showError('Failed to create project: ' + error.message);
            })
            .finally(() => {
                Utils.hideLoading();
            });
        },

        /**
         * Show import project modal
         */
        showImportProjectModal: function() {
            const content = `
                <div class="form-group">
                    <label for="import-project-file">Select Project ZIP File:</label>
                    <input type="file" id="import-project-file" class="form-control"
                           accept=".zip" required>
                    <small class="form-text text-muted">
                        Select an exported AnthropIDE project ZIP file
                    </small>
                </div>
                <div id="import-progress" class="mt-3" style="display: none;">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                </div>
            `;

            window.Modal.show({
                title: 'Import Project',
                content: content,
                size: 'medium',
                buttons: [
                    {
                        text: 'Cancel',
                        class: 'btn-secondary',
                        onclick: function(modal) {
                            modal.hide();
                        },
                    },
                    {
                        text: 'Import',
                        class: 'btn-primary',
                        onclick: (modal) => {
                            this.importProject(modal);
                        },
                    },
                ],
            });
        },

        /**
         * Import project from ZIP file
         */
        importProject: function(modal) {
            const fileInput = document.getElementById('import-project-file');
            const file = fileInput.files[0];

            if (!file) {
                Utils.showError('Please select a file');
                return;
            }

            if (!file.name.endsWith('.zip')) {
                Utils.showError('Please select a ZIP file');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            $('#import-progress').show();

            $.ajax({
                url: '/api/projects/import',
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                xhr: function() {
                    const xhr = new XMLHttpRequest();
                    xhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            const percentComplete = (e.loaded / e.total) * 100;
                            $('#import-progress .progress-bar').css('width', percentComplete + '%');
                        }
                    });
                    return xhr;
                },
                success: (data) => {
                    Utils.showSuccess(`Project "${data.project_name}" imported successfully`);
                    modal.hide();
                    this.loadProjects();

                    // Auto-select imported project
                    setTimeout(() => {
                        this.selectProject(data.project_name);
                    }, 500);
                },
                error: (xhr) => {
                    let message = 'Failed to import project';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        message = xhr.responseJSON.error;
                    }
                    Utils.showError(message);
                    $('#import-progress').hide();
                },
            });
        },

        /**
         * Export current project as ZIP
         */
        exportProject: function() {
            if (!this.currentProject) {
                Utils.showError('No project selected');
                return;
            }

            Utils.showLoading();

            // Create temporary download link
            const link = document.createElement('a');
            link.href = `/api/projects/${this.currentProject}/export`;
            link.download = `${this.currentProject}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            setTimeout(() => {
                Utils.hideLoading();
                Utils.showSuccess(`Project "${this.currentProject}" exported successfully`);
            }, 500);
        },

        /**
         * Show package settings modal (stub for now)
         */
        showPackageSettings: function() {
            if (!this.currentProject) {
                Utils.showError('No project selected');
                return;
            }

            Utils.showInfo('Package settings feature coming soon!');
        },

        /**
         * Delete project (with confirmation)
         * @param {string} name - Project name
         */
        deleteProject: function(name) {
            if (!name) {
                return;
            }

            Utils.confirm(
                `Are you sure you want to delete project "${name}"? This cannot be undone.`,
                (confirmed) => {
                    if (!confirmed) {
                        return;
                    }

                    Utils.showLoading();

                    Utils.ajax({
                        url: `/api/projects/${name}`,
                        method: 'DELETE',
                    })
                    .then(() => {
                        Utils.showSuccess(`Project "${name}" deleted successfully`);

                        // If deleted project was selected, clear selection
                        if (this.currentProject === name) {
                            this.currentProject = null;
                            $('#project-dropdown').val('');
                        }

                        this.loadProjects();
                    })
                    .catch((error) => {
                        Utils.showError('Failed to delete project: ' + error.message);
                    })
                    .finally(() => {
                        Utils.hideLoading();
                    });
                },
            );
        },

        /**
         * Get current project name
         * @returns {string|null} Current project name
         */
        getCurrentProject: function() {
            return this.currentProject;
        },
    };

    // Export to window
    window.ProjectManager = ProjectManager;

})(window, jQuery);
