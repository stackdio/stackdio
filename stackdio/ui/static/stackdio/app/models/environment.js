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
    'moment',
    'utils/utils'
], function ($, _, ko, bootbox, moment, utils) {
    'use strict';

    // Define the environment model.
    function Environment(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                name: raw,
                url: '/api/environments/' + raw + '/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        // Save the id
        this.id = raw.name;
        this.detailUrl = '/environments/' + this.id + '/';

        // Editable fields
        this.name = ko.observable();
        this.description = ko.observable();
        this.orchestrateSlsPath = ko.observable();
        this.labelList = ko.observable();
        this.createUsers = ko.observable();
        this.activity = ko.observable();
        this.health = ko.observable();
        this.labelClass = ko.observable();
        this.healthLabelClass = ko.observable();

        // Lazy-loaded properties (not returned from the main environment endpoint)
        this.properties = ko.observable({});
        this.components = ko.observableArray([]);
        this.availableActions = ko.observableArray([]);
        this.formulaVersions = ko.observableArray([]);
        this.latestLogs = ko.observableArray([]);
        this.historicalLogs = ko.observableArray([]);

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Environment.constructor = Environment;

    Environment.prototype.actionMessages = {
        orchestrate: 'This will re-run all of your custom formula components.  ' +
                     'This may overwrite anything you have manually changed on your hosts.',
        'propagate-ssh': 'This will create new users for everyone with "ssh" permission.',
        provision: 'This will re-run core provisioning, in addition to re-running all of your ' +
                   'custom formula components.  This may overwrite anything you have manually ' +
                   'changed on your hosts.',
    };

    Environment.prototype._processActivity = function (activity) {
        this.activity(activity);
        // Determine what type of label should be around the activity
        switch (activity) {
            case 'idle':
                this.labelClass('label-success');
                break;
            case 'launching':
            case 'provisioning':
            case 'orchestrating':
            case 'resuming':
            case 'pausing':
            case 'executing':
            case 'terminating':
                this.labelClass('label-warning');
                break;
            case 'queued':
            case 'paused':
            case 'terminated':
                this.labelClass('label-info');
                break;
            case 'dead':
                this.labelClass('label-danger');
                break;
            case 'unknown':
            default:
                this.labelClass('label-default');
        }
    };

    Environment.prototype._processHealth = function (health) {
        this.health(health);
        // Determine what type of label should be around the health
        switch (health) {
            case 'healthy':
                this.healthLabelClass('label-success');
                break;
            case 'unstable':
                this.healthLabelClass('label-warning');
                break;
            case 'unhealthy':
                this.healthLabelClass('label-danger');
                break;
            case 'unknown':
            default:
                this.healthLabelClass('label-default');
        }
    };

    Environment.prototype._process = function (raw) {
        this.name(raw.name);
        this.description(raw.description);
        this.labelList(raw.label_list);
        this.createUsers(raw.create_users);
        this.orchestrateSlsPath(raw.orchestrate_sls_path);
        this._processActivity(raw.activity);
        this._processHealth(raw.health);
    };

    // Reload the current environment
    Environment.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.url
        }).done(function (environment) {
            self.raw = environment;
            self._process(environment);
        });
    };

    // Lazy-load the properties
    Environment.prototype.loadProperties = function () {
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

    Environment.prototype.saveProperties = function () {
        $.ajax({
            method: 'PUT',
            url: this.raw.properties,
            data: JSON.stringify(this.properties())
        }).done(function (properties) {
            utils.growlAlert('Successfully saved environment properties!', 'success');
        }).fail(function (jqxhr) {
            var message;
            try {
                var resp = JSON.parse(jqxhr.responseText);
                message = resp.properties.join('<br>');
            } catch (e) {
                message = 'Oops... there was a server error.'
            }
            message += '  Your properties were not saved.';
            utils.growlAlert(message, 'danger');
        });
    };

    Environment.prototype.save = function () {
        var self = this;
        var keys = ['name', 'description', 'create_users', 'orchestrate_sls_path'];

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
                name: self.name(),
                description: self.description(),
                create_users: self.createUsers(),
                orchestrate_sls_path: self.orchestrateSlsPath()
            })
        }).done(function (environment) {
            utils.growlAlert('Successfully saved environment!', 'success');
            try {
                self.parent.environmentName(environment.name);
            } catch (e) {}
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'environment', keys);
        });
    };

    Environment.prototype.delete = function () {
        var self = this;
        var environmentName = this.name();
        bootbox.confirm({
            name: 'Confirm delete of <strong>' + environmentName + '</strong>',
            message: 'Are you sure you want to delete <strong>' + environmentName + '</strong>?',
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
                        if (window.location.pathname !== '/environments/') {
                            window.location = '/environments/';
                        } else if (self.parent && typeof self.parent.reload === 'function') {
                            self.parent.reload();
                        }
                    }).fail(function (jqxhr) {
                        var message;
                        try {
                            var resp = JSON.parse(jqxhr.responseText);
                            message = resp.detail.join('<br>');
                        } catch (e) {
                            message = 'Oops... there was a server error.  This has been reported ' +
                                'to your administrators.';
                        }
                        bootbox.alert({
                            name: 'Error deleting environment',
                            message: message
                        });
                    });
                }
            }
        });
    };

    // Reload the current environment
    Environment.prototype.refreshActivity = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: self.raw.url
        }).done(function (environment) {
            self.raw = environment;
            self._processActivity(environment.activity);
            self._processHealth(environment.health);
        }).fail(function (jqxhr) {
            if (jqxhr.status == 403) {
                window.location.reload(true);
            }
        });
    };

    // Lazy-load the available actions
    Environment.prototype.loadAvailableActions = function () {
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

    Environment.prototype.runSingleSls = function (component, hostTarget) {
        var self = this;
        var environmentName = _.escape(self.name());
        bootbox.confirm({
            title: 'Confirm component run for <strong>' + environmentName + '</strong>',
            message: 'Are you sure you want to run ' + component + ' on ' + environmentName + '?',
            buttons: {
                confirm: {
                    label: 'Run',
                    className: 'btn-primary'
                }
            },
            callback: function (result) {
                if (!result) {
                    return;
                }

                var arg = {
                    component: component
                };

                if (hostTarget) {
                    arg.host_target = hostTarget;
                }

                $.ajax({
                    method: 'POST',
                    url: self.raw.action,
                    data: JSON.stringify({
                        action: 'single-sls',
                        args: [arg]
                    })
                }).done(function () {
                    if (self.parent && typeof self.parent.reload === 'function') {
                        self.parent.reload();
                    }
                    utils.growlAlert('Triggered ' + component + '.', 'success');
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
                        title: 'Error running component',
                        message: message
                    });
                });
            }
        });
    };

    // Peform an action
    Environment.prototype.performAction = function (action) {
        var self = this;
        var environmentName = _.escape(self.name());
        var extraMessage = this.actionMessages.hasOwnProperty(action) ? this.actionMessages[action] : '';
        bootbox.confirm({
            title: 'Confirm action for <strong>' + environmentName + '</strong>',
            message: 'Are you sure you want to perform the "' + action + '" action on ' +
                     '<strong>' + environmentName + '</strong>?<br>' + extraMessage,
            buttons: {
                confirm: {
                    label: action.capitalize().replace('_', ' '),
                    className: 'btn-primary'
                }
            },
            callback: function (result) {
                if (result) {
                    $.ajax({
                        method: 'POST',
                        url: self.raw.action,
                        data: JSON.stringify({
                            action: action
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
                }
            }
        });

    };

    Environment.prototype._processStatus = function (obj) {
        switch (obj.status)
        {
            case 'queued':
                obj.statusPanel = 'panel-info';
                obj.statusLabel = 'label-info';
                break;

            case 'running':
                obj.statusPanel = 'panel-warning';
                obj.statusLabel = 'label-warning';
                break;

            case 'succeeded':
                obj.statusPanel = 'panel-success';
                obj.statusLabel = 'label-success';
                break;

            case 'failed':
                obj.statusPanel = 'panel-danger';
                obj.statusLabel = 'label-danger';
                break;

            case 'cancelled':
            case 'unknown':
            default:
                obj.statusPanel = 'panel-default';
                obj.statusLabel = 'label-default';
        }
    };

    Environment.prototype._processHostHealth = function (obj) {
        switch (obj.health)
        {
            case 'healthy':
                obj.healthPanel = 'panel-success';
                obj.healthLabel = 'label-success';
                break;

            case 'unstable':
                obj.healthPanel = 'panel-warning';
                obj.healthLabel = 'label-warning';
                break;

            case 'unhealthy':
                obj.healthPanel = 'panel-danger';
                obj.healthLabel = 'label-danger';
                break;

            case 'unknown':
            default:
                obj.healthPanel = 'panel-default';
                obj.healthLabel = 'label-default';
        }
    };

    Environment.prototype.loadComponents = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('components')) {
            this.raw.components = this.raw.url + 'components/';
        }
        return $.ajax({
            method: 'GET',
            url: this.raw.components
        }).done(function (components) {
            components.results.forEach(function (component) {
                component.htmlId = component.sls_path.replace(/\./g, '-');
                component.hosts.forEach(function (host) {
                    host.timestamp = moment(host.timestamp);
                    self._processStatus(host);
                    self._processHostHealth(host);
                });
                self._processStatus(component);
                self._processHostHealth(component);
            });
            self.components(components.results);
        });
    };

    Environment.prototype.loadLogs = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('logs')) {
            this.raw.logs = this.raw.url + 'logs/';
        }
        $.ajax({
            method: 'GET',
            url: this.raw.logs
        }).done(function (logs) {
            var latestLogs = [];
            for (var log in logs.latest) {
                if (logs.latest.hasOwnProperty(log)) {
                    latestLogs.push({
                        text: log,
                        type: 'item',
                        url: logs.latest[log]
                    });
                }
            }
            self.latestLogs(latestLogs);

            var historicalLogs = [];

            logs.historical.forEach(function (log) {
                var spl = log.split('/');
                historicalLogs.push({
                    text: spl[spl.length-1],
                    type: 'item',
                    url: log
                })
            });

            self.historicalLogs(historicalLogs);
        });
    };

    return Environment;
});