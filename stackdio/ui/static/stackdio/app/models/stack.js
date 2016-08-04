
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
    'utils/utils',
    'models/host',
    'models/blueprint'
], function ($, _, ko, bootbox, moment, utils, Host, Blueprint) {
    'use strict';

    function FakeMoment() {
        this.calendar = function () {
            return '';
        };

        this.toString = function () {
            return '';
        };
    }

    // Define the stack model.
    function Stack(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/stacks/' + raw + '/'
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
        this.createUsers = ko.observable();
        this.activity = ko.observable();
        this.health = ko.observable();
        this.hostCount = ko.observable();
        this.labelClass = ko.observable();
        this.healthLabelClass = ko.observable();

        // Non-editable fields
        this.namespace = ko.observable();
        this.created = ko.observable(new FakeMoment());
        this.labelList = ko.observable();

        // Lazy-loaded properties (not returned from the main stack endpoint)
        this.properties = ko.observable({});
        this.blueprint = ko.observable();
        this.availableActions = ko.observableArray([]);
        this.history = ko.observableArray([]);
        this.hosts = ko.observableArray([]);
        this.volumes = ko.observableArray([]);
        this.commands = ko.observableArray([]);
        this.securityGroups = ko.observableArray([]);
        this.formulaVersions = ko.observableArray([]);
        this.latestLogs = ko.observableArray([]);
        this.historicalLogs = ko.observableArray([]);

        if (needReload) {
            this.waiting = this.reload();
        } else {
            this._process(raw);
        }
    }

    Stack.constructor = Stack;

    Stack.prototype.actionMessages = {
        launch: 'This will create new infrastructure, undoing a "terminate" action you may have ' +
                'previously performed.  This will also re-launch any spot instances that have died.',
        orchestrate: 'This will re-run all of your custom formula components.  ' +
                     'This may overwrite anything you have manually changed on your hosts.',
        'propagate-ssh': 'This will create new users for everyone with "ssh" permission.',
        provision: 'This will re-run core provisioning, in addition to re-running all of your ' +
                   'custom formula components.  This may overwrite anything you have manually ' +
                   'changed on your hosts.',
        pause: '',
        resume: '',
        terminate: 'This will terminate all infrastructure related to this stack.  ' +
                   'You can get it all back by later running the "launch" action on this stack.'
    };

    Stack.prototype._processActivity = function (activity) {
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
                this.labelClass('label-info');
                break;
            case 'dead':
                this.labelClass('label-danger');
                break;
            default:
                this.labelClass('label-default');
        }
    };

    Stack.prototype._processHealth = function (health) {
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
            default:
                this.healthLabelClass('label-default');
        }
    };

    Stack.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.createUsers(raw.create_users);
        this.hostCount(raw.host_count);
        this.namespace(raw.namespace);
        this.created(moment(raw.created));
        this.labelList(raw.label_list);
        this._processActivity(raw.activity);
        this._processHealth(raw.health);
    };

    // Reload the current stack
    Stack.prototype.reload = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: self.raw.url
        }).done(function (stack) {
            self.raw = stack;
            self._process(stack);
        }).fail(function (jqxhr) {
            if (jqxhr.status == 403) {
                window.location.reload(true);
            }
        });
    };

    // Reload the current stack
    Stack.prototype.refreshActivity = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: self.raw.url
        }).done(function (stack) {
            self.raw = stack;
            self._processActivity(stack.activity);
            self._processHealth(stack.health);
        }).fail(function (jqxhr) {
            if (jqxhr.status == 403) {
                window.location.reload(true);
            }
        });
    };

    // Lazy-load the properties
    Stack.prototype.loadProperties = function () {
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

    Stack.prototype.saveProperties = function () {
        $.ajax({
            method: 'PUT',
            url: this.raw.properties,
            data: JSON.stringify(this.properties())
        }).done(function (properties) {
            utils.growlAlert('Successfully saved stack properties!', 'success');
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

    // Lazy-load the hosts
    Stack.prototype.loadHosts = function () {
        var self = this;
        $.ajax({
            method: 'GET',
            url: this.raw.hosts
        }).done(function (hosts) {
            self.hosts(hosts.results.map(function (rawHost) {
                return new Host(rawHost, self.parent);
            }));
        });
    };

    Stack.prototype._addRemove = function(addRem, hostDef, count) {
        var requestObj = {
            action: addRem,
            host_definition: hostDef.id,
            count: count
        };
        var self = this;
        $.ajax({
            method: 'POST',
            url: this.raw.hosts,
            data: JSON.stringify(requestObj)
        }).done(function () {
            // Reload the hosts
            self.loadHosts();
        }).fail(function (jqxhr) {
            var message;
            try {
                var resp = JSON.parse(jqxhr.responseText);
                message = '';
                for (var key in resp) {
                    if (resp.hasOwnProperty(key)) {
                        var betterKey = key.replace('_', ' ');

                        resp[key].forEach(function (errMsg) {
                            message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                        });
                    }
                }
                if (message) {
                    message = '<dl class="dl-horizontal">' + message + '</dl>';
                }
            } catch (e) {
                message = 'Oops... there was a server error.'
            }
            bootbox.alert({
                title: 'Error ' + addRem + 'ing hosts',
                message: message
            });
        });
    };

    Stack.prototype.addHosts = function (hostDefinition, count) {
        this._addRemove('add', hostDefinition, count);
    };

    Stack.prototype.removeHosts = function (hostDefinition, count) {
        this._addRemove('remove', hostDefinition, count);
    };

    Stack.prototype.loadBlueprint = function () {
        var self = this;
        return $.ajax({
            method: 'GET',
            url: this.raw.blueprint
        }).done(function (blueprint) {
            self.blueprint(new Blueprint(blueprint, self.parent));
        });
    };

    // Lazy-load the available actions
    Stack.prototype.loadAvailableActions = function () {
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
    Stack.prototype.performAction = function (action) {
        var self = this;
        var stackTitle = _.escape(self.title());
        var extraMessage = this.actionMessages.hasOwnProperty(action) ? this.actionMessages[action] : '';
        bootbox.confirm({
            title: 'Confirm action for <strong>' + stackTitle + '</strong>',
            message: 'Are you sure you want to perform the "' + action + '" action on ' +
                     '<strong>' + stackTitle + '</strong>?<br>' + extraMessage,
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

    Stack.prototype.loadHistory = function () {
        var self = this;
        if (!this.raw.hasOwnProperty('history')) {
            this.raw.history = this.raw.url + 'history/';
        }
        return $.ajax({
            method: 'GET',
            url: this.raw.history
        }).done(function (history) {
            history.results.forEach(function (entry) {
                entry.timestamp = moment(entry.created);
            });
            self.history(history.results);
        });
    };

    Stack.prototype.loadLogs = function () {
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

    Stack.prototype.runCommand = function (hostTarget, command) {
        var self = this;
        return $.ajax({
            method: 'POST',
            url: this.raw.commands,
            data: JSON.stringify({
                host_target: hostTarget,
                command: command
            })
        }).done(function () {
            try {
                self.parent.reload();
            } catch (e) {}
        }).fail(function (jqxhr) {
            var message;
            try {
                var resp = JSON.parse(jqxhr.responseText);
                message = '';
                for (var key in resp) {
                    if (resp.hasOwnProperty(key)) {
                        var betterKey = key.replace('_', ' ');

                        resp[key].forEach(function (errMsg) {
                            message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                        });
                    }
                }
                if (message) {
                    message = '<dl class="dl-horizontal">' + message + '</dl>';
                }
            } catch (e) {
                message = 'Oops... there was a server error.'
            }
            bootbox.alert({
                title: 'Failed to run command',
                message: message
            })
        });
    };

    Stack.prototype.save = function () {
        var self = this;
        var keys = ['title', 'description', 'create_users', 'namespace'];

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
                title: self.title(),
                description: self.description(),
                create_users: self.createUsers()
            })
        }).done(function (stack) {
            utils.growlAlert('Successfully saved stack!', 'success');
            try {
                self.parent.stackTitle(stack.title);
            } catch (e) {}
        }).fail(function (jqxhr) {
            utils.parseSaveError(jqxhr, 'stack', keys);
        });
    };

    Stack.prototype.delete = function () {
        var self = this;
        var stackTitle = _.escape(self.title());
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + stackTitle + '</strong>',
            message: 'Are you sure you want to delete <strong>' + stackTitle + '</strong>?<br>' +
                     'This will terminate all infrastructure, in addition to ' +
                     'removing all history related to this stack.',
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
                    }).done(function (stack) {
                        self.raw = stack;
                        self._process(stack);
                        if (self.parent && typeof self.parent.reload === 'function') {
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
                            title: 'Error deleting stack',
                            message: message
                        });
                    });
                }
            }
        });
    };

    return Stack;
});