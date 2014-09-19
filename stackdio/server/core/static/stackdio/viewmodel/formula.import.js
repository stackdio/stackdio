define([
    'q',
    'settings',
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'api/api'
],
function (Q, settings, ko, bootbox, $galaxy, alerts, formutils, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */

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
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.cancelChanges = function() {
            formutils.clearForm('formula-form');
            $galaxy.transport('formula.list');
        };

        self.superuser = function() {
            console.log('superuser: '+settings.superuser);
            return settings.superuser;
        };

        self.importFormula = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            API.Formulas.import(record.formula_url.value, record.git_username.value, record.git_password.value)
                .then(function () {
                    alerts.showMessage('#success', 'Formula has been submitted for import. Depending on the size of the formula repository it may take some time to complete.', true);

                    // clear form and head back to the list
                    self.cancelChanges();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })

            if (record.global_orch.value) {
                API.Formulas.import_global(record.formula_url.value, record.git_username.value, record.git_password.value)
                .then(function () {
                    alerts.showMessage('#success', 'Formula has been submitted for import into the global orchestration space. Depending on the size of the formula repository it may take some time to complete.', true);

                    // clear form and head back to the list
                    self.cancelChanges();
                })
                .catch(function (error) {
                    self.showError(error, 15000);
                })
            }
        };

    };
    return new vm();
});
