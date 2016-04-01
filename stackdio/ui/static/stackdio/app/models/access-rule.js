
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
    'knockout'
], function (ko) {
    'use strict';

    // Define the stack model.
    function AccessRule(raw, parent, hostDefinition) {
        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        this.hostDefinition = hostDefinition;

        // Editable fields
        this.rule = ko.observable();
        this.fromPort = ko.observable();
        this.toPort = ko.observable();

        this._process(raw);
    }

    AccessRule.constructor = AccessRule;

    AccessRule.prototype._process = function (raw) {
        this.rule(raw.rule);
        this.fromPort(raw.from_port);
        this.toPort(raw.to_port);
    };

    return AccessRule;
});