/**
 * AnthropIDE - Skill Manager
 * Handles skill CRUD operations
 */

(function(window, $) {
    'use strict';

    const SkillManager = {
        skills: [],

        init: function() {
            $('#btn-new-skill').on('click', () => {
                Utils.showInfo('Skill creation coming soon!');
            });
        },

        loadSkills: function() {
            // TODO: Load skills from API
            console.log('Loading skills...');
        },
    };

    window.SkillManager = SkillManager;

})(window, jQuery);
