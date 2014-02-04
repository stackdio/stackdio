define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/stores',
    'api/api'
],
function (Q, ko, base, _O_, stores, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stores = stores;
        self.selectedAccount = ko.observable();
        self.selectedProviderType = null;
        self.userCanModify = ko.observable(true);

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'formula.list';
        self.templatePath = 'formulas.html';
        self.domBindingId = '#formula-list';
        self.autoLoad = false;
        self.defaultView = false;

        try {
            self.$66.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.importFormula = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            API.Formulae.import(record.formula_url.value)
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
