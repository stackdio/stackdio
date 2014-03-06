define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/form',
    'store/Formulas',
    'api/api'
],
function (Q, ko, base, formutils, FormulaStore, API) {
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
            $galaxy.transport({ view: 'formula.list' });
        };

        self.importFormula = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            API.Formulas.import(record.formula_url.value)
                .then(function () {
                    formutils.clearForm('formula-form');
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })
        };

        self.share = function (formula) {
            return API.Formulae.update(formula);
        };

        self.popoverBuilder = function (formula) { 
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
        };

        self.showDetails = function (formula) {
            console.log(formula);
        };

        self.delete = function (formula) {
            return API.Formulae.delete(formula);
        };

        self.loadFormula = function () {
            return API.Formulae.load();
        };
    };

    vm.prototype = new base();
    return new vm();
});
