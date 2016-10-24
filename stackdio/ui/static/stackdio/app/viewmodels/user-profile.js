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
    'models/user'
], function($, ko, bootbox, User) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.user = null;
        self.userTokenShown = ko.observable();
        self.userToken = ko.observable();
        self.apiRootUrl = ko.observable();

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: true,
                title: 'User Profile'
            }
        ];

        self.subscription = null;

        self.reset = function() {
            // Make sure we don't have more than 1 subscription
            if (self.subscription) {
                self.subscription.dispose();
            }

            // Create the user object.
            self.user = new User(null, self);
            self.userTokenShown(false);
            self.userToken(null);
            self.apiRootUrl(window.location.origin + '/api/');
            var $el = $('.checkbox-custom');
            self.subscription = self.user.advanced.subscribe(function (newVal) {
                if (newVal) {
                    $el.checkbox('check');
                } else {
                    $el.checkbox('uncheck');
                }
            });

            self.user.waiting.done(function () {
                self.user.loadGroups();
            });
        };

        self.promptPassword = function (msg, callback) {
            bootbox.prompt({
                title: msg,
                inputType: 'password',
                callback: callback
            });
        };

        self.showUserToken = function () {
            self.promptPassword('Enter password to retrieve token',
                function (password) {
                    $.ajax({
                        method: 'POST',
                        url: '/api/user/token/',
                        data: JSON.stringify({
                            username: self.user.username(),
                            password: password
                        })
                    }).done(function (resp) {
                        self.userToken(resp.token);
                        self.userTokenShown(true);
                    }).fail(function (jqxhr) {

                    });
                });
        };

        self.resetUserToken = function () {
            self.promptPassword('Enter password to reset token',
                function (password) {
                    $.ajax({
                        method: 'POST',
                        url: '/api/user/token/reset/',
                        data: JSON.stringify({
                            username: self.user.username(),
                            password: password
                        })
                    }).done(function (resp) {
                        self.userToken(resp.token);
                        self.userTokenShown(true);
                    }).fail(function (jqxhr) {

                    });
                });
        };

        // Start everything up
        self.reset();
    };
});