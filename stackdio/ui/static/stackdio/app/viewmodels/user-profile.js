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
    'models/user'
], function($, ko, User) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.user = null;

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


        // Start everything up
        self.reset();
    };
});