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
    'utils/utils',
    'utils/formula-versions',
    'generics/pagination',
    'models/formula-version'
], function ($, ko, bootbox, utils, versionUtils, Pagination, FormulaVersion) {
    'use strict';

    return Pagination.extend({
        objectId: null,
        parentModel: null,
        parentObject: ko.observable(),
        formulas: null,
        autoRefresh: false,
        model: FormulaVersion,
        baseUrl: null,
        initialUrl: null,
        versionsReady: ko.observable(!window.stackdio.hasUpdatePerm),
        sortableFields: [
            {name: 'formula', displayName: 'Formula', width: '60%'},
            {name: 'version', displayName: 'Version', width: '40%'}
        ],
        init: function () {
            this._super();
            this.parentObject(new this.parentModel(this.objectId, this));
        },
        createSelectors: function () {
            var self = this;
            var markForRemoval = [];
            this.objects().forEach(function (version) {
                if (!versionUtils.createVersionSelector(version, self.formulas)) {
                    // We don't have permission, add it to the removal list
                    markForRemoval.push(version);
                }
            });

            // Get rid of ones we don't have permission to see
            markForRemoval.forEach(function (version) {
                self.objects.remove(version);
            });

            this.versionsReady(true);
        },
        extraReloadSteps: function () {
            if (window.stackdio.hasUpdatePerm) {
                if (this.formulas) {
                    this.createSelectors();
                } else {
                    // We don't have the formulas yet, we need to grab them
                    var self = this;
                    versionUtils.getAllFormulas(function (formulas) {
                        self.formulas = formulas;
                        self.createSelectors();
                    });
                }
            }
        },
        saveVersions: function () {
            var ajaxCalls = [];
            var self = this;
            this.objects().forEach(function (version) {
                ajaxCalls.push($.ajax({
                    method: 'POST',
                    url: self.parentObject().raw.formula_versions,
                    data: JSON.stringify({
                        formula: version.formula(),
                        version: version.version()
                    })
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving formula version',
                        'Errors saving version for ' + version.formula() + ':<br>');
                }));
            });

            $.when.apply(this, ajaxCalls).done(function () {
                utils.growlAlert('Successfully saved formula versions.', 'success');
            });
        }
    });
});
