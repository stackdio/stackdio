
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
    'select2'
], function($) {
    'use strict';
    return {
        getAllFormulas: function (callback) {
            // Grab the formulas
            var fullFormulasList = [];

            function getFormulas(url) {
                $.ajax({
                    method: 'GET',
                    url: url
                }).done(function (formulas) {
                    fullFormulasList.push.apply(fullFormulasList, formulas.results);
                    if (formulas.next === null) {
                        callback(fullFormulasList);
                    } else {
                        getFormulas(formulas.next);
                    }
                });
            }

            getFormulas('/api/formulas/');
        },
        createVersionSelector: function (version, formulaList) {
            var validVersionsUrl = null;

            for (var i = 0, length = formulaList.length; i < length; ++i) {
                if (formulaList[i].uri === version.formula()) {
                    validVersionsUrl = formulaList[i].valid_versions;
                    break;
                }
            }

            if (!validVersionsUrl) {
                // The user probably doesn't have permission to view this formula
                return false;
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

            return true;
        }
    };
});