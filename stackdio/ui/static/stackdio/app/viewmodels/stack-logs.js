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
    'bootbox',
    'generics/pagination',
    'models/stack'
], function ($, ko, bootbox, Pagination, Stack) {
    'use strict';



    return function () {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Stacks',
                href: '/stacks/'
            },
            {
                active: false,
                title: 'Stack Detail',
                href: '/stacks/' + window.stackdio.stackId + '/'
            },
            {
                active: true,
                title: 'Stack Logs'
            }
        ];

        self.stack = ko.observable();
        self.reset = function () {
            self.stack(new Stack(window.stackdio.stackId, self));
            self.stack().loadLogs();
        };

        self.logs = ko.computed(function () {
            if (!self.stack()) {
                return [];
            }
            return self.stack().historicalLogs();
        });

        self.reset();
    };
});
