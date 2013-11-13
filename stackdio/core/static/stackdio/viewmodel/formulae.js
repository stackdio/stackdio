define(["knockout",
        "q", 
        "util/form",
        "viewmodel/abstract",
        "model/models",
        "store/stores",
        "api/api"], 
    function (ko, Q, formutils, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;

            self.selectedAccount = ko.observable();
            self.selectedProviderType = null;
            self.userCanModify = ko.observable(true);

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

            self.showFormulaForm = function () {
                $( "#formula-form-container" ).dialog("open");
            }

            self.closeFormulaForm = function () {
                $("#formula-form-container").dialog("close");
            }

            /*
             *  ==================================================================================
             *  D I A L O G   E L E M E N T S
             *  ==================================================================================
             */
            $("#formula-form-container").dialog({
                autoOpen: false,
                position: [window.innerWidth/2 - 250, 200],
                width: 500,
                modal: false
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});