
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
    'knockout'
], function ($, ko) {
    // Define the stack model.
    function Stack(raw, parent) {
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
        this.namespace = raw.namespace;
        this.blueprint = raw.blueprint;

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

        this._process(raw);
    }

    Stack.constructor = Stack;

    Stack.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.createUsers(raw.create_users);
        this.status(raw.status);
        this.hostCount(raw.host_count);
        this.namespace = raw.namespace;
        this.blueprint = raw.blueprint;

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
        $.ajax({
            method: 'GET',
            url: self.raw.url
        }).done(function (stack) {
            self.raw = stack;
            self._process(stack);
        })
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
            alert('Failure to perform the ' + action + ' action.  Please check the log for the error.');
        });
    };

    Stack.prototype.delete = function () {
        var self = this;
        $.ajax({
            method: 'DELETE',
            url: self.raw.url
        }).done(function (stack) {
            self.raw = stack;
            self._process(stack);
        }).fail(function (jqxhr) {
            console.log(jqxhr);
            alert('Failure to delete the stack.  Please check the log for the error.');
        });
    };

    return Stack;
});