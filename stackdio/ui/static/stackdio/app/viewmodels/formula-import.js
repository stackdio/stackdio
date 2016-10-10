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
    'ladda',
    'bootbox',
    'utils/utils',
    'select2'
], function ($, ko, Ladda, bootbox, utils) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Formulas',
                href: '/formulas/'
            },
            {
                active: true,
                title: 'Import'
            }
        ];

        // Create the version selector
        self.uriSelector = $('#formulaUri');

        self.uriSelector.select2({
            data: [],
            theme: 'bootstrap',
            placeholder: 'Select a formula...',
            disabled: true
        });

        self.uriSelector.on('select2:select', function(ev) {
            var formula = ev.params.data;

            self.uri(formula.clone_url);
        });

        // View variables
        self.uri = ko.observable();
        self.sshPrivateKey = ko.observable();

        self.subscription = null;

        self.loadRepos = function () {
            $.ajax({
                method: 'GET',
                url: 'https://api.github.com/orgs/stackdio-formulas/repos'
            }).done(function (repos) {
                repos.forEach(function (repo) {
                    repo.text = repo.name;
                });

                self.uriSelector.select2({
                    data: repos.sort(function (a, b) {
                        return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
                    }),
                    theme: 'bootstrap',
                    placeholder: 'Select a formula...',
                    disabled: false,
                    minimumInputLength: 0,
                    templateResult: function (repo) {
                        if (repo.loading) {
                            return repo.text;
                        }
                        if (repo.description) {
                            return repo.name + ' (' + repo.description + ')';
                        } else {
                            return repo.name;
                        }
                    }
                });
            }).fail(function () {
                console.warn('Could not load default list of formulas: Github API rate ' +
                    'limit exceeded');

                // Add the tooltip
                var $container = $('.select2-container');
                $container.attr({
                    'data-toggle': 'tooltip',
                    'data-placement': 'top',
                    'title': 'Could not load default list of formulas: Github API rate ' +
                    'limit exceeded'
                });
                $container.tooltip();
            });
        };

        // Necessary functions
        self.reset = function() {
            self.uri('');
            self.sshPrivateKey('');
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.importFormula = function() {
            // First remove all the old error messages
            var keys = ['uri', 'ssh_private_key'];

            self.removeErrors(keys);

            // Grab both button objects
            var importButton = Ladda.create(document.querySelector('#import-button'));

            // Start them up
            importButton.start();

            // Create the formula!
            $.ajax({
                'method': 'POST',
                'url': '/api/formulas/',
                'data': JSON.stringify({
                    uri: self.uri(),
                    ssh_private_key: self.sshPrivateKey()
                })
            }).always(function () {
                // Stop our spinning buttons FIRST
                importButton.stop();
            }).done(function () {
                // Successful creation - just redirect to the main formulas page
                window.location = '/formulas/';
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
                                    if (errMsg.indexOf('uri') >= 0) {
                                        var el = $('#uri');
                                        el.addClass('has-error');
                                        el.append('<span class="help-block">A formula with this URI already exists.</span>');
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
                        title: 'Error importing formula',
                        message: message
                    });
                }
            });
        };

        self.reset();
        self.loadRepos();
    };
});
