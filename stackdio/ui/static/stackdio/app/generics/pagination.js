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
    'utils/class'
], function ($, ko, Class) {
    'use strict';
    
    return Class.extend({

        // Override these
        breadcrumbs: [],
        model: null,
        baseUrl: null,
        initialUrl: null,
        sortableFields: [],

        // Observable view variables
        pageNum: ko.observable(),
        pageSize: ko.observable(),
        currentPage: ko.observable(),
        previousPage: ko.observable(),
        nextPage: ko.observable(),
        count: ko.observable(),
        objects: ko.observableArray([]),

        init: function () {
            // Start everything up
            this.reset();

            // Needs to happen here so we have access to `this`
            this.sortedObjects = ko.computed(function () {
                var sortKey = this.sortKey();
                var searchTerm = this.searchTerm();

                // If there's nothing to sort/filter on, just return the main list
                if (!this.sortableFields) {
                    return this.objects();
                }

                var self = this;
                var objects = this.objects().filter(function (object) {
                    for (var i = 0; i < self.sortableFields.length; ++i) {
                        if (object[self.sortableFields[i]]().toString().indexOf(searchTerm) >= 0) {
                            return true;
                        }
                    }
                    return false;
                });

                if (this.sortableFields.indexOf(sortKey) < 0) {
                    return objects;
                }
                return objects.sort(function (a, b) {
                    if (!self.sortAsc()) {
                        var tmp = a;
                        a = b;
                        b = tmp;
                    }
                    if (a[sortKey]() < b[sortKey]()) {
                        return -1;
                    } else if (a[sortKey]() > b[sortKey]()) {
                        return 1;
                    } else {
                        return 0;
                    }
                });
            }, this);

            this.startNum = ko.computed(function () {
                if (this.pageSize() === null) {
                    return this.count() > 0 ? 1 : 0;
                }
                return (this.pageNum() - 1) * this.pageSize() + 1;
            }, this);

            this.endNum = ko.computed(function () {
                if (this.pageSize() === null) {
                    return this.objects().length;
                }
                return this.startNum() + Math.min(this.pageSize(), this.objects().length) - 1;
            }, this);

            this.numPages = ko.computed(function () {
                if (this.pageSize() === null) {
                    return 1;
                }
                var pages = this.count() / this.pageSize();
                return this.count() % this.pageSize() == 0 ? pages : pages + 1;
            }, this);

            setInterval((function (self) {
                return function() {
                    self.reload();
                }
            })(this), 3000);
        },

        sortKey: ko.observable(),
        sortAsc: ko.observable(true),
        searchTerm: ko.observable(),

        // Computed observables, to be created in init()
        sortedObjects: null,
        startNum: null,
        endNum: null,
        numPages: null,

        reset: function () {
            this.pageNum(1);
            this.pageSize(null);
            this.currentPage(this.initialUrl);
            this.previousPage(null);
            this.nextPage(null);
            this.count(0);
            this.objects([]);
            this.sortKey(null);
            this.sortAsc(true);
            this.searchTerm('');
            this.reload();
        },

        changeSortKey: function (newKey) {
            var sortKey = this.sortKey();
            if (newKey === sortKey) {
                this.sortAsc(!this.sortAsc());
            } else {
                this.sortKey(newKey);
            }
        },

        goToDetailPage: function (object) {
            window.location = this.baseUrl + object.id + '/';
        },

        goToNextPage: function () {
            if (this.nextPage() !== null) {
                this.currentPage(this.nextPage());
                this.pageNum(this.pageNum() + 1);
                this.reload();
            }
        },

        goToPreviousPage: function() {
            if (this.previousPage() !== null) {
                this.currentPage(this.previousPage());
                this.pageNum(this.pageNum() - 1);
                this.reload();
            }
        },

        processObject: function (object) {
            // Override this if there's extra work to be done after instantiating the model
        },

        extraReloadSteps: function () {
            // Override this if there's extra steps to be taken after the objects observable has
            // been populated
        },

        // Refresh everything
        reload: function () {
            var self = this;
            $.ajax({
                method: 'GET',
                url: this.currentPage()
            }).done(function (objects) {
                self.count(objects.count);
                self.previousPage(objects.previous);
                self.nextPage(objects.next);
                if (objects.next !== null) {
                    self.pageSize(objects.results.length);
                }

                self.objects(objects.results.map(function (object) {
                    var objectModel = new self.model(object, self);
                    self.processObject(objectModel);
                    return objectModel;
                }));

                self.extraReloadSteps();
            }).fail(function () {
                // If we get a 404 or something, reset EVERYTHING.
                self.reset();
            });
        }
    });
});
