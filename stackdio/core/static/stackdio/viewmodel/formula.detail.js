define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Formulas',
    'api/api'
],
function (Q, ko, $galaxy, formutils, FormulaStore, API) {
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

            API.Formulas.import(record.formula_url.value).then(function () {
                formutils.clearForm('formula-form');
                $galaxy.transport('formula.list');
            })
            .catch(function (error) {
                console.error(error);
            }).done();
        };
    };
    return new vm();
});
