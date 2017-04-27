/*!
  * Copyright 2017,  Digital Reasoning
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
    'models/environment'
], function ($, ko, Environment) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.environment = null;

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Environments',
                href: '/environments/'
            },
            {
                active: false,
                title: window.stackdio.environmentName,
                href: '/environments/' + window.stackdio.environmentName + '/'
            },
            {
                active: true,
                title: 'Components'
            }
        ];

        self.availableComponents = ko.observableArray();
        self.selectedComponent = ko.observable();
        self.hostTarget = ko.observable();

        self.reset = function() {
            // Create the environment object.  Pass in the environment id, and let the model load itself.
            self.environment = new Environment(window.stackdio.environmentName, self);
            self.availableComponents([]);
            self.selectedComponent(null);
            self.hostTarget(null);
        };

        self.openMap = {};

        // Functions
        self.refreshComponents = function () {
            self.environment.loadComponents().done(function () {
                if (self.availableComponents().length == 0) {
                    self.availableComponents(self.environment.components());
                }

                Object.keys(self.openMap).forEach(function (id) {
                    if (self.openMap[id]) {
                        $('#' + id).addClass('in');
                    }
                });

                self.environment.components().forEach(function (component) {
                     var collapse = $('#' + component.htmlId);

                    // Listen so we know which panel is open
                    collapse.on('show.bs.collapse', function () {
                        self.openMap[component.htmlId] = true;
                    });
                    collapse.on('hide.bs.collapse', function () {
                        self.openMap[component.htmlId] = false;
                    });
                });
                if (self.openId) {
                    // re-open the component that was open (adding the 'in' class does that)

                }

            });
        };

        self.reload = function () {
            self.refreshComponents();
            self.selectedComponent(null);
            self.hostTarget(null);
        };

        self.runSingle = function () {
            self.environment.runSingleSls(self.selectedComponent().sls_path, self.hostTarget()).done(function () {

            });
        };

        // Start everything up
        self.reset();
        self.refreshComponents();
        setInterval(self.refreshComponents, 3000);
    };
});
