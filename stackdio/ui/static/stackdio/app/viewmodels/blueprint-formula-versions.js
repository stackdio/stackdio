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
    'generics/formula-versions',
    'models/blueprint'
], function (Versions, Blueprint) {
    'use strict';

    return Versions.extend({
        breadcrumbs: [
            {
                active: false,
                title: 'Blueprints',
                href: '/blueprints/'
            },
            {
                active: false,
                title: window.stackdio.blueprintTitle,
                href: '/blueprints/' + window.stackdio.blueprintId + '/'
            },
            {
                active: true,
                title: 'Formula Versions'
            }
        ],
        objectId: window.stackdio.blueprintId,
        parentModel: Blueprint,
        baseUrl: '/blueprints/',
        initialUrl: '/api/blueprints/' + window.stackdio.blueprintId + '/formula_versions/'
    });
});
