/*!
  * Copyright 2017,  Digital Reasoning
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
    'ladda',
    'bootbox',
    'utils/formula-versions',
    'models/formula-version',
    'fuelux',
    'select2'
], function ($, ko, Ladda, bootbox, versionUtils, FormulaVersion) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Environments',
                href: '/environments/'
            },
            {
                active: true,
                title: 'New'
            }
        ];

        // View variables
        self.name = ko.observable();
        self.description = ko.observable();
        self.properties = ko.observable({});
        self.formulaVersions = ko.observableArray([]);
        self.formulas = null;
        self.versionsReady = ko.observable();

        self.validProperties = true;
        self.createButton = null;

        self.propertiesJSON = ko.pureComputed({
            read: function () {
                return ko.toJSON(self.properties(), null, 3);
            },
            write: function (value) {
                try {
                    self.properties(JSON.parse(value));
                    self.validProperties = true;
                } catch (err) {
                    self.validProperties = false;
                }
            }
        });

        self.subscription = null;

        // Necessary functions
        self.reset = function() {
            self.name('');
            self.description('');
            self.properties({});
            self.formulaVersions([]);
            self.versionsReady(false);
        };

        self.createSelectors = function () {
            var markForRemoval = [];
            self.formulaVersions().forEach(function (version) {
                if (!versionUtils.createVersionSelector(version, self.formulas)) {
                    // We don't have permission, add it to the removal list
                    markForRemoval.push(version);
                }
            });

            // Get rid of ones we don't have permission to see
            markForRemoval.forEach(function (version) {
                self.formulaVersions.remove(version);
            });

            self.versionsReady(true);
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.getVersionsData = function () {
            return self.formulaVersions().map(function (version) {
                return {
                    formula: version.formula(),
                    version: version.version()
                }
            });
        };

        self.createEnvironment = function() {
            // First remove all the old error messages
            var keys = ['name', 'description', 'properties'];

            self.removeErrors(keys);

            // Check the properties
            if (!self.validProperties) {
                var el = $('#properties');
                el.addClass('has-error');
                el.append('<span class="help-block">Invalid JSON.</span>');
                return;
            }

            // Grab both button objects
            var createButton = Ladda.create(document.querySelector('#create-button'));

            // Start them up
            createButton.start();

            // Create the environment!
            $.ajax({
                'method': 'POST',
                'url': '/api/environments/',
                'data': JSON.stringify({
                    name: self.name(),
                    description: self.description(),
                    properties: self.properties(),
                    formula_versions: self.getVersionsData()
                })
            }).always(function () {
                // Stop our spinning buttons FIRST
                createButton.stop();
            }).done(function () {
                // Successful creation - just redirect to the main environments page
                window.location = '/environments/';
            }).fail(function (jqxhr) {
                // Display any error messages
                var message = '';
                try {
                    var resp = JSON.parse(jqxhr.responseText);
                    for (var key in resp) {
                        if (resp.hasOwnProperty(key)) {
                            if (keys.indexOf(key) >= 0) {
                                var el = $('#' + key);
                                el.addClass('has-error');
                                resp[key].forEach(function (errMsg) {
                                    el.append('<span class="help-block">' + errMsg + '</span>');
                                });
                            } else if (key === 'non_field_errors') {
                                resp[key].forEach(function (errMsg) {
                                    if (errMsg.indexOf('name') >= 0) {
                                        var el = $('#name');
                                        el.addClass('has-error');
                                        el.append('<span class="help-block">A environment with this name already exists.</span>');
                                    }
                                });
                            } else {
                                var betterKey = key.replace('_', ' ');

                                resp[key].forEach(function (errMsg) {
                                    message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                                });
                            }
                        }
                    }
                    if (message) {
                        message = '<dl class="dl-horizontal">' + message + '</dl>';
                    }
                } catch (e) {
                    message = 'Oops... there was a server error.  This has been reported to ' +
                        'your administrators.';
                }
                if (message) {
                    bootbox.alert({
                        title: 'Error creating environment',
                        message: message
                    });
                }
            });
        };

        self.reset();
    };
});
