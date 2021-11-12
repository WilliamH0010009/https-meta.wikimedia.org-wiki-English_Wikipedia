odoo.define('web.NotificationService', function (require) {
'use strict';

var AbstractService = require('web.AbstractService');
var Notification = require('web.Notification');
var core = require('web.core');

var id = 0;

/**
 * Notification Service
 *
 * The Notification Service is simply a service used to display notifications in
 * the top/right part of the screen.
 *
 * If you want to display such a notification, you probably do not want to do it
 * by using this file. The proper way is to use the displayNotification
 * method on the Widget class.
 */
var NotificationService = AbstractService.extend({
    custom_events: {
        close: '_onCloseNotification',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this.notifications = {};
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * It may sometimes be useful to close programmatically a notification. For
     * example, when there is a sticky notification warning the user about some
     * condition (connection lost), but the condition does not apply anymore.
     *
     * @param {number} notificationId
     * @param {boolean} [silent=false] if true, the notification does not call
     *   onClose callback
     * @param {integer} [wait=0] seconds to wait before closing the notification
     */
    close: function (notificationId, silent, wait = 0) {
        var notification = this.notifications[notificationId];
        if (!notification) {
            return;
        }
        if (wait) {
            setTimeout(() => {
                notification.close(silent);
            }, wait);
        } else {
            notification.close(silent);
        }
    },
    /**
     * Display a notification at the appropriate location, and returns the
     * reference id to the same widget.
     *
     * Note that this method does not wait for the appendTo method to complete.
     *
     * @param {Object} params
     * @param {function} [params.Notification] javascript class of a notification
     *   to instantiate by default use 'web.Notification'
     * @param {string} params.title notification title
     * @param {string} params.subtitle notification subtitle
     * @param {string} params.message notification main message
     * @param {string} params.type 'notification' or 'warning'
     * @param {boolean} [params.sticky=false] if true, the notification will stay
     *   visible until the user clicks on it.
     * @param {string} [params.className] className to add on the dom
     * @param {function} [params.onClose] callback when the user click on the x
     *   or when the notification is auto close (no sticky)
     * @param {Object[]} params.buttons
     * @param {function} params.buttons[0].click callback on click
     * @param {Boolean} [params.buttons[0].primary] display the button as primary
     * @param {string} [params.buttons[0].text] button label
     * @param {string} [params.buttons[0].icon] font-awsome className or image src
     * @param {boolean} [params.messageIsHtml=false] allows passing an html
     *  message. Strongly discouraged: other options should be considered before
     *  enabling this option. The responsibility is on the caller to properly
     *  escape the message if this option is enabled.
     * @returns {Number} notification id
     */
    notify: function (params) {
        if (!this.$el) {
            this.$el = $('<div class="o_notification_manager"/>');
            this.$el.prependTo('body');
        }
        var NotificationWidget = params.Notification || Notification;
        var notification = this.notifications[++id] = new NotificationWidget(this, params);
        notification.appendTo(this.$el);
        return id;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onCloseNotification: function (ev) {
        ev.stopPropagation();
        for (var notificationId in this.notifications) {
            if (this.notifications[notificationId] === ev.target) {
                delete this.notifications[notificationId];
                break;
            }
        }
    },
});

core.serviceRegistry.add('notification', NotificationService);

return NotificationService;
});
