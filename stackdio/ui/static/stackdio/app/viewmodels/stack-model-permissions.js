
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
], function($, ko) {
    return function() {
        var self = this;

        // breadcrumbs
        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: true,
                title: 'Permissions'
            }
        ];

        // View variables
        self.availableUserPermissions = ko.observableArray([]);
        self.availableGroupPermissions = ko.observableArray([]);
        self.userPermissions = ko.observableArray([]);
        self.groupPermissions = ko.observableArray([]);

        self.loadPermissions = function() {
            $.ajax({
                method: 'GET',
                url: '/api/stacks/permissions/users/'
            }).done(function (permissions) {
                self.userPermissions(permissions.results);
                self.availableUserPermissions(permissions.available_permissions);
            });

            $.ajax({
                method: 'GET',
                url: '/api/stacks/permissions/groups/'
            }).done(function (permissions) {
                self.groupPermissions(permissions.results);
                self.availableGroupPermissions(permissions.available_permissions);
            });
        };

        self.loadPermissions();
    };
});