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
    'models/environment',
    'fuelux'
], function($, ko, Environment) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.environment = null;
        self.environmentUrl = ko.observable('');

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Environments',
                href: '/environments/'
            },
            {
                active: true,
                title: window.stackdio.environmentName
            }
        ];

        self.subscription = null;

        self.reset = function() {
            // Create the environment object.  Pass in the environment id, and let the model load itself.
            self.environment = new Environment(window.stackdio.environmentName, self);
            self.environment.waiting.done(function () {
                document.title = 'stackd.io | Environment Detail - ' + self.environment.name();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/environments/';
            });
        };

        // Start everything up
        self.reset();
    };
});