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
    'models/snapshot'
], function($, ko, Snapshot) {
    'use strict';

    return function() {
        var self = this;

        // View variables
        self.snapshot = null;
        self.snapshotUrl = ko.observable('');

        // Override the breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Snapshots',
                href: '/snapshots/'
            },
            {
                active: true,
                title: window.stackdio.snapshotTitle
            }
        ];

        self.reset = function() {
            // Create the snapshot object.  Pass in the snapshot id, and let the model load itself.
            self.snapshot = new Snapshot(window.stackdio.snapshotId, self);
            self.snapshot.waiting.done(function () {
                document.title = 'stackd.io | Snapshot Detail - ' + self.snapshot.title();
            }).fail(function () {
                // Just go back to the main page if we fail
                window.location = '/snapshots/';
            });
        };

        // Start everything up
        self.reset();
    };
});