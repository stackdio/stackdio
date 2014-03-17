define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'store/Formulas',
    'api/api'
],
function (Q, ko, $galaxy, alerts, formutils, FormulaStore, API) {
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
        self.id = 'formula.detail';
        self.templatePath = 'formula.html';
        self.domBindingId = '#formula-detail';

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

        self.cancelChanges = function () {
            $galaxy.transport('formula.list');
        };

        self.importFormula = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            formutils.clearForm('formula-form');
            API.Formulas.import(record.formula_url.value).then(function () {
                alerts.showMessage('#success', 'Formula is now being imported and should be complete in a few seconds.', true, 3000, $galaxy.transport('formula.list'));
            }).catch(function (error) {
                alerts.showMessage('#error', 'There was an error while importing your formula. ' + error, true, 4000, $galaxy.transport('formula.list'));
            }).done();
        };
    };
    return new vm();
});
