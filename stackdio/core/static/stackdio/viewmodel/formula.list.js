define([
    'q', 
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'util/ladda',
    'store/Formulas',
    'api/api'
],
function (Q, ko, bootbox, $galaxy, alerts, Ladda, FormulaStore, API) {
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

        self.updateFormula = function (formula) {
            if (formula.private_git_repo && !formula.git_password_stored) {
                bootbox.dialog({
                    title: "Enter your git password:",
                    message: '<form class="bootbox-form"><input class="bootbox-input bootbox-input-text form-control" autocomplete="off" type="password" id="git_password_for_update"></form>',
                    buttons: {
                        cancel: {
                            label: "Cancel",
                            className: "btn-default",
                            callback: function () {
                                // Do nothing
                            }
                        },
                        success: {
                            label: "OK",
                            className: "btn-primary",
                            callback: function () {
                                git_password = $('#git_password_for_update').val();
                                self.doUpdate(formula, git_password);
                            }
                        }
                    }
                });
            } else {
                self.doUpdate(formula, '');
            }
        };

        self.doUpdate = function (formula, git_password) {
            API.Formulas.updateFromRepo(formula, git_password).then(function () {
                alerts.showMessage('#success', 'Formula successfully updated from repository.', true);
                FormulaStore.populate(true).then(function () {}).catch(function (err) { console.error(err); } ).done();
            }).catch(function (error) {
                alerts.showMessage('#error', 'There was an error while updating your formula. ' + error, true, 4000);
            }).done();
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

        self.remove_password = function (formula) {
            bootbox.confirm("Please confirm that you want to remove the password from this formula.", function (result) {
                if (result) {
                    API.Formulas.removePassword(formula).then(function () {
                        alerts.showMessage('#success', 'Git password successfully removed.', true);
                        self.loadFormula();
                    }).catch(function (error) {
                        alerts.showMessage('#error', 'Could not delete the password. ' + error, true, 4000);
                    }).done()
                }
            });
        }

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
