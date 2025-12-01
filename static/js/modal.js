/**
 * AnthropIDE - Modal System
 * Reusable modal dialog system using jQuery UI
 */

(function(window, $) {
    'use strict';

    const Modal = {
        activeModals: [],
        modalCounter: 0,

        /**
         * Show a modal dialog
         * @param {Object} options - Modal options
         * @param {string} options.title - Modal title
         * @param {string|HTMLElement|jQuery} options.content - Modal content
         * @param {string} options.size - Modal size: 'small', 'medium', 'large', 'fullscreen'
         * @param {Array} options.buttons - Array of button objects
         * @param {Function} options.onClose - Callback when modal closes
         * @returns {Object} Modal instance
         */
        show: function(options) {
            const defaults = {
                title: 'Dialog',
                content: '',
                size: 'medium',
                buttons: [],
                onClose: null,
                closeOnEscape: true,
                closeOnClickOutside: false,
            };

            const settings = $.extend({}, defaults, options);
            const modalId = `modal-${++this.modalCounter}`;

            // Create modal HTML
            const $modal = this.createModalElement(modalId, settings);

            // Add to DOM
            $('body').append($modal);

            // Calculate width based on size
            const widths = {
                small: 400,
                medium: 600,
                large: 900,
                fullscreen: $(window).width() - 40,
            };

            const width = widths[settings.size] || widths.medium;

            // Calculate height for fullscreen
            const height = settings.size === 'fullscreen' ?
                $(window).height() - 40 : 'auto';

            // Initialize jQuery UI dialog
            $modal.dialog({
                modal: true,
                width: width,
                height: height,
                title: settings.title,
                closeOnEscape: settings.closeOnEscape,
                close: () => {
                    this.onModalClose(modalId, settings.onClose);
                },
                open: function() {
                    // Remove default jQuery UI buttons
                    $(this).parent().find('.ui-dialog-buttonpane').remove();
                },
            });

            // Store modal instance
            const modalInstance = {
                id: modalId,
                $element: $modal,
                hide: () => {
                    $modal.dialog('close');
                },
                setContent: (content) => {
                    $modal.find('.modal-body').html(content);
                },
                setTitle: (title) => {
                    $modal.dialog('option', 'title', title);
                },
            };

            this.activeModals.push(modalInstance);

            // Handle click outside to close
            if (settings.closeOnClickOutside) {
                $('.ui-widget-overlay').on('click', () => {
                    modalInstance.hide();
                });
            }

            return modalInstance;
        },

        /**
         * Create modal HTML element
         */
        createModalElement: function(modalId, settings) {
            const $modal = $(`
                <div id="${modalId}" class="anthropide-modal" style="display: none;">
                    <div class="modal-body">
                        ${typeof settings.content === 'string' ? settings.content : ''}
                    </div>
                    ${settings.buttons.length > 0 ? this.createButtonBar(modalId, settings.buttons) : ''}
                </div>
            `);

            // If content is not a string, append it
            if (typeof settings.content !== 'string') {
                $modal.find('.modal-body').append(settings.content);
            }

            return $modal;
        },

        /**
         * Create button bar HTML
         */
        createButtonBar: function(modalId, buttons) {
            const $buttonBar = $('<div class="modal-footer"></div>');

            buttons.forEach((button) => {
                const $button = $(`
                    <button class="btn ${button.class || 'btn-secondary'}">
                        ${button.text || 'Button'}
                    </button>
                `);

                $button.on('click', () => {
                    const modalInstance = this.getModalById(modalId);
                    if (button.onclick) {
                        button.onclick(modalInstance);
                    }
                });

                $buttonBar.append($button);
            });

            return $buttonBar;
        },

        /**
         * Handle modal close
         */
        onModalClose: function(modalId, callback) {
            const $modal = $(`#${modalId}`);

            // Call onClose callback
            if (callback) {
                callback();
            }

            // Remove from active modals
            this.activeModals = this.activeModals.filter(m => m.id !== modalId);

            // Destroy dialog and remove from DOM
            $modal.dialog('destroy').remove();
        },

        /**
         * Get modal instance by ID
         */
        getModalById: function(modalId) {
            return this.activeModals.find(m => m.id === modalId);
        },

        /**
         * Hide modal by ID
         */
        hide: function(modalId) {
            const modal = this.getModalById(modalId);
            if (modal) {
                modal.hide();
            }
        },

        /**
         * Hide all modals
         */
        hideAll: function() {
            this.activeModals.forEach(modal => {
                modal.hide();
            });
        },

        /**
         * Confirmation dialog
         * @param {Object} options
         * @returns {Promise} Resolves with true/false
         */
        confirm: function(options) {
            return new Promise((resolve) => {
                const settings = $.extend({
                    title: 'Confirm',
                    message: 'Are you sure?',
                    confirmText: 'Confirm',
                    cancelText: 'Cancel',
                    confirmClass: 'btn-primary',
                }, options);

                this.show({
                    title: settings.title,
                    content: `<p>${settings.message}</p>`,
                    size: 'small',
                    buttons: [
                        {
                            text: settings.cancelText,
                            class: 'btn-secondary',
                            onclick: (modal) => {
                                resolve(false);
                                modal.hide();
                            },
                        },
                        {
                            text: settings.confirmText,
                            class: settings.confirmClass,
                            onclick: (modal) => {
                                resolve(true);
                                modal.hide();
                            },
                        },
                    ],
                });
            });
        },

        /**
         * Alert dialog
         * @param {Object} options
         * @returns {Promise}
         */
        alert: function(options) {
            return new Promise((resolve) => {
                const settings = $.extend({
                    title: 'Alert',
                    message: '',
                    buttonText: 'OK',
                }, options);

                this.show({
                    title: settings.title,
                    content: `<p>${settings.message}</p>`,
                    size: 'small',
                    buttons: [
                        {
                            text: settings.buttonText,
                            class: 'btn-primary',
                            onclick: (modal) => {
                                resolve();
                                modal.hide();
                            },
                        },
                    ],
                });
            });
        },

        /**
         * Prompt dialog
         * @param {Object} options
         * @returns {Promise} Resolves with input value or null
         */
        prompt: function(options) {
            return new Promise((resolve) => {
                const settings = $.extend({
                    title: 'Input',
                    message: '',
                    placeholder: '',
                    defaultValue: '',
                    confirmText: 'OK',
                    cancelText: 'Cancel',
                }, options);

                const inputId = `prompt-input-${Date.now()}`;
                const content = `
                    <div class="form-group">
                        <label>${settings.message}</label>
                        <input type="text" id="${inputId}" class="form-control"
                               placeholder="${settings.placeholder}"
                               value="${settings.defaultValue}">
                    </div>
                `;

                this.show({
                    title: settings.title,
                    content: content,
                    size: 'small',
                    buttons: [
                        {
                            text: settings.cancelText,
                            class: 'btn-secondary',
                            onclick: (modal) => {
                                resolve(null);
                                modal.hide();
                            },
                        },
                        {
                            text: settings.confirmText,
                            class: 'btn-primary',
                            onclick: (modal) => {
                                const value = $(`#${inputId}`).val();
                                resolve(value);
                                modal.hide();
                            },
                        },
                    ],
                });

                // Focus input after modal opens
                setTimeout(() => {
                    $(`#${inputId}`).focus();
                }, 100);
            });
        },
    };

    // Export to window
    window.Modal = Modal;

})(window, jQuery);
