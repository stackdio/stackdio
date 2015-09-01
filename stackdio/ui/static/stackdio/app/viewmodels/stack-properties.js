
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
    'jsoneditor',
    'models/stack'
], function($, ko, bootbox, JSONEditor, Stack) {
    'use strict';
    return function () {
        var self = this;

        self.alerts = [];

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
                title: 'Stack Properties'
            }
        ];

        self.validProperties = true;

        self.stack = new Stack(window.stackdio.stackId);

        self.propertiesJSON = ko.pureComputed({
            read: function () {
                return ko.toJSON(self.stack.properties(), null, 3);
            },
            write: function (value) {
                try {
                    self.stack.properties(JSON.parse(value));
                    self.validProperties = true;
                } catch (err) {
                    self.validProperties = false;
                }

            }
        });

        self.saveProperties = function () {
            if (!self.validProperties) {
                bootbox.alert({
                    title: 'Error saving properties',
                    message: 'The properties field must contain valid JSON.'
                });
                return;
            }
            self.stack.saveProperties();
        };

        self.reload = function () {
            self.stack.loadProperties();
        };

        self.reload();
    }
});