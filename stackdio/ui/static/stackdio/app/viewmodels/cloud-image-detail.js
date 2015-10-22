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
    'models/cloud-image',
    'models/cloud-account'
], function($, ko, CloudImage, CloudAccount) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.image = null;
        self.account = null;

        // For the breadcrumb only
        self.imageTitle = ko.observable('');

        self.imageTitle = ko.observable('');
        self.imageUrl = ko.observable('');

        self.accountTitle = ko.observable();
        self.accountUrl = '/accounts/' + window.stackdio.accountId + '/';

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Cloud Images',
                href: '/images/'
            },
            ko.observable({
                active: true,
                title: ko.computed(function() {
                    return self.imageTitle()
                })
            })
        ];

        self.reset = function() {
            // Create the image object.  Pass in the image id, and let the model load itself.
            self.image = new CloudImage(window.stackdio.imageId, self);
            self.account = new CloudAccount(window.stackdio.accountId, self);
            self.image.waiting.done(function () {
                document.title = 'stackd.io | Cloud Image Detail - ' + self.image.title();
                self.imageTitle(self.image.title());
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/images/';
            });
            self.account.waiting.done(function () {
                self.accountTitle(self.account.title() + '  --  ' + self.account.description());
            });
        };

        // Start everything up
        self.reset();
    };
});