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
], function ($, ko, Stack) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: true,
                title: 'Stacks'
            }
        ];

        // Observable view variables
        self.pageNum = ko.observable();
        self.pageSize = ko.observable();
        self.currentPage = ko.observable();
        self.previousPage = ko.observable();
        self.nextPage = ko.observable();
        self.count = ko.observable();
        self.stacks = ko.observableArray([]);

        // We need to keep track of which action dropdown is open.  This way we can keep
        // it open across a refresh.
        self.openActionStackId = null;

        // Save a copy of the actions for each stack
        self.actionMap = {};

        self.startNum = ko.computed(function () {
            if (self.pageSize() === null) {
                return self.count() > 0 ? 1 : 0;
            }
            return (self.pageNum() - 1) * self.pageSize() + 1;
        });

        self.endNum = ko.computed(function () {
            if (self.pageSize() === null) {
                return self.stacks().length;
            }
            return self.startNum() + Math.min(self.pageSize(), self.stacks().length) - 1;
        });

        self.numPages = ko.computed(function () {
            if (self.pageSize() === null) {
                return 1;
            }
            var pages = self.count() / self.pageSize();
            return self.count() % self.pageSize() == 0 ? pages : pages + 1;
        });

        self.reset = function () {
            self.pageNum(1);
            self.pageSize(null);
            self.currentPage('/api/stacks/');
            self.previousPage(null);
            self.nextPage(null);
            self.count(0);
            self.stacks([]);
            self.openActionLists = [];
            self.actionMap = {};
            self.reloadStacks();
        };

        self.goToDetailPage = function (stack) {
            window.location = '/stacks/' + stack.id + '/';
        };

        self.goToNextPage = function () {
            if (self.nextPage() !== null) {
                self.currentPage(self.nextPage());
                self.pageNum(self.pageNum() + 1);
                self.reloadStacks();
            }
        };

        self.goToPreviousPage = function() {
            if (self.previousPage() !== null) {
                self.currentPage(self.previousPage());
                self.pageNum(self.pageNum() - 1);
                self.reloadStacks();
            }
        };

        // Refresh everything
        self.reloadStacks = function () {
            $.ajax({
                method: 'GET',
                url: self.currentPage()
            }).done(function (stacks) {
                self.count(stacks.count);
                self.previousPage(stacks.previous);
                self.nextPage(stacks.next);
                if (stacks.next !== null) {
                    self.pageSize(stacks.results.length);
                }

                var stackModels = [];
                stacks.results.forEach(function (rawStack) {
                    // Create a new stack
                    var stackModel = new Stack(rawStack, self);

                    // Check if we already have a list of actions for this stack, and inject them if so
                    if (self.actionMap.hasOwnProperty(rawStack.id)) {
                        stackModel.availableActions(self.actionMap[rawStack.id]);
                    }

                    stackModels.push(ko.observable(stackModel));
                });
                self.stacks(stackModels);

                // Add the dropdown events.  This must happen AFTER we set the stacks observable
                // in the previous statement.
                var actionElement = $('.action-dropdown');

                // React to an open-dropdown event
                actionElement.on('show.bs.dropdown', function (evt) {
                    // Grab the ID of the open element
                    var id = parseInt(evt.target.id);

                    // Set the ID of the currently open action dropdown
                    self.openActionStackId = id;

                    // Freeze a copy of the current stacks
                    var stacks = self.stacks();

                    // Find the current stack with the correct ID, and load the actions
                    for (var i = 0, length = stacks.length; i < length; ++i) {
                        if (stacks[i]().id === id) {
                            stacks[i]().loadAvailableActions();
                            break;
                        }
                    }
                });

                // React to a close dropdown event (this one is pretty simple)
                actionElement.on('hide.bs.dropdown', function () {
                    // Make sure that we know nothing is open
                    self.openActionStackId = null;
                });
            }).fail(function () {
                // If we get a 404 or something, reset EVERYTHING.
                self.reset();
            });
        };

        // Start everything up
        self.reset();
        setInterval(self.reloadStacks, 3000);
    };
});
