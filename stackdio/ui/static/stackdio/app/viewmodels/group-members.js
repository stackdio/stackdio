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
    'bootbox',
    'generics/pagination',
    'models/user',
    'models/group',
    'select2'
], function ($, ko, bootbox, Pagination, User, Group) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Groups',
                href: '/groups/'
            },
            {
                active: false,
                title: window.stackdio.groupName,
                href: '/groups/' + window.stackdio.groupName + '/'
            },
            {
                active: true,
                title: 'Members'
            }
        ],
        group: null,
        autoRefresh: true,
        userSelector: $('#groupUser'),
        model: User,
        baseUrl: '/groups/',
        initialUrl: '/api/groups/' + window.stackdio.groupName + '/users/',
        sortableFields: [
            {name: 'username', displayName: 'Username', width: '90%'}
        ],
        createSelector: function () {
            var self = this;

            // Create the user selector
            this.userSelector.select2({
                ajax: {
                    url: '/api/users/',
                    dataType: 'json',
                    delay: 100,
                    data: function (params) {
                        return {
                            username: params.term
                        };
                    },
                    processResults: function (data) {
                        data.results = data.results.filter(function (user) {
                            user.id = user.username;
                            user.text = user.username;

                            var duplicate = false;
                            self.objects().forEach(function (memberUser) {
                                if (memberUser.username() === user.username) {
                                    duplicate = true;
                                }
                            });

                            return !duplicate;
                        });

                        return data;
                    },
                    cache: true
                },
                theme: 'bootstrap',
                placeholder: 'Add a user to this group...',
                minimumInputLength: 0
            });
        },
        init: function () {
            this._super();
            this.group = new Group(window.stackdio.groupName, this);
            this.createSelector();

            var self = this;

            // Do this here so we don't get a bunch of selectors
            this.userSelector.on('select2:select', function(ev) {
                var user = ev.params.data;
                self.group.addUser(user).done(function () {
                    self.userSelector.empty();
                    self.userSelector.val(null).trigger('change');
                    self.userSelector.select2('open');
                });
            });
        },
        addUser: function () {

        }
    });
});
