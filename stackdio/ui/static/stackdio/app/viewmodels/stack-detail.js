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
    'models/stack'
], function($, ko, Stack) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.stack = null;

        // For the breadcrumb only
        self.stackTitle = ko.observable('');

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            ko.observable({
                active: true,
                title: ko.computed(function() {
                    return self.stackTitle()
                })
            })
        ];

        self.alerts = ko.observableArray([]);

        self.reset = function() {
            // Create the stack object.  Pass in the stack id, and let the model load itself.
            self.stack = new Stack(window.stackdio.stackId, self);
            self.stack.loadHistory();
            self.stackTitle('');
            self.alerts([]);
        };

        // Functions
        self.refreshStack = function () {
            self.stack.reload().done(function () {
                document.title = 'stackd.io | Stack Detail - ' + self.stack.title();
                self.stackTitle(self.stack.title());
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/stacks/';
            });
            self.stack.loadHistory();

            // React to an open-dropdown event & lazy load the actions
            $('.action-dropdown').on('show.bs.dropdown', function () {
                self.stack.loadAvailableActions();
            });
        };

        // Start everything up
        self.reset();
        self.refreshStack();
        setInterval(self.refreshStack, 3000);
    };
});