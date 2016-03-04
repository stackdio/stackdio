
/*!
  * Copyright 2016,  Digital Reasoning
  *
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  *
  *     http://www.apache.org/licenses/LICENSE-2.0
  *
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  *
*/

define([
    'jquery',
    'knockout',
    'underscore',
    'bootbox',
    'utils/utils'
], function ($, ko, _, bootbox, utils) {
    'use strict';

    // Define the command model.
    function Group(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                name: raw,
                url: '/api/groups/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Editable fields
        this.name = ko.observable();

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Group.constructor = Group;

    Group.prototype._process = function (raw) {
        this.name(raw.name);
    };

    // Reload the current group
    Group.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (group) {
            self.raw = group;
            self._process(group);
        });
    };

    Group.prototype._actionGroup = function (action, user) {
        if (!this.raw.action) {
            this.raw.action = this.raw.url + 'action/';
        }

        var username;

        // Make it work with both models and raw objects
        if (typeof user.username === 'function') {
            username = user.username();
        } else {
            username = user.username;
        }

        var self = this;

        return $.ajax({
            method: 'POST',
            url: this.raw.action,
            data: JSON.stringify({
                action: action,
                user: username
            })
        }).done(function (group) {
            var message = '';
            switch (action) {
                case 'add-user':
                    message = 'Added ' + username + ' to ' + group.name;
                    break;
                case 'remove-user':
                    message = 'Removed ' + username + ' from ' + group.name;
                    break;
                default:
                    break;
            }

            utils.growlAlert(message, 'success');

            if (self.parent.reload) {
                self.parent.reload();
            }
        }).fail(function (jqxhr) {
            console.log(jqxhr);

            var message = 'Error changing membership of group';
            if (message) {
                bootbox.alert({
                    title: 'Error updating group',
                    message: message
                });
            }
        });
    };

    Group.prototype.addUser = function (user) {
        return this._actionGroup('add-user', user);
    };

    Group.prototype.removeUser = function (user) {
        return this._actionGroup('remove-user', user);
    };

    Group.prototype.save = function () {
        var self = this;
        $.ajax({
            method: 'PUT',
            url: this.raw.url,
            data: JSON.stringify({
                name: self.name()
            })
        }).done(function (group) {
            utils.growlAlert('Successfully saved group!', 'success');
        }).fail(function (jqxhr) {
            var message = '';
            try {
                var resp = JSON.parse(jqxhr.responseText);

                for (var key in resp) {
                    if (resp.hasOwnProperty(key)) {
                        if (keys.indexOf(key) >= 0) {
                            var el = $('#' + key);
                            el.addClass('has-error');
                            resp[key].forEach(function (errMsg) {
                                el.append('<span class="help-block">' + errMsg + '</span>');
                            });
                        } else if (key === 'non_field_errors') {
                            resp[key].forEach(function (errMsg) {
                                if (errMsg.indexOf('name') >= 0) {
                                    var el = $('#name');
                                    el.addClass('has-error');
                                    el.append('<span class="help-block">A group with this name already exists.</span>');
                                }
                            });
                        } else {
                            var betterKey = key.replace('_', ' ');

                            resp[key].forEach(function (errMsg) {
                                message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                            });
                        }
                    }
                }
                if (message) {
                    message = '<dl class="dl-horizontal">' + message + '</dl>';
                }
            } catch (e) {
                message = 'Oops... there was a server error.  This has been reported to ' +
                    'your administrators.'
            }
            if (message) {
                bootbox.alert({
                    title: 'Error saving group',
                    message: message
                });
            }
        });
    };

    Group.prototype.delete = function () {
        var self = this;
        var groupName = _.escape(self.name());
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + groupName + '</strong>',
            message: 'Are you sure you want to delete <strong>' + groupName + '</strong>?',
            buttons: {
                confirm: {
                    label: 'Delete',
                    className: 'btn-danger'
                }
            },
            callback: function (result) {
                if (result) {
                    $.ajax({
                        method: 'DELETE',
                        url: self.raw.url
                    }).done(function () {
                        if (window.location.pathname !== '/groups/') {
                            window.location = '/groups/';
                        } else if (self.parent && typeof self.parent.reload === 'function') {
                            self.parent.reload();
                        }
                    }).fail(function (jqxhr) {
                        var message;
                        if (jqxhr.status === 403) {
                            message = 'You are unauthorized to delete this group.'
                        } else {
                            try {
                                var resp = JSON.parse(jqxhr.responseText);
                                message = resp.detail.join('<br>');
                            } catch (e) {
                                message = 'Oops... there was a server error.  This has been reported ' +
                                    'to your administrators.';
                            }
                        }

                        bootbox.alert({
                            title: 'Error deleting group',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Group;
});