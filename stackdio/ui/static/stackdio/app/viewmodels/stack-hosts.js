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
    'bootbox',
    'generics/pagination',
    'models/stack',
    'models/host'
], function ($, ko, bootbox, Pagination, Stack, Host) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: false,
                title: window.stackdio.stackTitle,
                href: '/stacks/' + window.stackdio.stackId + '/'
            },
            {
                active: true,
                title: 'Hosts'
            }
        ],
        stack: ko.observable(),
        autoRefresh: true,
        model: Host,
        baseUrl: '/stacks/',
        initialUrl: '/api/stacks/' + window.stackdio.stackId + '/hosts/',
        sortableFields: [
            {name: 'hostDefinition', displayName: 'Host Type', width: '15%'},
            {name: 'hostname', displayName: 'Hostname', width: '15%'},
            {name: 'fqdn', displayName: 'FQDN', width: '30%'},
            {name: 'privateDNS', displayName: 'Private DNS', width: '15%'},
            {name: 'publicDNS', displayName: 'Public DNS', width: '15%'},
            {name: 'activity', displayName: 'Activity', width: '10%'}
        ],
        selectedHostDef: ko.observable(null),
        selectedAction: ko.observable(null),
        actionCount: ko.observable(1),
        actions: [
            'add',
            'remove'
        ],
        init: function () {
            this._super();
            this.stack(new Stack(window.stackdio.stackId, this));
            var self = this;
            // Load the blueprint & formula components
            this.stack().waiting.done(function () {
                self.stack().loadBlueprint().done(function () {
                    self.stack().blueprint().loadHostDefinitions();
                });
            });

            this.hostDefinitions = ko.computed(function () {
                if (!self.stack().blueprint()) {
                    return [];
                }
                return self.stack().blueprint().hostDefinitions();
            });
        },
        addRemoveHosts: function () {
            var callback, title, message, count;
            var error = false;
            try {
                count = parseInt(this.actionCount());
            } catch (e) {
                error = true;
            }
            if (count < 1) {
                error = true;
            }
            if (error) {
                bootbox.alert({
                    title: 'Error adding or removing hosts',
                    message: 'The count of hosts must be a positive non-zero integer.'
                });
                return;
            }
            var hostDef = this.selectedHostDef();
            var s = count === 1 ? '' : 's';
            switch (this.selectedAction()) {
                case 'add':
                    callback = this.stack().addHosts;
                    title = 'Add ' + count + ' host' + s + ' to stack';
                    message = 'Are you sure you want to add ' + count +
                        ' <strong>' + hostDef.title() + '</strong> host' + s + ' to ' +
                        '<strong>' + this.stack().title() + '</strong>?';
                    break;
                case 'remove':
                    callback = this.stack().removeHosts;
                    title = 'Remove ' + count + ' host' + s + ' from stack';
                    message = 'Are you sure you want to remove ' + count +
                        ' <strong>' + hostDef.title() + '</strong> host' + s + ' from ' +
                        '<strong>' + this.stack().title() + '</strong>?';
                    break;
                default:
                    // Bad, this should never happen
            }
            var self = this;
            bootbox.confirm({
                title: title,
                message: message,
                callback: function (result) {
                    if (result) {
                        callback.call(self.stack(), hostDef, count);
                    }
                }
            });
        }
    });
});
