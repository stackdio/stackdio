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
    'models/stack'
], function ($, Stack) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.stack = null;

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: false,
                title: window.stackdio.stackTitle,
                href: '/stacks/' + window.stackdio.stackId + '/'
            },
            {
                active: true,
                title: 'Components'
            }
        ];

        self.reset = function() {
            // Create the stack object.  Pass in the stack id, and let the model load itself.
            self.stack = new Stack(window.stackdio.stackId, self);
        };

        self.openId = null;

        // Functions
        self.refreshComponents = function () {
            self.stack.loadComponents().done(function () {
                if (self.openId) {
                    // re-open the component that was open (adding the 'in' class does that)
                    $('#' + self.openId).addClass('in');
                }
                var collapse = $('.panel-collapse');

                // Listen so we know which panel is open
                collapse.on('show.bs.collapse', function (e) {
                    self.openId = e.target.id;
                });
                collapse.on('hide.bs.collapse', function () {
                    self.openId = null;
                });
            });
        };

        // Start everything up
        self.reset();
        self.refreshComponents();
        setInterval(self.refreshComponents, 3000);
    };
});
