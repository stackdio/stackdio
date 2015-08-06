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
    '../../bower_components/q/q',
    'settings',
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'api/api'
],
function (Q, settings, ko, bootbox, $galaxy, alerts, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */

        self.accessToken = ko.observable();
        self.uri = ko.observable();
        self.username = ko.observable();
        self.password = ko.observable();
        self.globalOrch = ko.observable();

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'formula.import';
        self.templatePath = 'formula.import.html';
        self.domBindingId = '#formula-import';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }

        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            self.init(data);
        });

        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.init = function(data) {
            self.accessToken(false);
            self.uri('');
            self.username('');
            self.password('');
            self.globalOrch(false);
        };

        self.cancelChanges = function() {
            $galaxy.transport('formula.list');
        };

        self.usernameText = ko.computed(function() {
            if (self.accessToken()) {
                return 'Access token';
            } else {
                return 'Git username';
            }
        });

        self.superuser = function() {
            return settings.superuser;
        };

        self.importFormula = function (model, evt) {

            API.Formulas.import(self.uri(), self.username(), self.password(), self.accessToken())
                .then(function () {
                    alerts.showMessage('#success', 'Formula has been submitted for import. Depending on the size of the formula repository it may take some time to complete.', true);

                    // clear form and head back to the list
                    self.cancelChanges();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                });

            if (self.globalOrch()) {
                API.Formulas.import_global(self.uri(), self.username(), self.password(), self.accessToken())
                .then(function () {
                    alerts.showMessage('#success', 'Formula has been submitted for import into the global orchestration space. Depending on the size of the formula repository it may take some time to complete.', true);

                    // clear form and head back to the list
                    self.cancelChanges();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                });
            }
        };

    };
    return new vm();
});
