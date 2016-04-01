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
    'models/cloud-account'
], function($, ko, CloudAccount) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.account = null;
        self.accountUrl = ko.observable('');

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Cloud Accounts',
                href: '/accounts/'
            },
            {
                active: true,
                title: window.stackdio.accountTitle
            }
        ];

        self.subscription = null;

        self.reset = function() {
            // Make sure we don't have more than 1 subscription
            if (self.subscription) {
                self.subscription.dispose();
            }

            // Create the account object.  Pass in the account id, and let the model load itself.
            self.account = new CloudAccount(window.stackdio.accountId, self);
            self.account.waiting.done(function () {
                document.title = 'stackd.io | Cloud Account Detail - ' + self.account.title();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/accounts/';
            });
            var $el = $('.checkbox-custom');
            self.subscription = self.account.createSecurityGroups.subscribe(function (newVal) {
                if (newVal) {
                    $el.checkbox('check');
                } else {
                    $el.checkbox('uncheck');
                }
            });
        };

        // Start everything up
        self.reset();
    };
});