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
    'bootbox'
], function ($, ko, Ladda, bootbox) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Users',
                href: '/users/'
            },
            {
                active: true,
                title: 'New'
            }
        ];

        // View variables
        self.username = ko.observable();
        self.firstName = ko.observable();
        self.lastName = ko.observable();
        self.email = ko.observable();

        // Necessary functions
        self.reset = function() {
            self.username('');
            self.firstName('');
            self.lastName('');
            self.email('');
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.createUser = function() {
            var username = self.username();

            bootbox.confirm({
                title: 'Confirm user creation',
                message: 'Are you sure you want to create <strong>' + username + '</strong>?<br>' +
                    'An email <strong>will</strong> be sent to the provided email address.',
                buttons: {
                    confirm: {
                        label: 'Create',
                        className: 'btn-primary'
                    }
                },
                callback: function (result) {
                    if (result) {
                        // First remove all the old error messages
                        var keys = ['username', 'first_name', 'last_name', 'email'];

                        self.removeErrors(keys);

                        // Grab both button objects
                        var createButton = Ladda.create(document.querySelector('#create-button'));

                        // Start them up
                        createButton.start();

                        // Create the user!
                        $.ajax({
                            'method': 'POST',
                            'url': '/api/users/',
                            'data': JSON.stringify({
                                username: self.username(),
                                first_name: self.firstName(),
                                last_name: self.lastName(),
                                email: self.email()
                            })
                        }).always(function () {
                            // Stop our spinning buttons FIRST
                            createButton.stop();
                        }).done(function () {
                            // Successful creation redirect to the members page so they can add members
                            window.location = '/users/';
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
                                                if (errMsg.indexOf('username') >= 0) {
                                                    var el = $('#username');
                                                    el.addClass('has-error');
                                                    el.append('<span class="help-block">A user with this username already exists.</span>');
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
                                    title: 'Error creating user',
                                    message: message
                                });
                            }
                        });
                    }
                }
            });
        };

        self.reset();
    };
});
