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
    'models/formula-version',
    'select2'
], function ($, ko, bootbox, utils, Pagination, FormulaVersion) {
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
            this.objects().forEach(function (version) {
                var validVersionsUrl = null;

                for (var i = 0, length = self.formulas.length; i < length; ++i) {
                    if (self.formulas[i].uri === version.formula()) {
                        validVersionsUrl = self.formulas[i].valid_versions;
                        break;
                    }
                }

                if (!validVersionsUrl) {
                    console.warn('Formula ' + version.formula() + ' not found...');
                    return;
                }

                var $el = $('#' + version.formulaHtmlId());

                var ver = version.version();

                $el.append('<option value="' + ver + '" title="' + ver + '">' + ver + '</option>');

                // Unhide it
                $el.removeClass('hidden-formula-versions');

                $el.select2({
                    ajax: {
                        url: validVersionsUrl,
                        dataType: 'json',
                        delay: 100,
                        data: function (params) {
                            return {
                                title: params.term
                            };
                        },
                        processResults: function (data) {
                            var results = [];
                            data.results.forEach(function (version) {
                                results.push({
                                    id: version,
                                    text: version,
                                    version: version
                                });
                            });
                            return {
                                results: results
                            };
                        },
                        cache: true
                    },
                    theme: 'bootstrap',
                    placeholder: 'Select a version...',
                    templateResult: function (version) {
                        return version.text;
                    },
                    minimumInputLength: 0
                });

                $el.val(ver).trigger('change');

                $el.on('select2:select', function (ev) {
                    var selectedVersion = ev.params.data;
                    version.version(selectedVersion.version);
                });
            });
        },
        extraReloadSteps: function () {
            if (this.formulas) {
                this.createSelectors();
            } else {
                // We don't have the formulas yet, we need to grab them
                var self = this;
                $.ajax({
                    method: 'GET',
                    url: '/api/formulas/'
                }).done(function (formulas) {
                    self.formulas = formulas.results;
                    self.createSelectors();
                });
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
