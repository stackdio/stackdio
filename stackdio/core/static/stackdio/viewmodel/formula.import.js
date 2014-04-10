define([
    'q', 
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'store/Formulas',
    'api/api'
],
function (Q, ko, bootbox, $galaxy, alerts, formutils, FormulaStore, API) {
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
                    alerts.showMessage('#success', 'Formula has been submitted for import. Depending on the size of the formula repository it may take some time to complete.', true);
                    $galaxy.transport('formula.list');
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })
        };

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

        self.loadFormula = function () {
            return API.Formulae.load();
        };

        self.showImportForm = function () {
            $galaxy.transport('formula');
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
