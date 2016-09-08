
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
    'models/blueprint',
    'models/host-definition',
    'fuelux'
], function($, ko, Blueprint, HostDefinition) {
    'use strict';
    return function () {
        var self = this;

        self.blueprint = new Blueprint(window.stackdio.blueprintId);
        self.currentHostDefinition = ko.observable(null);
        self.hostDefinitionModal = $('#edit-host-definition-modal');
        self.subsciption = null;

        self.breadcrumbs = [
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
                title: 'Host Definitions'
            }
        ];

        self.reload = function () {
            self.blueprint.waiting.done(function () {
                self.blueprint.loadHostDefinitions();
            });
        };

        self.editHostDefinition = function (hostDefinition) {
            self.currentHostDefinition(new HostDefinition(hostDefinition.raw));
            self.hostDefinitionModal.modal('show');
            var $el = $('.checkbox-custom');
            // Set the initial value
            if (self.currentHostDefinition().isSpot()) {
                $el.checkbox('check');
            } else {
                $el.checkbox('uncheck')
            }
        };

        self.saveHostDefinition = function () {
            self.currentHostDefinition().save().done(function (hostDefinition) {
                self.hostDefinitionModal.modal('hide');
                self.currentHostDefinition(null);
                self.blueprint.loadHostDefinitions();
            });
        };

        self.reload();
    }
});