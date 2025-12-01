/**
 * AnthropIDE - Main Application
 * Application initialization and global state management
 */

(function(window, $) {
    'use strict';

    const App = {
        initialized: false,

        /**
         * Initialize application
         */
        init: function() {
            if (this.initialized) {
                return;
            }

            console.log('Initializing AnthropIDE...');

            // Initialize components
            this.initializeComponents();

            // Bind global events
            this.bindGlobalEvents();

            // Set up tab navigation
            this.initializeTabs();

            this.initialized = true;
            console.log('AnthropIDE initialized successfully');
        },

        /**
         * Initialize all components
         */
        initializeComponents: function() {
            // Initialize managers
            if (window.ProjectManager) {
                window.ProjectManager.init();
            }

            if (window.SessionEditor) {
                window.SessionEditor.init();
            }

            if (window.SnippetBrowser) {
                window.SnippetBrowser.init();
            }

            if (window.AgentManager) {
                window.AgentManager.init();
            }

            if (window.SkillManager) {
                window.SkillManager.init();
            }

            if (window.ToolManager) {
                window.ToolManager.init();
            }
        },

        /**
         * Bind global event handlers
         */
        bindGlobalEvents: function() {
            // Handle beforeunload to save state
            $(window).on('beforeunload', () => {
                // Auto-save session if dirty
                if (window.SessionEditor && window.SessionEditor.isDirty) {
                    window.SessionEditor.saveSession();
                }
            });

            // Global AJAX error handler
            $(document).ajaxError((event, jqXHR, settings, thrownError) => {
                if (jqXHR.status === 401) {
                    Utils.showError('Authentication required');
                } else if (jqXHR.status === 403) {
                    Utils.showError('Access denied');
                } else if (jqXHR.status === 404) {
                    console.error('Not found:', settings.url);
                } else if (jqXHR.status >= 500) {
                    Utils.showError('Server error occurred');
                }
            });

            // Keyboard shortcuts
            $(document).on('keydown', (e) => {
                // Cmd/Ctrl + S to save
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    if (window.SessionEditor) {
                        window.SessionEditor.saveSession()
                            .then(() => {
                                Utils.showSuccess('Session saved');
                            });
                    }
                }

                // Cmd/Ctrl + N for new session
                if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                    e.preventDefault();
                    if (window.SessionEditor) {
                        window.SessionEditor.newSession();
                    }
                }
            });
        },

        /**
         * Initialize tab navigation
         */
        initializeTabs: function() {
            $('.tab-btn').on('click', function() {
                const tabName = $(this).data('tab');

                // Update active tab button
                $('.tab-btn').removeClass('active');
                $(this).addClass('active');

                // Show corresponding tab pane
                $('.tab-pane').removeClass('active');
                $(`#tab-${tabName}`).addClass('active');

                // Load data for tab if needed
                switch (tabName) {
                    case 'agents':
                        if (window.AgentManager) {
                            window.AgentManager.loadAgents();
                        }
                        break;
                    case 'skills':
                        if (window.SkillManager) {
                            window.SkillManager.loadSkills();
                        }
                        break;
                    case 'tools':
                        if (window.ToolManager) {
                            window.ToolManager.loadTools();
                        }
                        break;
                }
            });
        },

        /**
         * Save global UI state
         */
        saveUIState: Utils.debounce(function() {
            const state = {
                expanded_widgets: {},
                scroll_positions: {},
            };

            // Save expanded/collapsed state of sections
            $('.widget-section[data-section]').each(function() {
                const section = $(this).data('section');
                state.expanded_widgets[section] = !$(this).hasClass('collapsed');
            });

            // Save scroll positions
            state.scroll_positions.session_editor = $('#tab-session').scrollTop();
            state.scroll_positions.snippet_browser = $('#snippet-tree').scrollTop();

            // Send to API
            Utils.ajax({
                url: '/api/state',
                method: 'POST',
                data: JSON.stringify({ ui: state }),
            }).catch((error) => {
                console.error('Failed to save UI state:', error);
            });
        }, 1000),

        /**
         * Load global UI state
         */
        loadUIState: function() {
            Utils.ajax({
                url: '/api/state',
                method: 'GET',
            })
            .then((data) => {
                if (data.ui) {
                    this.restoreUIState(data.ui);
                }
            })
            .catch((error) => {
                console.log('No saved UI state found');
            });
        },

        /**
         * Restore UI state
         */
        restoreUIState: function(state) {
            // Restore expanded/collapsed sections
            if (state.expanded_widgets) {
                Object.keys(state.expanded_widgets).forEach((section) => {
                    const $section = $(`.widget-section[data-section="${section}"]`);
                    if (!state.expanded_widgets[section]) {
                        $section.addClass('collapsed');
                    }
                });
            }

            // Restore scroll positions
            if (state.scroll_positions) {
                if (state.scroll_positions.session_editor) {
                    $('#tab-session').scrollTop(state.scroll_positions.session_editor);
                }
                if (state.scroll_positions.snippet_browser) {
                    $('#snippet-tree').scrollTop(state.scroll_positions.snippet_browser);
                }
            }
        },
    };

    // Export to window
    window.App = App;

    // Initialize when document is ready
    $(document).ready(() => {
        App.init();
    });

})(window, jQuery);
