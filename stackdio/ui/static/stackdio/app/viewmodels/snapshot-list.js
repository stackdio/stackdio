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
    'models/snapshot'
], function ($, Pagination, Snapshot) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Snapshots'
            }
        ],
        model: Snapshot,
        baseUrl: '/snapshots/',
        initialUrl: '/api/cloud/snapshots/',
        detailRequiresAdvanced: true,
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '30%'},
            {name: 'description', displayName: 'Description', width: '30%'},
            {name: 'snapshotId', displayName: 'ID', width: '15%' },
            {name: 'filesystemType', displayName: 'Filesystem Type', width: '15%'}
        ]
    });
});
