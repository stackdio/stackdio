
/*!
  * Copyright 2014,  Digital Reasoning
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
    'bootbox',
    'moment'
], function ($, ko, bootbox, moment) {
    'use strict';

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
        this.status = ko.observable();
        this.hostCount = ko.observable();
        this.labelClass = ko.observable();

        // Non-editable fields
        this.namespace = ko.observable();
        this.blueprint = ko.observable();

        // Lazy-loaded properties (not returned from the main stack endpoint)
        this.properties = ko.observable({});
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
            this.reload();
        } else {
            this._process(raw);
        }
    }

    Stack.constructor = Stack;

    Stack.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.createUsers(raw.create_users);
        this.status(raw.status);
        this.hostCount(raw.host_count);
        this.namespace(raw.namespace);
        this.blueprint(raw.blueprint);

        // Determine what type of label should be around the status
        switch (raw.status) {
            case 'finished':
            case 'ok':
                this.labelClass('label-success');
                break;
            case 'launching':
            case 'configuring':
            case 'syncing':
            case 'provisioning':
            case 'orchestrating':
            case 'finalizing':
            case 'destroying':
            case 'starting':
            case 'stopping':
            case 'executing_action':
            case 'terminating':
                this.labelClass('label-warning');
                break;
            case 'pending':
                this.labelClass('label-info');
                break;
            case 'error':
                this.labelClass('label-danger');
                break;
            default:
                this.labelClass('label-default');
        }
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
        });
    };

    // Lazy-load the properties
    Stack.prototype.loadProperties = function () {
        var self = this;
        $.ajax({
            method: 'GET',
            url: self.raw.properties
        }).done(function (properties) {
            self.properties(properties);
        });
    };

    // Lazy-load the available actions
    Stack.prototype.loadAvailableActions = function () {
        var self = this;
        $.ajax({
            method: 'GET',
            url: self.raw.action
        }).done(function (resp) {
            self.availableActions(resp.available_actions);

            if (self.parent.hasOwnProperty('actionMap')) {
                self.parent.actionMap[self.id] = resp.available_actions;
            }
        });
    };

    // Peform an action
    Stack.prototype.performAction = function (action) {
        var self = this;
        $.ajax({
            method: 'POST',
            url: self.raw.action,
            data: JSON.stringify({
                action: action
            })
        }).done(function () {
            self.reload();
        }).fail(function (jqxhr) {
            console.log(jqxhr);
            alert('Failed to perform the "' + action + '" action.  Please check the log for the error.');
        });
    };

    Stack.prototype.loadHistory = function () {
        var self = this;
        $.ajax({
            method: 'GET',
            url: self.raw.url + 'history/'
        }).done(function (history) {
            history.results.forEach(function (entry) {
                entry.timestamp = moment(entry.created);
                switch (entry.level) {
                    case 'ERROR':
                        entry.itemClass = 'list-group-item-danger';
                        break;
                    default:
                        entry.itemClass = '';
                }
                if (entry.status === 'finished') {
                    entry.itemClass = 'list-group-item-success';
                }
            });
            self.history(history.results);
        }).fail(function (jqxhr) {
            console.log(jqxhr);
        });
    };

    Stack.prototype.save = function () {
        var self = this;
        $.ajax({
            method: 'PUT',
            url: self.raw.url,
            data: JSON.stringify({
                title: self.title(),
                description: self.description(),
                create_users: self.createUsers()
            })
        }).done(function (stack) {
            // Not sure?
        }).fail(function (jqxhr) {
            console.log(jqxhr);
            alert('Failed to save the stack.  Please check the log for the error.');
        });
    };

    Stack.prototype.delete = function () {
        var self = this;
        var stackTitle =
        bootbox.confirm({
            title: 'Confirm delete of <strong>' + self.title() + '</strong>',
            message: 'Are you sure you want to delete <strong>' + self.title() + '</strong>?  ' +
                     'This will terminate all infrastructure, in addition to ' +
                     'removing all history related to this stack.',
            callback: function (result) {
                if (result) {
                    $.ajax({
                        method: 'DELETE',
                        url: self.raw.url
                    }).done(function (stack) {
                        self.raw = stack;
                        self._process(stack);
                    }).fail(function (jqxhr) {
                        console.log(jqxhr);
                        alert('Failed to delete the stack.  Please check the log for the error.');
                    });
                }
            }
        });
    };

    return Stack;
});