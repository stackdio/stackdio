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
    'models/formula'
], function ($, Pagination, Formula) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Formulas'
            }
        ],
        model: Formula,
        baseUrl: '/formulas/',
        initialUrl: '/api/formulas/',
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '25%'},
            {name: 'uri', displayName: 'Repo URL', width: '50%'},
            {name: 'status', displayName: 'Status', width: '10%'},
            {name: 'privateGitRepo', displayName: 'Private', width: '5%'}
        ],
        openActionFormulaId: null,
        actionMap: {},
        reset: function() {
            this.openActionFormulaId = null;
            this.actionMap = {};
            this._super();
        },
        processObject: function (formula) {
            if (this.actionMap.hasOwnProperty(formula.id)) {
                formula.availableActions(this.actionMap[formula.id]);
            }
        },
        extraReloadSteps: function () {
            // Add the dropdown events.  This must happen AFTER we set the formula observable
            // in the previous statement.
            var actionElement = $('.action-dropdown');

            var self = this;
            // React to an open-dropdown event
            actionElement.on('show.bs.dropdown', function (evt) {
                // Grab the ID of the open element
                var id = parseInt(evt.target.id);

                // Set the ID of the currently open action dropdown
                self.openActionFormulaId = id;

                // Freeze a copy of the current formulas
                var formulas = self.objects();

                // Find the current formula with the correct ID, and load the actions
                for (var i = 0, length = formulas.length; i < length; ++i) {
                    if (formulas[i].id === id) {
                        formulas[i].loadAvailableActions();
                        break;
                    }
                }
            });

            // React to a close dropdown event (this one is pretty simple)
            actionElement.on('hide.bs.dropdown', function () {
                // Make sure that we know nothing is open
                self.openActionFormulaId = null;
            });
        }
    });
});
