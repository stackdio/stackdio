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
    'generics/pagination',
    'models/formula',
    'models/component',
    'select2'
], function($, ko, Pagination, Formula, Component) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Formulas',
                href: '/formulas/'
            },
            {
                active: true,
                title: window.stackdio.formulaTitle
            }
        ],
        model: Component,
        baseUrl: '/formulas/' + window.stackdio.formulaId + '/',
        initialUrl: '/api/formulas/' + window.stackdio.formulaId + '/components/',
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '30%'},
            {name: 'description', displayName: 'Description', width: '50%'},
            {name: 'slsPath', displayName: 'SLS Path', width: '20%'}
        ],
        autoRefresh: false,
        formula: null,
        init: function () {
            this._super();
            var self = this;

            this.formula = new Formula(window.stackdio.formulaId, this);
            this.formula.waiting.done(function () {
                document.title = 'stackd.io | Formula Detail - ' + self.formula.title();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/formulas/';
            });

            // Create the version selector
            this.versionSelector = $('#formulaVersion');

            this.versionSelector.select2({
                ajax: {
                    url: this.formula.raw.valid_versions,
                    dataType: 'json',
                    delay: 100,
                    data: function (params) {
                        return {
                            version: params.term
                        };
                    },
                    processResults: function (data) {
                        var res = [];
                        data.results.forEach(function (version) {
                            res.push({
                                id: version,
                                version: version,
                                text: version
                            });
                        });

                        return {
                            count: data.count,
                            results: res
                        };
                    },
                    cache: true
                },
                theme: 'bootstrap',
                placeholder: 'Select a version...',
                minimumInputLength: 0
            });

            this.versionSelector.on('select2:select', function(ev) {
                var version = ev.params.data;

                self.currentPage(self.initialUrl + '?version=' + version.version);
                self.shouldReset = false;
                self.reset();
            });

            // React to an open-dropdown event & lazy load the actions
            $('.action-dropdown').on('show.bs.dropdown', function () {
                self.formula.loadAvailableActions();
            });

            function refreshFormula() {
                self.formula.reload();
                self.formula.loadComponents();
            }

            setInterval(refreshFormula, 3000);
        }
    });
});