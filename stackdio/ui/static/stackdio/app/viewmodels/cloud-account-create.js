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
                title: 'Cloud Accounts',
                href: '/accounts/'
            },
            {
                active: true,
                title: 'New'
            }
        ];

        // Create the provider selector
        self.providerSelector = $('#accountProvider');

        self.providerSelector.select2({
            ajax: {
                url: '/api/cloud/providers/',
                dataType: 'json',
                delay: 100,
                data: function (params) {
                    return {
                        name: params.term
                    };
                },
                processResults: function (data) {
                    data.results.forEach(function (provider) {
                        provider.text = provider.name;
                        provider.id = provider.name;
                    });
                    return data;
                },
                cache: true
            },
            theme: 'bootstrap',
            placeholder: 'Select a provider...',
            templateResult: function (provider) {
                if (provider.loading) {
                    return provider.text;
                }
                return provider.name;
            },
            minimumInputLength: 0
        });

        self.providerSelector.on('select2:select', function(ev) {
            var provider = ev.params.data;

            self.provider(provider);
        });

        // View variables
        self.providerId = ko.observable();
        self.title = ko.observable();
        self.description = ko.observable();

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

            self.providerId(null);
            self.title('');
            self.description('');
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.createCloudAccount = function() {
            // First remove all the old error messages
            var keys = ['provider', 'title', 'description',
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

            // Create the account!
            $.ajax({
                'method': 'POST',
                'url': '/api/cloud/accounts/',
                'data': JSON.stringify({
                    provider: self.providerId(),
                    title: self.title(),
                    description: self.description()
                })
            }).always(function () {
                // Stop our spinning buttons FIRST
                createButton.stop();
            }).done(function () {
                // Successful creation - just redirect to the main accounts page
                window.location = '/accounts/';
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
                                        el.append('<span class="help-block">An account with this title already exists.</span>');
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
                        title: 'Error creating account',
                        message: message
                    });
                }
            });
        };

        self.reset();
    };
});
