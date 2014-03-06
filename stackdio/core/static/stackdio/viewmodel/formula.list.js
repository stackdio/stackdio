define([
    'q', 
    'knockout',
    'util/galaxy',
    'store/Formulas',
    'api/api'
],
function (Q, ko, $galaxy, FormulaStore, API) {
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
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            FormulaStore.populate().then(function () {}).catch(function (err) { console.error(err); } ).done();
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
            API.Formulas.update(formula).then(function () {
                FormulaStore.populate(true).then(function () {}).catch(function (err) { console.error(err); } ).done();
            });
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
            $galaxy.transport('formula.detail');
        };
    };
    return new vm();
});
