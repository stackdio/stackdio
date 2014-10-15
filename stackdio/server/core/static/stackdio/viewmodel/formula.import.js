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
    'q',
    'settings',
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'api/api'
],
function (Q, settings, ko, bootbox, $galaxy, alerts, formutils, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */

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

        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.cancelChanges = function() {
            formutils.clearForm('formula-form');
            $galaxy.transport('formula.list');
        };

        self.superuser = function() {
            console.log('superuser: '+settings.superuser);
            return settings.superuser;
        };

        self.importFormula = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            API.Formulas.import(record.formula_url.value, record.git_username.value, record.git_password.value)
                .then(function () {
                    alerts.showMessage('#success', 'Formula has been submitted for import. Depending on the size of the formula repository it may take some time to complete.', true);

                    // clear form and head back to the list
                    self.cancelChanges();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })

            if (record.global_orch.value) {
                API.Formulas.import_global(record.formula_url.value, record.git_username.value, record.git_password.value)
                .then(function () {
                    alerts.showMessage('#success', 'Formula has been submitted for import into the global orchestration space. Depending on the size of the formula repository it may take some time to complete.', true);

                    // clear form and head back to the list
                    self.cancelChanges();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })
            }
        };

    };
    return new vm();
});
