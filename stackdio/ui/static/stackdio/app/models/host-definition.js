
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
    'knockout',
    'models/formula-component',
    'models/access-rule',
    'models/blueprint-volume'
], function (ko, FormulaComponent, AccessRule, Volume) {
    'use strict';

    // Define the stack model.
    function HostDefinition(raw, parent) {
        var needReload = false;
        if (typeof raw === 'string') {
            raw = parseInt(raw);
        }
        if (typeof raw === 'number') {
            needReload = true;
            // Set the things we need for the reload
            raw = {
                id: raw,
                url: '/api/stacks/' + raw + '/hosts/'
            }
        }

        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the id
        this.id = raw.id;

        // Save the parent VM
        this.parent = parent;

        // Editable fields
        this.title = ko.observable();
        this.description = ko.observable();
        this.cloudImage = ko.observable();
        this.count = ko.observable();
        this.hostnameTemplate = ko.observable();
        this.size = ko.observable();
        this.spotPrice = ko.observable();


        // One or the other here
        this.zone = ko.observable();
        this.subnetId = ko.observable();

        this.components = ko.observableArray([]);
        this.accessRules = ko.observableArray([]);
        this.volumes = ko.observableArray([]);

        if (needReload) {
            this.reload();
        } else {
            this._process(raw);
        }
    }

    HostDefinition.constructor = HostDefinition;

    HostDefinition.prototype._process = function (raw) {
        this.title(raw.title);
        this.description(raw.description);
        this.cloudImage(raw.cloud_image);
        this.count(raw.count);
        this.hostnameTemplate(raw.hostname_template);
        this.size(raw.size);
        this.zone(raw.zone);
        this.subnetId(raw.subnetId);
        this.spotPrice(raw.spot_price);

        var self = this;
        this.components(raw.formula_components.map(function (component) {
            return new FormulaComponent(component, self.parent, self);
        }));

        this.accessRules(raw.access_rules.map(function (rule) {
            return new AccessRule(rule, self.parent, self);
        }));

        this.volumes(raw.volumes.map(function (volume) {
            return new Volume(volume, self.parent, self);
        }));
    };

    return HostDefinition;
});