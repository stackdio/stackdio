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
    'models/stack'
], function($, ko, Stack) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.stack = null;
        self.blueprintTitle = ko.observable(window.stackdio.blueprintTitle);
        self.blueprintUrl = ko.observable('/blueprints/' + window.stackdio.blueprintId + '/');

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: true,
                title: window.stackdio.stackTitle
            }
        ];

        self.subscription = null;

        self.reset = function() {
            // Make sure we don't have more than 1 subscription
            if (self.subscription) {
                self.subscription.dispose();
            }

            // Create the stack object.  Pass in the stack id, and let the model load itself.
            self.stack = new Stack(window.stackdio.stackId, self);
            self.stack.waiting.done(function () {
                document.title = 'stackd.io | Stack Detail - ' + self.stack.title();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/stacks/';
            });
            var $el = $('.checkbox-custom');
            self.subscription = self.stack.createUsers.subscribe(function (newVal) {
                if (newVal) {
                    $el.checkbox('check');
                } else {
                    $el.checkbox('uncheck');
                }
            });
        };

        // Functions
        self.refreshStack = function () {
            self.stack.refreshActivity().fail(function () {
                window.location = '/stacks/';
            });
            self.stack.loadHistory();
        };

        // React to an open-dropdown event & lazy load the actions
        $('.action-dropdown').on('show.bs.dropdown', function () {
            self.stack.loadAvailableActions();
        });

        // Start everything up
        self.reset();
        self.refreshStack();
        setInterval(self.refreshStack, 3000);
    };
});