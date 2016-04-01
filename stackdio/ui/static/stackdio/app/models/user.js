
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
    'moment',
    'bootbox',
    'utils/utils',
    'models/group'
], function ($, ko, moment, bootbox, utils, Group) {
    'use strict';

    function FakeMoment() {
        this.calendar = function () {
            return '';
        };

        this.toString = function () {
            return '';
        };
    }

    // Define the command model.
    function User(raw, parent) {
        var needReload = false;
        if (typeof raw !== 'object' || !raw) {
            needReload = true;
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Editable fields
        this.username = ko.observable();
        this.firstName = ko.observable();
        this.lastName = ko.observable();
        this.email = ko.observable();
        this.ldapEnabled = window.stackdio.ldapEnabled;
        this.lastLogin = ko.observable(new FakeMoment());
        this.superuser = ko.observable();
        this.publicKey = ko.observable();
        this.advanced = ko.observable();

        this.groups = ko.observableArray();

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    User.constructor = User;

    function processTime(time) {
        if (time && time.length) {
            return moment(time);
        } else {
            return new FakeMoment();
        }
    }

    User.prototype._process = function (raw) {
        this.username(raw.username);
        this.firstName(raw.first_name);
        this.lastName(raw.last_name);
        this.email(raw.email);
        this.superuser(raw.superuser);
        this.lastLogin(processTime(raw.last_login));
        if (raw.settings) {
            this.publicKey(raw.settings.public_key);
            this.advanced(raw.settings.advanced_view);
        }
    };

    // Reload the current volume
    User.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: '/api/user/'
        }).done(function (user) {
            self.raw = user;
            self._process(user);
        });
    };

    User.prototype.loadGroups = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.groups
        }).done(function (groups) {
            var groupModels = [];

            groups.results.forEach(function (group) {
                groupModels.push(new Group(group));
            });

            self.groups(groupModels);
        });
    };

    User.prototype.save = function () {
        var self = this;
        var keys = ['username', 'first_name', 'last_name', 'email'];
        var settingsKeys = ['public_key', 'advanced_view'];

        keys.concat(settingsKeys).forEach(function (key) {
            var el = $('#' + key);
            el.removeClass('has-error');
            var help = el.find('.help-block');
            help.remove();
        });

        $.ajax({
            method: 'PUT',
            url: '/api/user/',
            data: JSON.stringify({
                username: self.username(),
                first_name: self.firstName(),
                last_name: self.lastName(),
                email: self.email(),
                superuser: self.superuser(),
                settings: {
                    public_key: self.publicKey(),
                    advanced_view: self.advanced()
                }
            })
        }).done(function (user) {
            utils.growlAlert('Successfully saved user!', 'success');
            if (self.raw.settings.advanced_view !== self.advanced()) {
                window.location.reload(true);
            }
            self._process(user);
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
                        } else if (key === 'settings') {
                            for (var subKey in resp[key]) {
                                if (resp[key].hasOwnProperty(subKey) && settingsKeys.indexOf(subKey) >= 0) {
                                    var subEl = $('#' + subKey);
                                    subEl.addClass('has-error');
                                    resp[key].forEach(function (errMsg) {
                                        subEl.append('<span class="help-block">' + errMsg + '</span>');
                                    });
                                }
                            }
                        } else if (key === 'non_field_errors') {
                            resp[key].forEach(function (errMsg) {
                                if (errMsg.indexOf('username') >= 0) {
                                    var el = $('#username');
                                    el.addClass('has-error');
                                    el.append('<span class="help-block">A user with this username already exists.</span>');
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
                    title: 'Error saving user',
                    message: message
                });
            }
        });
    };

    User.prototype.delete = function () {
        $.ajax({
            method: 'DELETE',
            url: this.raw.url
        })
    };

    return User;
});