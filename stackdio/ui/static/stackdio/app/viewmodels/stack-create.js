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
    'ladda',
    'bootbox',
    'select2'
], function ($, ko, Ladda, bootbox) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: true,
                title: 'New'
            }
        ];

        // Create the blueprint selector
        self.blueprintSelector = $('#stackBlueprint');

        self.blueprintSelector.select2({
            ajax: {
                url: '/api/blueprints/',
                dataType: 'json',
                delay: 100,
                data: function (params) {
                    return {
                        title: params.term
                    };
                },
                processResults: function (data) {
                    data.results.forEach(function (blueprint) {
                        blueprint.text = blueprint.title;
                    });
                    return data;
                },
                cache: true
            },
            theme: 'bootstrap',
            placeholder: 'Select a blueprint...',
            templateResult: function (blueprint) {
                return $('<span>' + blueprint.title + '  --  ' + blueprint.description + '</span>');
            },
            minimumInputLength: 0
        });

        self.blueprintSelector.on('select2:select', function(ev) {
            var blueprint = ev.params.data;

            self.createUsers(blueprint.create_users);
            self.blueprintId(blueprint.id);
            var keys = ['blueprint', 'title', 'description',
                'create_users', 'namespace', 'properties'];

            self.removeErrors(keys);

            $.ajax({
                method: 'GET',
                url: blueprint.properties
            }).done(function (properties) {
                self.properties(properties);
            });

            var fullVersionsList = [];

            function getVersions(url) {
                $.ajax({
                    method: 'GET',
                    url: url
                }).done(function (versions) {
                    fullVersionsList.push.apply(fullVersionsList, versions.results.map(function (version) {
                        return {
                            formula: version.formula,
                            version: ko.observable(version.version)
                        }
                    }));
                    if (versions.next === null) {
                        self.formulaVersions(fullVersionsList);
                    } else {
                        getVersions(versions.next);
                    }
                });
            }

            getVersions(blueprint.formula_versions);
        });

        // View variables
        self.blueprintId = ko.observable();
        self.title = ko.observable();
        self.description = ko.observable();
        self.createUsers = ko.observable();
        self.namespace = ko.observable();
        self.properties = ko.observable({});
        self.formulaVersions = ko.observableArray([]);

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
            // Make sure we don't have more than 1 subscription
            if (self.subscription) {
                self.subscription.dispose();
            }

            var $el = $('.checkbox-custom');
            self.subscription = self.createUsers.subscribe(function (newVal) {
                if (newVal) {
                    $el.checkbox('check');
                } else {
                    $el.checkbox('uncheck');
                }
            });

            self.blueprintId(null);
            self.title('');
            self.description('');
            self.createUsers(false);
            self.namespace('');
            self.properties({});
            self.formulaVersions([]);
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.createStack = function() {
            // First remove all the old error messages
            var keys = ['blueprint', 'title', 'description',
                'create_users', 'namespace', 'properties'];

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

            // Create the stack!
            $.ajax({
                'method': 'POST',
                'url': '/api/stacks/',
                'data': JSON.stringify({
                    blueprint: self.blueprintId(),
                    title: self.title(),
                    description: self.description(),
                    create_users: self.createUsers(),
                    namespace: self.namespace(),
                    properties: self.properties(),
                    formulaVersions: ko.toJS(self.formulaVersions())
                })
            }).always(function () {
                // Stop our spinning buttons FIRST
                createButton.stop();
            }).done(function () {
                // Successful creation - just redirect to the main stacks page
                window.location = '/stacks/';
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
                                    if (errMsg.indexOf('title') >= 0) {
                                        var el = $('#title');
                                        el.addClass('has-error');
                                        el.append('<span class="help-block">A stack with this title already exists.</span>');
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
                        title: 'Error creating stack',
                        message: message
                    });
                }
            });
        };

        self.reset();
    };
});
