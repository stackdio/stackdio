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
    'knockout'
], function ($, ko) {
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
        self.stacks = ko.observableArray();

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

        // Functions
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
                self.stacks(stacks.results);
            }).fail(function () {
                // If we get a 404 or something, reset EVERYTHING
                self.reset();
            });
        };

        self.deleteStack = function (stack) {
            $.ajax({
                method: 'DELETE',
                url: stack.url
            }).done(function () {
                self.reloadStacks();
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.log(jqXHR);
                console.log(textStatus);
                console.log(errorThrown);
            });
        };

        // Start everything up
        self.reset();
        setInterval(self.reloadStacks, 3000);
    };
});
