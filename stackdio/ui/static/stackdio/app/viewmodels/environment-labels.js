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
    'generics/labels',
    'models/environment'
], function (Labels, Environment) {
    'use strict';

    return Labels.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Environments',
                href: '/environments/'
            },
            {
                active: false,
                title: window.stackdio.environmentName,
                href: '/environments/' + window.stackdio.environmentName + '/'
            },
            {
                active: true,
                title: 'Labels'
            }
        ],
        parentModel: Environment,
        parentId: window.stackdio.environmentName,
        baseUrl: '/environments/',
        initialUrl: '/api/environments/' + window.stackdio.environmentName + '/labels/'
    });
});
