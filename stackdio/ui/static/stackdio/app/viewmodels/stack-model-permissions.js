
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
    'bloodhound',
    'typeahead'
], function($, ko, Bloodhound) {
    'use strict';

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

        // Helper functions
        self.getBloodhound = function (userOrGroup, permsObservableArray) {
            var lookupField;
            switch (userOrGroup){
                case 'user':
                    lookupField = 'username';
                    break;
                case 'group':
                    lookupField = 'name';
                    break;
            }

            return new Bloodhound({
                datumTokenizer: Bloodhound.tokenizers.whitespace,
                queryTokenizer: Bloodhound.tokenizers.whitespace,
                remote: {
                    url: '/api/' + userOrGroup + 's/?' + lookupField + '=%QUERY',
                    wildcard: '%QUERY',
                    transform: function (resp) {
                        var ret = [];
                        var current = permsObservableArray().map(function (perm) {
                            return perm[userOrGroup];
                        });
                        resp.results.forEach(function (obj) {
                            if (current.indexOf(obj[lookupField]) < 0) {
                                ret.push(obj);
                            }
                        });
                        return ret;
                    }
                }
            });
        };

        self.createTypeahead = function (userOrGroup, permsObservableArray, avaliableObservableArray) {
            var selector = $('#add-' + userOrGroup + ' .typeahead');

            var lookupField;
            switch (userOrGroup){
                case 'user':
                    lookupField = 'username';
                    break;
                case 'group':
                    lookupField = 'name';
                    break;
            }
            selector.typeahead({
                highlight: true
            }, {
                name: userOrGroup + 's',
                display: lookupField,
                source: self[userOrGroup + 's']
            });

            selector.bind('typeahead:select', function(ev, obj) {
                var newPerms = [];
                avaliableObservableArray().forEach(function (permissionChoice) {
                    newPerms[permissionChoice] = ko.observable(false);
                });
                var newObj = {
                    permissions: newPerms
                };
                newObj[userOrGroup] = obj[lookupField];
                permsObservableArray.push(newObj);
                selector.typeahead('val', null);
            });
        };

        self.transformPermissions = function (userOrGroup) {
            return function (permissions) {
                permissions.results.forEach(function (permission) {
                    var permObj = {};

                    permissions.available_permissions.forEach(function (permissionChoice) {
                        permObj[permissionChoice] = ko.observable(false);
                    });
                    permission.permissions.forEach(function (permissionChoice) {
                        permObj[permissionChoice](true);
                    });
                    permission.permissions = permObj;
                });
                self[userOrGroup + 'Permissions'](permissions.results);
                self['available' + userOrGroup.capitalize() + 'Permissions'](permissions.available_permissions);
            };
        };

        self.savePermissions = function (userOrGroup, perms, availPerms) {
            var ajaxList = [];
            perms.forEach(function (perm) {
                var newPerms = [];
                availPerms.forEach(function (availablePerm) {
                    if (perm.permissions[availablePerm]()) {
                        newPerms.push(availablePerm);
                    }
                });

                var data = {
                    permissions: newPerms
                };

                data[userOrGroup] = perm[userOrGroup];

                data = JSON.stringify(data);

                var request;
                if (perm.hasOwnProperty('url')) {
                    request = $.ajax({
                        method: 'PUT',
                        url: perm.url,
                        data: data
                    });
                } else {
                    request = $.ajax({
                        method: 'POST',
                        url: '/api/stacks/permissions/' + userOrGroup + 's/',
                        data: data
                    });
                }
                ajaxList.push(request);
            });

            return ajaxList;
        };

        // View variables
        self.availableUserPermissions = ko.observableArray([]);
        self.availableGroupPermissions = ko.observableArray([]);
        self.userPermissions = ko.observableArray([]);
        self.groupPermissions = ko.observableArray([]);

        self.users = self.getBloodhound('user', self.userPermissions);
        self.groups = self.getBloodhound('group', self.groupPermissions);

        self.createTypeahead('user', self.userPermissions, self.availableUserPermissions);
        self.createTypeahead('group', self.groupPermissions, self.availableGroupPermissions);

        self.loadPermissions = function() {
            $.ajax({
                method: 'GET',
                url: '/api/stacks/permissions/users/'
            }).done(self.transformPermissions('user')).fail(function (jqxhr) {
                alert('Unable to load permissions.  Please check the log.');
                console.log(jqxhr);
            });

            $.ajax({
                method: 'GET',
                url: '/api/stacks/permissions/groups/'
            }).done(self.transformPermissions('group')).fail(function (jqxhr) {
                alert('Unable to load permissions.  Please check the log.');
                console.log(jqxhr);
            });
        };

        self.save = function () {
            var ajaxList = self.savePermissions('user', self.userPermissions(), self.availableUserPermissions());
            ajaxList.push.apply(ajaxList, self.savePermissions('group', self.groupPermissions(), self.availableGroupPermissions()));


            $.when.apply(self, ajaxList).done(function () {
                window.location = '/stacks/';
            }).fail(function (jqxhr) {
                alert('Failed to assign permissions.  Please check the log.');
                console.log(jqxhr);
            });

        };

        self.loadPermissions();
    };
});