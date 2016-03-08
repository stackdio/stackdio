
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
    function FormulaComponent(raw, parent, hostDefinition) {
        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;

        this.hostDefinition = hostDefinition;

        // Editable fields
        this.formula = ko.observable();
        this.title = ko.observable();
        this.description = ko.observable();
        this.slsPath = ko.observable();
        this.order = ko.observable();

        this._process(raw);
    }

    FormulaComponent.constructor = FormulaComponent;

    FormulaComponent.prototype._process = function (raw) {
        this.formula(raw.formula);
        this.title(raw.title);
        this.description(raw.description);
        this.slsPath(raw.sls_path);
        this.order(raw.order);
    };

    return FormulaComponent;
});