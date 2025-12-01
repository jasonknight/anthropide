/**
 * AnthropIDE - Snippet Browser
 * Handles snippet tree, drag-and-drop, and snippet management
 */

(function(window, $) {
    'use strict';

    const SnippetBrowser = {
        snippets: [],
        categories: [],

        /**
         * Initialize snippet browser
         */
        init: function() {
            this.bindEvents();
        },

        /**
         * Bind event handlers
         */
        bindEvents: function() {
            $('#btn-new-snippet').on('click', this.createSnippet.bind(this));
            $('#btn-new-category').on('click', this.createCategory.bind(this));
        },

        /**
         * Load snippets from API
         */
        loadSnippets: function() {
            const projectName = window.ProjectManager.getCurrentProject();
            if (!projectName) {
                return;
            }

            Utils.ajax({
                url: `/api/projects/${projectName}/snippets`,
                method: 'GET',
            })
            .then((data) => {
                this.snippets = data.snippets || [];
                this.categories = data.categories || [];
                this.renderTree();
            })
            .catch((error) => {
                console.error('Failed to load snippets:', error);
            });
        },

        /**
         * Render snippet tree
         */
        renderTree: function() {
            const $tree = $('#snippet-tree');
            $tree.empty();

            if (this.snippets.length === 0) {
                $tree.html(`
                    <div class="snippet-tree-empty">
                        <p>No snippets yet.</p>
                        <p>Create your first snippet to get started!</p>
                    </div>
                `);
                return;
            }

            // Group snippets by category
            const grouped = this.groupSnippetsByCategory();

            // Render categories
            Object.keys(grouped).forEach((category) => {
                const $category = this.createCategoryElement(category, grouped[category]);
                $tree.append($category);
            });
        },

        /**
         * Group snippets by category
         */
        groupSnippetsByCategory: function() {
            const grouped = {};

            this.snippets.forEach((snippet) => {
                const category = snippet.category || 'uncategorized';
                if (!grouped[category]) {
                    grouped[category] = [];
                }
                grouped[category].push(snippet);
            });

            return grouped;
        },

        /**
         * Create category element
         */
        createCategoryElement: function(categoryName, snippets) {
            const $category = $(`
                <div class="snippet-category">
                    <div class="category-header">
                        <span class="category-icon">📁</span>
                        <span class="category-name">${Utils.escapeHtml(categoryName)}</span>
                        <span class="category-collapse-icon">▼</span>
                    </div>
                    <div class="category-items"></div>
                </div>
            `);

            const $items = $category.find('.category-items');

            snippets.forEach((snippet) => {
                const $item = this.createSnippetElement(snippet);
                $items.append($item);
            });

            // Click to toggle
            $category.find('.category-header').on('click', function() {
                $category.toggleClass('collapsed');
            });

            return $category;
        },

        /**
         * Create snippet element
         */
        createSnippetElement: function(snippet) {
            return $(`
                <div class="snippet-item" data-path="${snippet.path}">
                    <span class="snippet-icon">📄</span>
                    <span class="snippet-name">${Utils.escapeHtml(snippet.name)}</span>
                </div>
            `);
        },

        /**
         * Create new snippet
         */
        createSnippet: function() {
            Utils.showInfo('Snippet creation coming soon!');
        },

        /**
         * Create new category
         */
        createCategory: function() {
            Modal.prompt({
                title: 'New Category',
                message: 'Category name:',
                placeholder: 'category-name',
            })
            .then((name) => {
                if (name) {
                    Utils.showInfo('Category creation coming soon!');
                }
            });
        },
    };

    // Export to window
    window.SnippetBrowser = SnippetBrowser;

})(window, jQuery);
