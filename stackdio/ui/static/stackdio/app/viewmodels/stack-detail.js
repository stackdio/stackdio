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
    'knockout-mapping'
], function($, ko, komapping) {
    return function() {
        var self = this;

        self.id = ko.observable('');
        self.title = ko.observable('');
        self.description = ko.observable();
        self.status = ko.observable();
        self.namespace = ko.observable();
        self.createUsers = ko.observable();
        self.hostCount = ko.observable();
        self.volumeCount = ko.observable();
        self.created = ko.observable();

        self.url = ko.computed(function() {
            return  '/api/stacks/'+self.id()+'/';
        });

        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            ko.observable({
                active: true,
                title: ko.computed(function() { return self.title(); })
            })
        ];

        self.reset = function() {
            self.id(window.stackdio.stackId);
            self.title('');
            self.description('');
            self.status('');
            self.namespace('');
            self.createUsers('');
            self.hostCount('');
            self.volumeCount('');
            self.created('');
        };

        // Functions
        self.refreshStack = function () {
            $.ajax({
                method: 'GET',
                url: self.url()
            }).done(function (stack) {
                document.title = 'stackd.io | Stack Detail - ' + stack.title;
                self.title(stack.title);
                self.description(stack.description);
                self.status(stack.status);
                self.namespace(stack.namespace);
                self.createUsers(stack.create_users);
                self.hostCount(stack.host_count);
                self.volumeCount(stack.volume_count);
                self.created(stack.created);
            }).fail(function () {
                // If we get a 404 or something, reset EVERYTHING
                self.reset();
            });
        };

        self.updateStack = function () {
            $.ajax({
                method: 'PUT',
                url: self.url(),
                data: komapping.toJSON(self)
            }).done(function (stack) {
                console.debug(stack);
            }).fail(function (xhr) {
                console.debug(xhr);
            });
        };

        // Start everything up
        self.reset();
        self.refreshStack();
    };
});