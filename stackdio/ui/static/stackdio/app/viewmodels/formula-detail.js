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
    'generics/pagination',
    'models/formula',
    'models/component'
], function($, ko, Pagination, Formula, Component) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [],
        model: Component,
        baseUrl: '/formulas/' + window.stackdio.formulaId + '/',
        initialUrl: '/api/formulas/' + window.stackdio.formulaId + '/components/',
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '30%'},
            {name: 'description', displayName: 'Description', width: '50%'},
            {name: 'slsPath', displayName: 'SLS Path', width: '20%'}
        ],
        formula: null,
        formulaTitle: ko.observable(''),
        formulaUrl: ko.observable(''),
        init: function () {
            this._super();
            var self = this;
            this.breadcrumbs = [
                {
                    active: false,
                    title: 'Formulas',
                    href: '/formulas/'
                },
                ko.observable({
                    active: true,
                    title: ko.computed(function() {
                        return self.formulaTitle()
                    })
                })
            ];

            this.formula = new Formula(window.stackdio.formulaId, this);
            this.formula.waiting.done(function () {
                document.title = 'stackd.io | Formula Detail - ' + self.formula.title();
                self.formulaTitle(self.formula.title());
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/formulas/';
            });
        }
    });
});