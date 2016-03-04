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
    'models/group'
], function($, ko, Group) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.group = null;

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Groups',
                href: '/groups/'
            },
            {
                active: true,
                title: window.stackdio.groupName
            }
        ];

        self.reset = function() {

            // Create the group object.  Pass in the group id, and let the model load itself.
            self.group = new Group(window.stackdio.groupName, self);
            self.group.waiting.done(function () {
                document.title = 'stackd.io | Group Detail - ' + self.group.name();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/groups/';
            });
        };

        // Start everything up
        self.reset();
    };
});