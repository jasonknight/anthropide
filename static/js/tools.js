/**
 * AnthropIDE - Tool Manager
 * Handles tool CRUD operations
 */

(function(window, $) {
    'use strict';

    const ToolManager = {
        tools: [],

        init: function() {
            $('#btn-new-tool').on('click', () => {
                Utils.showInfo('Tool creation coming soon!');
            });
        },

        loadTools: function() {
            // TODO: Load tools from API
            console.log('Loading tools...');
        },
    };

    window.ToolManager = ToolManager;

})(window, jQuery);
