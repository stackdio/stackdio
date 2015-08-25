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
    'bloodhound',
    'ladda',
    'bootbox',
    'typeahead'
], function ($, ko, Bloodhound, Ladda, bootbox) {
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

        // Create the blueprint typeahead
        self.blueprints = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.whitespace,
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            remote: {
                url: '/api/blueprints/?title=%QUERY',
                wildcard: '%QUERY',
                transform: function (resp) { return resp.results; }
            }
        });

        self.blueprintTypeahead = $('#blueprints').find('.typeahead');

        self.blueprintTypeahead.typeahead({
            highlight: true
        }, {
            name: 'blueprints',
            display: 'title',
            source: self.blueprints
        });

        self.blueprintTypeahead.bind('typeahead:select', function(ev, blueprint) {
            self.createUsers(blueprint.create_users);
            self.blueprintId(blueprint.id);
            $.ajax({
                method: 'GET',
                url: blueprint.properties
            }).done(function (properties) {
                self.properties(properties);
            })
        });

        // View variables
        self.blueprintId = ko.observable();
        self.title = ko.observable();
        self.description = ko.observable();
        self.createUsers = ko.observable();
        self.namespace = ko.observable();
        self.properties = ko.observable({});

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


        // Necessary functions
        self.reset = function() {
            self.blueprintId(null);
            self.title('');
            self.description('');
            self.createUsers(false);
            self.namespace('');
            self.properties({});

        };

        self.createStack = function() {
            // First remove all the old error messages
            var keys = ['blueprint', 'title', 'description',
                'create_users', 'namespace', 'properties'];

            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });

            // Check the properties
            if (!self.validProperties) {
                var el = $('#properties');
                el.addClass('has-error');
                el.append('<span class="help-block">Invalid JSON.</span>');
                return;
            }

            // Grab both button objects
            var createButton = Ladda.create(document.querySelector('#create-button'));
            var createButtonSm = Ladda.create(document.querySelector('#create-button-sm'));

            // Start them up
            createButton.start();
            createButtonSm.start();

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
                    properties: self.properties()
                })
            }).always(function () {
                // Stop our spinning buttons FIRST
                createButton.stop();
                createButtonSm.stop();
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
                                resp[key].forEach(function (errMsg) {
                                    message += key + ': ' + errMsg + '<br>';
                                });
                            }
                        }
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
