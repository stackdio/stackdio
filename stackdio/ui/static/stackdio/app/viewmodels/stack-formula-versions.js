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
    'utils/utils',
    'generics/pagination',
    'models/stack',
    'models/formula-version'
], function ($, ko, bootbox, utils, Pagination, Stack, FormulaVersion) {
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
                title: 'Stack Detail',
                href: '/stacks/' + window.stackdio.stackId + '/'
            },
            {
                active: true,
                title: 'Stack Formula Versions'
            }
        ],
        stack: ko.observable(),
        newVersions: ko.observableArray([]),
        newVersionFormula: ko.observable(),
        autoRefresh: false,
        model: FormulaVersion,
        baseUrl: '/stacks/',
        initialUrl: '/api/stacks/' + window.stackdio.stackId + '/formula_versions/',
        sortableFields: [
            {name: 'formula', displayName: 'Formula', width: '60%'},
            {name: 'version', displayName: 'Version', width: '40%'}
        ],
        init: function () {
            this._super();
            this.newVersionFormula(null);
            this.stack(new Stack(window.stackdio.stackId, this));
        },
        addNewVersion: function () {
            var $el = $('#new-version-form');

            $el.removeClass('has-error');

            var self = this;
            var dup = false;
            this.sortedObjects().forEach(function (version) {
                if (version.formula() === self.newVersionFormula()) {
                    dup = true;
                }
            });

            this.newVersions().forEach(function (version) {
                if (version.formula === self.newVersionFormula()) {
                    dup = true;
                }
            });

            if (dup) {
                utils.growlAlert('You may not have two versions with the same formula.', 'danger');
                $el.addClass('has-error');
                return;
            }

            this.newVersions.push({
                formula: this.newVersionFormula(),
                version: ko.observable(null)
            });
            this.newVersionFormula(null);
        },
        saveVersions: function () {
            var ajaxCalls = [];
            var self = this;
            this.objects().forEach(function (version) {
                ajaxCalls.push($.ajax({
                    method: 'POST',
                    url: self.stack().raw.formula_versions,
                    data: JSON.stringify({
                        formula: version.formula(),
                        version: version.version()
                    })
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving formula version',
                        'Errors saving version for ' + version.formula() + ':<br>');
                }));
            });

            this.newVersions().forEach(function (version) {
                ajaxCalls.push($.ajax({
                    method: 'POST',
                    url: self.stack().raw.formula_versions,
                    data: JSON.stringify({
                        formula: version.formula,
                        version: version.version()
                    })
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving formula version',
                        'Errors saving version for ' + version.formula + ':<br>');
                }));
            });

            $.when.apply(this, ajaxCalls).done(function () {
                utils.growlAlert('Successfully saved formula versions.', 'success');
            });

        }
    });
});