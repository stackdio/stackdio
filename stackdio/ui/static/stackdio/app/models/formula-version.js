
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

    // Define the formula version model.
    function FormulaVersion(raw, parent) {
        // Save the raw in order to get things like URLs
        this.raw = raw;

        // Save the parent VM
        this.parent = parent;


        // Editable fields
        this.formula = ko.observable();
        this.version = ko.observable();

        this.formulaHtmlId = ko.observable();

        this._process(raw);
    }

    FormulaVersion.constructor = FormulaVersion;


    FormulaVersion.prototype._process = function (raw) {
        this.formula(raw.formula);
        this.version(raw.version);
        // This is necessary because html ids can't contain slashes, colons, or periods.
        // We use the formula URI as an html ID at points.
        this.formulaHtmlId(raw.formula.replace(/\//g, '-').replace(/:/g, '-').replace(/\./g, '-').replace(/@/g, '-'));
    };

    return FormulaVersion;
});