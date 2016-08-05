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
    'generics/pagination',
    'models/stack'
], function ($, Pagination, Stack) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Stacks'
            }
        ],
        model: Stack,
        baseUrl: '/stacks/',
        initialUrl: '/api/stacks/',
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '14%'},
            {name: 'description', displayName: 'Description', width: '18%'},
            {name: 'namespace', displayName: 'Namespace', width: '10%'},
            {name: 'created', displayName: 'Launched', width: '15%'},
            {name: 'hostCount', displayName: 'Hosts', width: '8%'},
            {name: 'activity', displayName: 'Activity', width: '10%'},
            {name: 'health', displayName: 'Health', width: '10%'}
        ],
        openActionStackId: null,
        actionMap: {},
        reset: function() {
            this.openActionStackId = null;
            this.actionMap = {};
            this._super();
        },
        processObject: function (stack) {
            if (this.actionMap.hasOwnProperty(stack.id)) {
                stack.availableActions(this.actionMap[stack.id]);
            }
        },
        extraReloadSteps: function () {
            // Add the dropdown events.  This must happen AFTER we set the stacks observable
            // in the previous statement.
            var actionElement = $('.action-dropdown');

            var self = this;
            // React to an open-dropdown event
            actionElement.on('show.bs.dropdown', function (evt) {
                // Grab the ID of the open element
                var id = parseInt(evt.target.id);

                // Set the ID of the currently open action dropdown
                self.openActionStackId = id;

                // Freeze a copy of the current stacks
                var stacks = self.objects();

                // Find the current stack with the correct ID, and load the actions
                for (var i = 0, length = stacks.length; i < length; ++i) {
                    if (stacks[i].id === id) {
                        stacks[i].loadAvailableActions();
                        break;
                    }
                }
            });

            // React to a close dropdown event (this one is pretty simple)
            actionElement.on('hide.bs.dropdown', function () {
                // Make sure that we know nothing is open
                self.openActionStackId = null;
            });
        }
    });
});
