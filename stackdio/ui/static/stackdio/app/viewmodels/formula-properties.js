
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
    'bootbox',
    'models/formula'
], function($, ko, bootbox, Formula) {
    'use strict';
    return function () {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Formulas',
                href: '/formulas/'
            },
            {
                active: false,
                title: window.stackdio.formulaTitle,
                href: '/formulas/' + window.stackdio.formulaId + '/'
            },
            {
                active: true,
                title: 'Default Properties'
            }
        ];

        self.validProperties = true;

        self.formula = new Formula(window.stackdio.formulaId);

        self.propertiesJSON = ko.pureComputed({
            read: function () {
                return ko.toJSON(self.formula.properties(), null, 3);
            },
            write: function (value) {
                try {
                    self.formula.properties(JSON.parse(value));
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
            self.formula.saveProperties();
        };

        self.reload = function () {
            self.formula.loadProperties();
        };

        self.reload();
    }
});