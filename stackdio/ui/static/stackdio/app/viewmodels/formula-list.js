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
    'generics/pagination',
    'models/formula'
], function ($, Pagination, Formula) {
    'use strict';

    return Pagination.extend({
        breadcrumbs: [
            {
                active: true,
                title: 'Formulas'
            }
        ],
        model: Formula,
        baseUrl: '/formulas/',
        initialUrl: '/api/formulas/',
        sortableFields: [
            {name: 'title', displayName: 'Title', width: '25%'},
            {name: 'uri', displayName: 'Repo URL', width: '50%'},
            {name: 'status', displayName: 'Status', width: '10%'},
            {name: 'privateGitRepo', displayName: 'Private', width: '5%'}
        ]
    });
});
