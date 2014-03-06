define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/Formulas',
    'api/api'
],
function (Q, ko, base, _O_, FormulaStore, API) {
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
        self.templatePath = 'formulas.html';
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
        self.$66.news.subscribe('formula.list.rendered', function (data) {
            FormulaStore.populate().then(function () {
                console.log(FormulaStore.collection());
            });
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
            return API.Formulas.delete(formula);
        };

        self.loadFormula = function () {
            return API.Formulae.load();
        };

        self.showImportForm = function () {
            $galaxy.transport({ view: 'formula.detail' });
        };

    };

    vm.prototype = new base();
    return new vm();
});
