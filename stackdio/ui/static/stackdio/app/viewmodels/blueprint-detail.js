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
    'models/blueprint',
    'fuelux'
], function($, ko, Blueprint) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.blueprint = null;
        self.blueprintUrl = ko.observable('');

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Blueprints',
                href: '/blueprints/'
            },
            {
                active: true,
                title: window.stackdio.blueprintTitle
            }
        ];

        self.subscription = null;

        self.reset = function() {
            // Make sure we don't have more than 1 subscription
            if (self.subscription) {
                self.subscription.dispose();
            }

            // Create the blueprint object.  Pass in the blueprint id, and let the model load itself.
            self.blueprint = new Blueprint(window.stackdio.blueprintId, self);
            self.blueprint.waiting.done(function () {
                document.title = 'stackd.io | Blueprint Detail - ' + self.blueprint.title();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/blueprints/';
            });
            var $el = $('.checkbox-custom');
            self.subscription = self.blueprint.createUsers.subscribe(function (newVal) {
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