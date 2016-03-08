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
    'utils/class',
    'fuelux'
], function ($, ko, Class) {
    'use strict';
    
    return Class.extend({

        // Override these
        breadcrumbs: [],
        model: null,
        baseUrl: null,
        initialUrl: null,
        sortableFields: [],
        autoRefresh: true,
        detailRequiresAdvanced: false,

        // Observable view variables
        pageNum: ko.observable(),
        pageSize: ko.observable(),
        currentPage: ko.observable(),
        previousPage: ko.observable(),
        nextPage: ko.observable(),
        count: ko.observable(),
        objects: ko.observableArray([]),
        loading: ko.observable(),
        sortKey: ko.observable(),
        sortAsc: ko.observable(true),

        permissionsMap: window.stackdio.permissionsMap,

        // Computed observables, to be created in init()
        sortedObjects: null,
        startNum: null,
        endNum: null,
        numPages: null,

        searchInput: $('#search-input'),

        shouldReset: true,

        init: function () {
            // Start everything up
            this.reset();

            var self = this;

            var $searchBar = $('#pagination-search');

            $searchBar.search();

            $searchBar.on('searched.fu.search', function () {
                self.currentPage(self.initialUrl + '?q=' + self.searchInput.val());
                self.shouldReset = false;
                self.reset();
            });

            $searchBar.on('cleared.fu.search', function () {
                self.reset();
            });

            // Needs to happen here so we have access to `this`
            this.sortedObjects = ko.computed(function () {
                var sortKey = this.sortKey();

                // If there's nothing to sort/filter on, just return the main list
                if (!this.sortableFields) {
                    return this.objects();
                }

                var fieldNames = this.sortableFields.map(function (field) {
                    return field.name;
                });

                var self = this;
                var objects = self.objects();

                if (fieldNames.indexOf(sortKey) < 0) {
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

            if (this.autoRefresh) {
                this.intervalId = setInterval((function (self) {
                    return function() {
                        self.reload();
                    }
                })(this), 3000);
            }
        },

        reset: function () {
            this.pageNum(1);
            this.pageSize(null);

            if (this.shouldReset) {
                this.currentPage(this.initialUrl);
                this.sortKey(null);
                this.sortAsc(true);
            }
            this.previousPage(null);
            this.nextPage(null);
            this.count(0);
            this.objects([]);
            this.loading(false);
            this.shouldReset = true;
            this.reload(true);
        },

        changeSortKey: function (newKey) {
            var sortKey = this.sortKey();
            if (newKey.name === sortKey) {
                this.sortAsc(!this.sortAsc());
            } else {
                this.sortKey(newKey.name);
            }
        },

        goToDetailPage: function (object) {
            if (this.detailRequiresAdvanced && !window.stackdio.advancedView) {
                return;
            }
            window.location = this.baseUrl + object.id + '/';
        },

        goToNextPage: function () {
            if (this.nextPage() !== null) {
                this.currentPage(this.nextPage());
                this.pageNum(this.pageNum() + 1);
                this.reload(true);
            }
        },

        goToPreviousPage: function() {
            if (this.previousPage() !== null) {
                this.currentPage(this.previousPage());
                this.pageNum(this.pageNum() - 1);
                this.reload(true);
            }
        },

        processObject: function (object) {
            // Override this if there's extra work to be done after instantiating the model
        },

        extraReloadSteps: function () {
            // Override this if there's extra steps to be taken after the objects observable has
            // been populated
        },

        filterObject: function (object) {
            // Override this if certain objects need to be filtered out of the list.  Just
            // return true if the object should stay, or false if it should be removed.
            // By default, don't remove anything
            return true;
        },

        // Refresh everything
        reload: function (firstTime) {
            if (typeof firstTime === 'undefined') {
                firstTime = false;
            }
            if (firstTime) {
                this.loading(true);
            }
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

                // Filter and create the models.
                self.objects(objects.results.filter(self.filterObject).map(function (object) {
                    var objectModel = new self.model(object, self);
                    self.processObject(objectModel);
                    return objectModel;
                }));

                self.extraReloadSteps();
            }).fail(function (jqxhr) {
                if (jqxhr.status == 403) {
                    // On 403, we should reload, which SHOULD redirect to the login page
                    window.location.reload(true);
                } else {
                    // If we get a 404 or something else, reset EVERYTHING.
                    self.reset();
                }
            }).always(function () {
                self.loading(false);
            });
        }
    });
});
