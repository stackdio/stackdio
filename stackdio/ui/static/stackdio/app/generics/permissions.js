
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
    'bloodhound',
    'bootbox',
    'utils/class',
    'utils/utils',
    'typeahead'
], function($, ko, Bloodhound, bootbox, Class, utils) {
    'use strict';

    return Class.extend({
        breadcrumbs: [],
        permsUrl: null,
        saveUrl: null,
        availableUserPermissions: ko.observableArray([]),
        availableGroupPermissions: ko.observableArray([]),
        userPermissions: ko.observableArray([]),
        groupPermissions: ko.observableArray([]),
        init: function() {
            this.users = this.getBloodhound('user', this.userPermissions);
            this.groups = this.getBloodhound('group', this.groupPermissions);
            this.createTypeahead('user', this.userPermissions, this.availableUserPermissions);
            this.createTypeahead('group', this.groupPermissions, this.availableGroupPermissions);

            this.loadPermissions();
        },
        getBloodhound: function (userOrGroup, permsObservableArray) {
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
        },
        createTypeahead: function (userOrGroup, permsObservableArray, avaliableObservableArray) {
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
                source: this[userOrGroup + 's']
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
        },
        transformPermissions: function (userOrGroup) {
            var permsObservable = this[userOrGroup + 'Permissions'];
            var availablePermsObservable = this['available' + userOrGroup.capitalize() + 'Permissions'];
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
                permsObservable(permissions.results);
                availablePermsObservable(permissions.available_permissions);
            };
        },
        savePermissions: function (userOrGroup, perms, availPerms) {
            var self = this;
            var ajaxList = [];
            var bulkUpdateList = [];

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

                if (perm.hasOwnProperty('url')) {
                    // Already existing user/group - add it to the bulk update list
                    bulkUpdateList.push(data);
                } else {
                    // This user/group didn't previously have permissions, need to create
                    ajaxList.push($.ajax({
                        method: 'POST',
                        url: this.permsUrl + userOrGroup + 's/',
                        data: JSON.stringify(data)
                    }));
                }
            }, this);

            // always do the create list first - then do the bulk update
            return $.when.apply(this, ajaxList).done(function () {
                return $.ajax({
                    method: 'PUT',
                    url: self.permsUrl + userOrGroup + 's/',
                    data: JSON.stringify(bulkUpdateList)
                }).done(function (perms) {
                    utils.growlAlert('Successfully saved ' + userOrGroup + ' permissions!', 'success');
                    self.loadPermissions();
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving permissions');
                });
            }).fail(function (jqxhr) {
                utils.alertError(jqxhr, 'Error saving permissions');
            });
        },
        loadPermissions: function() {
            $.ajax({
                method: 'GET',
                url: this.permsUrl + 'users/'
            }).done(this.transformPermissions('user')).fail(function (jqxhr) {
                utils.alertError(jqxhr, 'Error fetching permissions');
            });

            $.ajax({
                method: 'GET',
                url: this.permsUrl + 'groups/'
            }).done(this.transformPermissions('group')).fail(function (jqxhr) {
                utils.alertError(jqxhr, 'Error fetching permissions');
            });
        },
        userSave: function () {
            this.savePermissions('user', this.userPermissions(), this.availableUserPermissions());

        },
        groupSave: function () {
            this.savePermissions('group', this.groupPermissions(), this.availableGroupPermissions());
        }
    });
});