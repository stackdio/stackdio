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
    'generics/pagination',
    'models/group'
], function ($, Pagination, Group) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Groups'
            }
        ],
        model: Group,
        baseUrl: '/groups/',
        initialUrl: '/api/groups/',
        detailRequiresAdvanced: true,
        sortableFields: [
            {name: 'name', displayName: 'Group Name', width: '90%'}
        ],
        goToDetailPage: function (object) {
            if (this.detailRequiresAdvanced && !window.stackdio.advancedView) {
                return;
            }
            window.location = this.baseUrl + object.name() + '/members/';
        }
    });
});
