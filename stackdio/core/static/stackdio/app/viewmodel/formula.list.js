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
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'ladda',
    'util/formula',
    'store/Formulas',
    'api/api'
],
function (Q, ko, bootbox, $galaxy, alerts, Ladda, formulautils, FormulaStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedAccount = ko.observable();
        self.selectedProviderType = null;
        self.userCanModify = ko.observable(true);
        self.FormulaStore = FormulaStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'formula.list';
        self.templatePath = 'formula.list.html';
        self.domBindingId = '#formula-list';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);
        }

        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            $('span').popover('hide');
            FormulaStore.populate(true).then(function () {}).catch(function (err) { console.error(err); } ).done();
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.importFormula = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            API.Formulas.import(record.formula_url.value)
                .then(function () {
                    // Close the form and clear it out
                    self.closeFormulaForm();
                    formutils.clearForm('formula-form');

                    self.showSuccess();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })
        };

        self.updateFormula = formulautils.updateFormula;

        self.doUpdate = formulautils.doUpdate;

        self.share = function (formula) {
            API.Formulas.update(formula).then(function () {
                alerts.showMessage('#success', 'Formula successfully updated.', true);
                FormulaStore.populate(true).then(function () {}).catch(function (err) { console.error(err); } ).done();
            }).catch(function (error) {
                alerts.showMessage('#error', 'There was an error while updating your formula. ' + error, true, 4000);
            }).done();
        };

        self.popoverBuilder = function (formula) {
            if (formula.hasOwnProperty('components')) {
                return formula.components.map(function (item) {
                    var content = [];

                    content.push("<div class=\'dotted-border xxsmall-padding\'>");
                    content.push("<div>");
                    content.push(item.title);
                    content.push('</div>');
                    content.push("<div class='grey'>");
                    content.push(item.description);
                    content.push('</div>');
                    content.push('</div>');

                    return content.join('');
                }).join('');
            }
        };

        self.delete = function (formula) {
            bootbox.confirm("Please confirm that you want to delete this formula.", function (result) {
                if (result) {
                    API.Formulas.delete(formula).then(function () {
                        alerts.showMessage('#success', 'Formula successfully deleted.', true);
                        return FormulaStore.populate(true);
                    }).catch(function (error) {
                        alerts.showMessage('#error', 'There was an error while importing your formula. ' + error, true, 4000);
                    }).done();
                }
            });
        };

        self.loadFormula = function (obj, evt) {
            evt.preventDefault();
            var l = Ladda.create(evt.currentTarget);
            l.start();

            FormulaStore.populate(true).then(function() {
                l.stop();
            }).catch(function (err) {
                console.error(err);
                l.stop();
            }).done();
        };

        self.showImportForm = function () {
            $galaxy.transport('formula.import');
        };

        self.showFormulaDetail = function (formula) {
            $galaxy.transport({
                location: 'formula.detail',
                payload: {
                    formula: formula.id
                }
            });
        };
    };
    return new vm();
});
