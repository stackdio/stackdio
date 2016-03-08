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
    'generics/pagination',
    'utils/utils',
    'models/security-group',
    'select2'
], function($, ko, Pagination, utils, SecurityGroup) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Cloud Accounts',
                href: '/accounts/'
            },
            {
                active: false,
                title: window.stackdio.accountTitle,
                href: '/accounts/' + window.stackdio.accountId + '/'
            },
            {
                active: true,
                title: 'Default Security Groups'
            }
        ],
        model: SecurityGroup,
        newGroupName: ko.observable(),
        baseUrl: '/accounts/' + window.stackdio.accountId + '/security_groups/',
        accountUrl: '/api/cloud/accounts/' + window.stackdio.accountId + '/',
        initialUrl: '/api/cloud/accounts/' + window.stackdio.accountId + '/security_groups/',
        sortableFields: [
            {name: 'name', displayName: 'Name', width: '30%'},
            {name: 'description', displayName: 'Description', width: '35%'},
            {name: 'managed', displayName: 'Managed', width: '10%'},
            {name: 'groupId', displayName: 'Group ID', width: '15%'}
        ],
        filterObject: function (object) {
            return object.default;
        },
        init: function () {
            this._super();

            this.createSelector();

            var self = this;

            // Make sure we don't have multiple event listeners
            this.sgSelector.on('select2:select', function (ev) {
                var group = ev.params.data;

                $.ajax({
                    method: 'POST',
                    url: self.accountUrl + 'security_groups/',
                    data: JSON.stringify({
                        'group_id': group.group_id,
                        'default': true
                    })
                }).done(function () {
                    self.sgSelector.empty();
                    self.sgSelector.val(null).trigger('change');
                    self.reload();
                }).fail(function (jqxhr) {
                    utils.alertError(jqxhr, 'Error saving permissions');
                });
            });
        },
        createSelector: function () {
            this.sgSelector = $('#accountSecurityGroups');

            var self = this;

            this.sgSelector.select2({
                ajax: {
                    url: this.accountUrl + 'security_groups/all/',
                    dataType: 'json',
                    delay: 100,
                    data: function (params) {
                        return {
                            name: params.term
                        };
                    },
                    processResults: function (data) {
                        var realData = [];
                        data.results.forEach(function (group) {
                            group.text = group.name;
                            group.id = group.name;

                            var shouldAdd = true;
                            self.objects().forEach(function (realGroup) {
                                if (realGroup.groupId() === group.group_id) {
                                    shouldAdd = false;
                                }
                            });
                            if (shouldAdd) {
                                realData.push(group);
                            }
                        });
                        return { results: realData };
                    },
                    cache: true
                },
                theme: 'bootstrap',
                disabled: false,
                placeholder: 'Select a security group...',
                minimumInputLength: 0
            });
        },
        addNewGroup: function () {
            var self = this;
            $.ajax({
                method: 'POST',
                url: this.accountUrl + 'security_groups/',
                data: JSON.stringify({
                    'name': this.newGroupName(),
                    'default': true
                })
            }).done(function () {
                self.newGroupName('');
                self.reload();
            }).fail(function (jqxhr) {
                utils.alertError(jqxhr, 'Error saving permissions');
            });
        }
    });
});