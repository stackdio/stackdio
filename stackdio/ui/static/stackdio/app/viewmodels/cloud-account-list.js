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
    'models/cloud-account'
], function ($, Pagination, CloudAccount) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Cloud Accounts'
            }
        ],
        model: CloudAccount,
        baseUrl: '/accounts/',
        initialUrl: '/api/cloud/accounts/',
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '20%'},
            {name: 'description', displayName: 'Description', width: '44%'},
            {name: 'vpcId', displayName: 'VPC ID', width: '15%'},
            {name: 'createSecurityGroups', displayName: 'Security Groups', width: '11%'}
        ]
    });
});
