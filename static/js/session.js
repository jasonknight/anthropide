/**
 * AnthropIDE - Session Editor
 * Handles session editing, auto-save, and API request management
 */

(function(window, $) {
    'use strict';

    const SessionEditor = {
        currentSession: null,
        autoSaveTimer: null,
        isDirty: false,

        /**
         * Initialize session editor
         */
        init: function() {
            this.bindEvents();
        },

        /**
         * Bind event handlers
         */
        bindEvents: function() {
            // Model configuration
            $('#model-select').on('change', this.onModelChange.bind(this));
            $('#max-tokens').on('input', this.onMaxTokensChange.bind(this));
            $('#temperature').on('input', this.onTemperatureChange.bind(this));

            // Session actions
            $('#btn-new-session').on('click', this.newSession.bind(this));
            $('#btn-load-session').on('click', this.showSessionBrowser.bind(this));
            $('#btn-execute-session').on('click', this.executeSession.bind(this));

            // Section buttons
            $('#btn-add-system-prompt').on('click', this.showSystemPromptEditor.bind(this));
            $('#btn-add-tool').on('click', this.showToolSelector.bind(this));
            $('#btn-add-message').on('click', () => this.showMessageEditor());

            // Collapsible sections
            $('.section-header[data-section]').on('click', this.toggleSection.bind(this));
        },

        /**
         * Load session from API
         */
        loadSession: function() {
            const projectName = window.ProjectManager.getCurrentProject();
            if (!projectName) {
                return;
            }

            Utils.ajax({
                url: `/api/projects/${projectName}/session`,
                method: 'GET',
            })
            .then((data) => {
                this.currentSession = data;
                this.renderSession();
                $('#session-status').removeClass('error').addClass('saved').text('Loaded');
            })
            .catch((error) => {
                Utils.showError('Failed to load session: ' + error.message);
                $('#session-status').addClass('error').text('Error');
            });
        },

        /**
         * Render session in UI
         */
        renderSession: function() {
            if (!this.currentSession) {
                return;
            }

            // Render model config
            $('#model-select').val(this.currentSession.model || 'claude-sonnet-4-5-20250929');
            $('#max-tokens').val(this.currentSession.max_tokens || 8192);
            $('#temperature').val(this.currentSession.temperature || 1.0);
            $('#temperature-value').text(this.currentSession.temperature || 1.0);

            // Render system prompts
            this.renderSystemPrompts();

            // Render tools
            this.renderTools();

            // Render messages
            this.renderMessages();

            this.isDirty = false;
        },

        /**
         * Render system prompts section
         */
        renderSystemPrompts: function() {
            const $list = $('#system-prompts-list');
            $list.empty();

            const systemBlocks = this.currentSession.system || [];
            $('#system-prompts-count').text(systemBlocks.length);

            if (systemBlocks.length === 0) {
                $list.html('<div class="drop-zone-empty">No system prompts. Click "+ Add" to create one.</div>');
                return;
            }

            systemBlocks.forEach((block, index) => {
                const $block = this.createSystemPromptBlock(block, index);
                $list.append($block);
            });

            // Make sortable
            $list.sortable({
                handle: '.drag-handle',
                axis: 'y',
                update: () => {
                    this.reorderSystemPrompts();
                },
            });
        },

        /**
         * Create system prompt block element
         */
        createSystemPromptBlock: function(block, index) {
            const preview = Utils.truncate(block.text || '', 100);
            const cacheIndicator = block.cache_control ? '<span class="cache-badge">CACHED</span>' : '';

            return $(`
                <div class="system-prompt-block" data-index="${index}">
                    <div class="system-prompt-header">
                        <span class="drag-handle">⋮⋮</span>
                        <span class="system-prompt-type">
                            ${block.type === 'image' ? '🖼️' : '📝'} ${block.type}
                        </span>
                        ${cacheIndicator}
                    </div>
                    <div class="system-prompt-preview">${Utils.escapeHtml(preview)}</div>
                    <div class="system-prompt-actions">
                        <button class="icon-btn" onclick="SessionEditor.editSystemPrompt(${index})" title="Edit">✏️</button>
                        <button class="icon-btn danger" onclick="SessionEditor.deleteSystemPrompt(${index})" title="Delete">🗑️</button>
                    </div>
                </div>
            `);
        },

        /**
         * Render tools section
         */
        renderTools: function() {
            const $list = $('#tools-list');
            $list.empty();

            const tools = this.currentSession.tools || [];
            $('#tools-count').text(tools.length);

            if (tools.length === 0) {
                $list.html('<div class="drop-zone-empty">No tools added. Click "+ Add" to select tools.</div>');
                return;
            }

            tools.forEach((tool, index) => {
                const $tool = this.createToolItem(tool, index);
                $list.append($tool);
            });
        },

        /**
         * Create tool item element
         */
        createToolItem: function(tool, index) {
            const description = Utils.truncate(tool.description || '', 150);

            return $(`
                <div class="tool-item" data-index="${index}">
                    <span class="tool-icon">🔧</span>
                    <div class="tool-info">
                        <div class="tool-name">${Utils.escapeHtml(tool.name)}</div>
                        <div class="tool-description">${Utils.escapeHtml(description)}</div>
                    </div>
                    <div class="tool-actions">
                        <button class="icon-btn danger" onclick="SessionEditor.removeTool(${index})" title="Remove">✕</button>
                    </div>
                </div>
            `);
        },

        /**
         * Render messages section
         */
        renderMessages: function() {
            const $list = $('#messages-list');
            $list.empty();

            const messages = this.currentSession.messages || [];
            $('#messages-count').text(messages.length);

            if (messages.length === 0) {
                $list.html('<div class="drop-zone-empty">No messages. Click "+ Add" to create a message.</div>');
                return;
            }

            messages.forEach((message, index) => {
                const $message = this.createMessageBlock(message, index);
                $list.append($message);
            });

            // Make sortable
            $list.sortable({
                handle: '.drag-handle',
                axis: 'y',
                update: () => {
                    this.reorderMessages();
                },
            });
        },

        /**
         * Create message block element
         */
        createMessageBlock: function(message, index) {
            const roleIcon = message.role === 'user' ? '👤' : '🤖';
            const roleClass = `role-${message.role}`;

            let contentPreview = '';
            if (message.content && message.content.length > 0) {
                const firstContent = message.content[0];
                if (firstContent.type === 'text') {
                    contentPreview = Utils.truncate(firstContent.text || '', 150);
                } else if (firstContent.type === 'tool_use') {
                    contentPreview = `🔧 ${firstContent.name}(...)`;
                } else if (firstContent.type === 'tool_result') {
                    contentPreview = firstContent.is_error ? '✗ Error result' : '✓ Tool result';
                }
            }

            return $(`
                <div class="message-block ${roleClass}" data-index="${index}">
                    <div class="message-header">
                        <span class="drag-handle">⋮⋮</span>
                        <span class="message-role ${roleClass}">${roleIcon} ${message.role}</span>
                        <div class="message-actions ml-auto">
                            <button class="icon-btn" onclick="SessionEditor.editMessage(${index})" title="Edit">✏️</button>
                            <button class="icon-btn danger" onclick="SessionEditor.deleteMessage(${index})" title="Delete">🗑️</button>
                        </div>
                    </div>
                    <div class="message-content">
                        <div class="content-text">${Utils.escapeHtml(contentPreview)}</div>
                    </div>
                </div>
            `);
        },

        /**
         * Handle model change
         */
        onModelChange: function() {
            if (!this.currentSession) return;
            this.currentSession.model = $('#model-select').val();
            this.markDirty();
        },

        /**
         * Handle max tokens change
         */
        onMaxTokensChange: function() {
            if (!this.currentSession) return;
            const value = parseInt($('#max-tokens').val(), 10);
            if (!isNaN(value) && value > 0 && value <= 200000) {
                this.currentSession.max_tokens = value;
                this.markDirty();
            }
        },

        /**
         * Handle temperature change
         */
        onTemperatureChange: function() {
            if (!this.currentSession) return;
            const value = parseFloat($('#temperature').val());
            this.currentSession.temperature = value;
            $('#temperature-value').text(value.toFixed(1));
            this.markDirty();
        },

        /**
         * Mark session as dirty and trigger auto-save
         */
        markDirty: function() {
            this.isDirty = true;
            $('#session-status').removeClass('saved error').addClass('saving').text('Saving...');

            // Clear existing timer
            if (this.autoSaveTimer) {
                clearTimeout(this.autoSaveTimer);
            }

            // Set new timer (500ms debounce)
            this.autoSaveTimer = setTimeout(() => {
                this.saveSession();
            }, 500);
        },

        /**
         * Save session to API
         */
        saveSession: function() {
            const projectName = window.ProjectManager.getCurrentProject();
            if (!projectName || !this.currentSession) {
                return Promise.resolve();
            }

            return Utils.ajax({
                url: `/api/projects/${projectName}/session`,
                method: 'POST',
                data: JSON.stringify(this.currentSession),
            })
            .then(() => {
                this.isDirty = false;
                $('#session-status').removeClass('saving error').addClass('saved').text('Saved');
            })
            .catch((error) => {
                $('#session-status').removeClass('saving saved').addClass('error').text('Error');
                console.error('Failed to save session:', error);
            });
        },

        /**
         * Toggle section collapse/expand
         */
        toggleSection: function(e) {
            const $header = $(e.currentTarget);
            const $section = $header.closest('.widget-section');
            $section.toggleClass('collapsed');

            // Save state
            // TODO: Save to state.json
        },

        /**
         * Create new session
         */
        newSession: function() {
            Modal.confirm({
                title: 'Create New Session',
                message: 'This will backup the current session and start fresh. Continue?',
                confirmText: 'Create New',
            })
            .then((confirmed) => {
                if (confirmed) {
                    this.currentSession = {
                        model: 'claude-sonnet-4-5-20250929',
                        max_tokens: 8192,
                        temperature: 1.0,
                        system: [],
                        tools: [],
                        messages: [],
                    };
                    this.renderSession();
                    this.saveSession();
                    Utils.showSuccess('New session created');
                }
            });
        },

        /**
         * Stub methods for features to be implemented
         */
        showSystemPromptEditor: function(index) {
            Utils.showInfo('System prompt editor coming soon!');
        },

        editSystemPrompt: function(index) {
            this.showSystemPromptEditor(index);
        },

        deleteSystemPrompt: function(index) {
            if (!this.currentSession) return;
            this.currentSession.system.splice(index, 1);
            this.renderSystemPrompts();
            this.markDirty();
        },

        reorderSystemPrompts: function() {
            const newOrder = [];
            $('#system-prompts-list .system-prompt-block').each((i, el) => {
                const index = $(el).data('index');
                newOrder.push(this.currentSession.system[index]);
            });
            this.currentSession.system = newOrder;
            this.renderSystemPrompts();
            this.markDirty();
        },

        showToolSelector: function() {
            Utils.showInfo('Tool selector coming soon!');
        },

        removeTool: function(index) {
            if (!this.currentSession) return;
            this.currentSession.tools.splice(index, 1);
            this.renderTools();
            this.markDirty();
        },

        showMessageEditor: function(index) {
            Utils.showInfo('Message editor coming soon!');
        },

        editMessage: function(index) {
            this.showMessageEditor(index);
        },

        deleteMessage: function(index) {
            if (!this.currentSession) return;
            this.currentSession.messages.splice(index, 1);
            this.renderMessages();
            this.markDirty();
        },

        reorderMessages: function() {
            const newOrder = [];
            $('#messages-list .message-block').each((i, el) => {
                const index = $(el).data('index');
                newOrder.push(this.currentSession.messages[index]);
            });
            this.currentSession.messages = newOrder;
            this.renderMessages();
            this.markDirty();
        },

        showSessionBrowser: function() {
            Utils.showInfo('Session browser coming soon!');
        },

        executeSession: function() {
            Utils.showInfo('Session execution coming soon!');
        },
    };

    // Export to window
    window.SessionEditor = SessionEditor;

})(window, jQuery);
