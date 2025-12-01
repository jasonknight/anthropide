/**
 * AnthropIDE - Agent Manager
 * Handles agent CRUD operations
 */

(function(window, $) {
    'use strict';

    const AgentManager = {
        agents: [],

        init: function() {
            $('#btn-new-agent').on('click', () => {
                Utils.showInfo('Agent creation coming soon!');
            });
        },

        loadAgents: function() {
            // TODO: Load agents from API
            console.log('Loading agents...');
        },
    };

    window.AgentManager = AgentManager;

})(window, jQuery);
