
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
    'underscore',
    'knockout',
    'bootbox',
    'utils/utils',
    'models/component'
], function ($, _, ko, bootbox, utils, Component) {
    'use strict';

    // Define the formula model.
    function Formula(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/formulas/' + raw + '/',
                valid_versions: '/api/formulas/' + raw + '/valid_versions/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Save the id
        this.id = raw.id;

        // Editable fields
        this.title = ko.observable();
        this.description = ko.observable();
        this.uri = ko.observable();
        this.privateGitRepo = ko.observable();
        this.gitUsername = ko.observable();
        this.accessToken = ko.observable();
        this.rootPath = ko.observable();
        this.status = ko.observable();
        this.statusDetail = ko.observable();

        this.labelClass = ko.observable();

        // Lazy-loaded properties (not returned from the main formula endpoint)
        this.properties = ko.observable({});
        this.components = ko.observableArray([]);
        this.validVersions = ko.observableArray([]);
        this.availableActions = ko.observableArray([]);

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Formula.constructor = Formula;

    Formula.prototype.actionMessages = {
        update: 'This will update your formula to the most recent commit on the main branch.'
    };

    Formula.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.uri(raw.uri);
        this.privateGitRepo(raw.private_git_repo);
        this.gitUsername(raw.git_username);
        this.accessToken(raw.access_token);
        this.rootPath(raw.root_path);
        this.status(raw.status);
        this.statusDetail(raw.status_detail);

        // Determine what type of label should be around the status
        switch (raw.status) {
            case 'complete':
                this.labelClass('label-success');
                break;
            case 'importing':
                this.labelClass('label-warning');
                break;
            case 'error':
                this.labelClass('label-danger');
                break;
            default:
                this.labelClass('label-default');
        }
    };

    // Reload the current formula
    Formula.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (formula) {
            self.raw = formula;
            self._process(formula);
        }).fail(function (jqxhr) {
            if (jqxhr.status == 403) {
                window.location.reload(true);
            }
        });
    };

    // Lazy-load the properties
    Formula.prototype.loadProperties = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('properties')) {
            this.raw.properties = this.raw.url + 'properties/';
        }
        return $.ajax({
            method: 'GET',
            url: this.raw.properties
        }).done(function (properties) {
            self.properties(properties);
        });
    };

    Formula.prototype.loadComponents = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('components')) {
            this.raw.components = this.raw.url + 'components/';
        }
        $.ajax({
            method: 'GET',
            url: this.raw.components
        }).done(function (components) {
            self.components(components.results.map(function (rawComp) {
                return new Component(rawComp, self.parent, self);
            }));
        });
    };

    Formula.prototype.loadValidVersions = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('valid_versions')) {
            this.raw.valid_versions = this.raw.url + 'valid_versions/';
        }
        $.ajax({
            method: 'GET',
            url: this.raw.valid_versions
        }).done(function (versions) {
            self.validVersions(versions.results);
        });
    };

    // Lazy-load the available actions
    Formula.prototype.loadAvailableActions = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('action')) {
            this.raw.action = this.url + 'action/';
        }
        $.ajax({
            method: 'GET',
            url: this.raw.action
        }).done(function (resp) {
            self.availableActions(resp.available_actions);
            try {
                // Just do this and fail silently if it doesn't work since all viewmodels don't
                // have an actionMap
                self.parent.actionMap[self.id] = resp.available_actions;
            } catch (e) {}
        });
    };

    // Peform an action
    Formula.prototype.performAction = function (action) {
        var self = this;
        var formulaTitle = _.escape(self.title());
        var extraMessage = this.actionMessages.hasOwnProperty(action) ? this.actionMessages[action] : '';
        bootbox.confirm({
            title: 'Confirm action for <strong>' + formulaTitle + '</strong>',
            message: 'Are you sure you want to perform the "' + action + '" action on ' +
                     '<strong>' + formulaTitle + '</strong>?<br>' + extraMessage,
            buttons: {
                confirm: {
                    label: action.capitalize().replace('_', ' '),
                    className: 'btn-primary'
                }
            },
            callback: function (result) {
                if (result) {
                    var doAction = function(gitPassword) {
                        if (typeof gitPassword === 'undefined') {
                            gitPassword = '';
                        }

                        $.ajax({
                            method: 'POST',
                            url: self.raw.action,
                            data: JSON.stringify({
                                action: action,
                                git_password: gitPassword
                            })
                        }).done(function () {
                            if (self.parent && typeof self.parent.reload === 'function') {
                                self.parent.reload();
                            } else {
                                self.reload();
                            }
                        }).fail(function (jqxhr) {
                            var message;
                            try {
                                var resp = JSON.parse(jqxhr.responseText);
                                message = resp.action.join('<br>');
                            } catch (e) {
                                message = 'Oops... there was a server error.  This has been ' +
                                    'reported to your administrators.';
                            }
                            bootbox.alert({
                                title: 'Error performing the "' + action + '" action',
                                message: message
                            });
                        });
                    };

                    if (self.privateGitRepo() && !self.accessToken()) {
                        bootbox.prompt({
                            title: 'Password for private repo',
                            inputType: 'password',
                            callback: function (result) {
                                if (result) {
                                    doAction(result);
                                }
                            }
                        });
                    } else {
                        doAction();
                    }
                }
            }
        });

    };

    Formula.prototype.save = function () {
        var self = this;
        var keys = ['git_username', 'access_token'];

        keys.forEach(function (key) {
            var el = $('#' + key);
            el.removeClass('has-error');
            var help = el.find('.help-block');
            help.remove();
        });

        $.ajax({
            method: 'PUT',
            url: self.raw.url,
            data: JSON.stringify({
                git_username: self.gitUsername(),
                access_token: self.accessToken()
            })
        }).done(function (formula) {
            utils.growlAlert('Successfully saved formula!', 'success');
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'formula', keys);
        });
    };

    Formula.prototype.delete = function () {
        var self = this;
        var formulaTitle = this.title();
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + formulaTitle + '</strong>',
            message: 'Are you sure you want to delete <strong>' + formulaTitle + '</strong>?',
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
                        if (window.location.pathname !== '/formulas/') {
                            window.location = '/formulas/';
                        } else if (self.parent && typeof self.parent.reload === 'function') {
                            self.parent.reload();
                        }
                    }).fail(function (jqxhr) {
                        var message;
                        try {
                            var resp = JSON.parse(jqxhr.responseText);
                            message = resp.detail.join('<br>');
                            if (Object.keys(resp).indexOf('blueprints') >= 0) {
                                message += '<br><br>Blueprints:<ul><li>' + resp.blueprints.join('</li><li>') + '</li></ul>';
                            }
                        } catch (e) {
                            message = 'Oops... there was a server error.  This has been reported ' +
                                'to your administrators.';
                        }
                        bootbox.alert({
                            title: 'Error deleting formula',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Formula;
});