/**
 * AnthropIDE - Utility Functions
 * Shared utility functions for the application
 */

(function(window) {
    'use strict';

    const Utils = {
        /**
         * Show loading overlay
         */
        showLoading: function() {
            let overlay = document.getElementById('loading-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'loading-overlay';
                overlay.innerHTML = '<div class="spinner"></div>';
                document.body.appendChild(overlay);
            }
            overlay.classList.add('active');
        },

        /**
         * Hide loading overlay
         */
        hideLoading: function() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.remove('active');
            }
        },

        /**
         * Show toast notification
         * @param {string} message - Message to display
         * @param {string} type - Type of toast: 'success', 'error', 'info', 'warning'
         * @param {number} duration - Duration in ms (default: 3000)
         */
        showToast: function(message, type = 'info', duration = 3000) {
            let container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                document.body.appendChild(container);
            }

            const icons = {
                success: '✓',
                error: '✗',
                info: 'ℹ',
                warning: '⚠',
            };

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <span class="toast-icon">${icons[type] || icons.info}</span>
                <span class="toast-message">${this.escapeHtml(message)}</span>
                <button class="toast-close">×</button>
            `;

            container.appendChild(toast);

            // Close button
            toast.querySelector('.toast-close').addEventListener('click', function() {
                toast.remove();
            });

            // Auto-remove after duration
            if (duration > 0) {
                setTimeout(function() {
                    toast.style.opacity = '0';
                    setTimeout(function() {
                        toast.remove();
                    }, 300);
                }, duration);
            }
        },

        /**
         * Show success toast
         */
        showSuccess: function(message, duration = 3000) {
            this.showToast(message, 'success', duration);
        },

        /**
         * Show error toast
         */
        showError: function(message, duration = 5000) {
            this.showToast(message, 'error', duration);
        },

        /**
         * Show info toast
         */
        showInfo: function(message, duration = 3000) {
            this.showToast(message, 'info', duration);
        },

        /**
         * Show warning toast
         */
        showWarning: function(message, duration = 4000) {
            this.showToast(message, 'warning', duration);
        },

        /**
         * Debounce function - delays execution until after wait milliseconds have elapsed
         * @param {Function} func - Function to debounce
         * @param {number} wait - Wait time in milliseconds
         * @returns {Function} - Debounced function
         */
        debounce: function(func, wait) {
            let timeout;
            return function(...args) {
                const context = this;
                clearTimeout(timeout);
                timeout = setTimeout(function() {
                    func.apply(context, args);
                }, wait);
            };
        },

        /**
         * Throttle function - ensures function is called at most once per wait period
         * @param {Function} func - Function to throttle
         * @param {number} wait - Wait time in milliseconds
         * @returns {Function} - Throttled function
         */
        throttle: function(func, wait) {
            let lastTime = 0;
            return function(...args) {
                const now = Date.now();
                if (now - lastTime >= wait) {
                    lastTime = now;
                    func.apply(this, args);
                }
            };
        },

        /**
         * Format timestamp as readable date
         * @param {string|number|Date} timestamp - Timestamp to format
         * @returns {string} - Formatted date string
         */
        formatDate: function(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;

            // Less than 1 minute
            if (diff < 60000) {
                return 'Just now';
            }

            // Less than 1 hour
            if (diff < 3600000) {
                const minutes = Math.floor(diff / 60000);
                return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
            }

            // Less than 1 day
            if (diff < 86400000) {
                const hours = Math.floor(diff / 3600000);
                return `${hours} hour${hours > 1 ? 's' : ''} ago`;
            }

            // Format as date
            const options = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            };
            return date.toLocaleString('en-US', options);
        },

        /**
         * Format file size in bytes to human readable format
         * @param {number} bytes - File size in bytes
         * @returns {string} - Formatted file size
         */
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        },

        /**
         * Escape HTML special characters
         * @param {string} text - Text to escape
         * @returns {string} - Escaped text
         */
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        /**
         * Truncate text to specified length
         * @param {string} text - Text to truncate
         * @param {number} length - Maximum length
         * @param {string} suffix - Suffix to append (default: '...')
         * @returns {string} - Truncated text
         */
        truncate: function(text, length, suffix = '...') {
            if (!text || text.length <= length) {
                return text || '';
            }
            return text.substring(0, length) + suffix;
        },

        /**
         * Generate unique ID
         * @param {string} prefix - Optional prefix
         * @returns {string} - Unique ID
         */
        generateId: function(prefix = 'id') {
            return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        },

        /**
         * Deep clone an object
         * @param {*} obj - Object to clone
         * @returns {*} - Cloned object
         */
        deepClone: function(obj) {
            return JSON.parse(JSON.stringify(obj));
        },

        /**
         * Check if object is empty
         * @param {Object} obj - Object to check
         * @returns {boolean} - True if empty
         */
        isEmpty: function(obj) {
            if (!obj) return true;
            if (Array.isArray(obj)) return obj.length === 0;
            if (typeof obj === 'object') return Object.keys(obj).length === 0;
            return false;
        },

        /**
         * Get value from nested object using dot notation path
         * @param {Object} obj - Object to search
         * @param {string} path - Dot notation path (e.g., 'user.name')
         * @param {*} defaultValue - Default value if path not found
         * @returns {*} - Value at path or default
         */
        getPath: function(obj, path, defaultValue = undefined) {
            const keys = path.split('.');
            let result = obj;
            for (const key of keys) {
                if (result === null || result === undefined) {
                    return defaultValue;
                }
                result = result[key];
            }
            return result !== undefined ? result : defaultValue;
        },

        /**
         * Set value in nested object using dot notation path
         * @param {Object} obj - Object to modify
         * @param {string} path - Dot notation path
         * @param {*} value - Value to set
         */
        setPath: function(obj, path, value) {
            const keys = path.split('.');
            const lastKey = keys.pop();
            let target = obj;

            for (const key of keys) {
                if (!(key in target)) {
                    target[key] = {};
                }
                target = target[key];
            }

            target[lastKey] = value;
        },

        /**
         * AJAX helper with error handling
         * @param {Object} options - jQuery AJAX options
         * @returns {Promise} - Promise that resolves with response
         */
        ajax: function(options) {
            return new Promise(function(resolve, reject) {
                const defaultOptions = {
                    dataType: 'json',
                    contentType: 'application/json',
                };

                const ajaxOptions = $.extend({}, defaultOptions, options);

                ajaxOptions.success = function(data) {
                    resolve(data);
                };

                ajaxOptions.error = function(xhr, status, error) {
                    let message = 'An error occurred';

                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        message = xhr.responseJSON.error;
                    } else if (xhr.responseText) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            message = response.error || response.message || message;
                        } catch (e) {
                            message = xhr.responseText;
                        }
                    } else if (error) {
                        message = error;
                    }

                    reject({
                        status: xhr.status,
                        message: message,
                        xhr: xhr,
                    });
                };

                $.ajax(ajaxOptions);
            });
        },

        /**
         * Validate session data
         * @param {Object} session - Session object to validate
         * @returns {Object} - Validation result {valid: boolean, errors: string[]}
         */
        validateSession: function(session) {
            const errors = [];

            if (!session.model) {
                errors.push('Model is required');
            }

            if (!session.max_tokens || session.max_tokens < 1 || session.max_tokens > 200000) {
                errors.push('Max tokens must be between 1 and 200000');
            }

            if (session.temperature !== null && session.temperature !== undefined) {
                if (session.temperature < 0 || session.temperature > 1) {
                    errors.push('Temperature must be between 0 and 1');
                }
            }

            // Validate messages array
            if (session.messages && Array.isArray(session.messages)) {
                let prevRole = null;
                session.messages.forEach(function(msg, i) {
                    if (!msg.role || !['user', 'assistant'].includes(msg.role)) {
                        errors.push(`Message ${i}: Invalid role`);
                    }

                    if (prevRole === 'assistant' && msg.role === 'assistant') {
                        errors.push(`Message ${i}: Consecutive assistant messages not allowed`);
                    }

                    prevRole = msg.role;
                });
            }

            return {
                valid: errors.length === 0,
                errors: errors,
            };
        },

        /**
         * Convert markdown to HTML
         * @param {string} markdown - Markdown text
         * @returns {string} - HTML
         */
        markdownToHtml: function(markdown) {
            if (typeof marked !== 'undefined') {
                return marked.parse(markdown);
            }
            // Fallback: just escape HTML
            return this.escapeHtml(markdown).replace(/\n/g, '<br>');
        },

        /**
         * Confirm dialog
         * @param {string} message - Confirmation message
         * @param {Function} callback - Callback function (receives true/false)
         */
        confirm: function(message, callback) {
            if (typeof callback === 'function') {
                const result = window.confirm(message);
                callback(result);
            } else {
                return window.confirm(message);
            }
        },

        /**
         * Prompt dialog
         * @param {string} message - Prompt message
         * @param {string} defaultValue - Default value
         * @param {Function} callback - Callback function (receives value or null)
         */
        prompt: function(message, defaultValue = '', callback) {
            if (typeof callback === 'function') {
                const result = window.prompt(message, defaultValue);
                callback(result);
            } else {
                return window.prompt(message, defaultValue);
            }
        },
    };

    // Export to window
    window.Utils = Utils;

})(window);
