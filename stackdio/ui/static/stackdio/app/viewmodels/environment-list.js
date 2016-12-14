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
    'models/environment'
], function ($, Pagination, Environment) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Environments'
            }
        ],
        model: Environment,
        baseUrl: '/environments/',
        initialUrl: '/api/environments/',
        detailRequiresAdvanced: true,
        sortableFields: [
            {name: 'name', displayName: 'Name', width: '20%'},
            {name: 'description', displayName: 'Description', width: '35%'},
            {name: 'labelList', displayName: 'Labels', width: '15%'},
            {name: 'activity', displayName: 'Activity', width: '10%'},
            {name: 'health', displayName: 'Health', width: '10%'}
        ],
        openActionEnvironmentId: null,
        actionMap: {},
        reset: function() {
            this.openActionEnvironmentId = null;
            this.actionMap = {};
            this._super();
        },
        processObject: function (environment) {
            if (this.actionMap.hasOwnProperty(environment.id)) {
                environment.availableActions(this.actionMap[environment.id]);
            }
        },
        extraReloadSteps: function () {
            // Add the dropdown events.  This must happen AFTER we set the environments observable
            // in the previous statement.
            var actionElement = $('.action-dropdown');

            var self = this;
            // React to an open-dropdown event
            actionElement.on('show.bs.dropdown', function (evt) {
                // Grab the ID of the open element
                var id = evt.target.id;

                // Set the ID of the currently open action dropdown
                self.openActionEnvironmentId = id;

                // Freeze a copy of the current environments
                var environments = self.objects();

                // Find the current environment with the correct ID, and load the actions
                for (var i = 0, length = environments.length; i < length; ++i) {
                    if (environments[i].id === id) {
                        environments[i].loadAvailableActions();
                        break;
                    }
                }
            });

            // React to a close dropdown event (this one is pretty simple)
            actionElement.on('hide.bs.dropdown', function () {
                // Make sure that we know nothing is open
                self.openActionEnvironmentId = null;
            });
        }
    });
});
