define(["knockout",
        "lib/q", 
        "app/util/form",
        "app/viewmodel/abstract",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, Q, formutils, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;

            self.selectedAccount = ko.observable();
            self.selectedProviderType = null;
            self.userCanModify = ko.observable(true);

            self.addAccount = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                record.providerType = self.selectedProviderType;

                API.Accounts.save(record)
                    .then(function (account) {
                        // Close the form and clear it out
                        $("#accounts-form-container").dialog("close");
                        formutils.clearForm('account-form');

                        // Query user if default security groups should be chosen for account
                        self.showMessage("#alert-default-security-groups", "", false);

                        // Set the saved account as the "selected" account for display in the default security group dialog
                        self.selectedAccount = account;
                        $('#default_groups_account_title').val(account.title);

                        // self.showSuccess();
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.deleteAccount = function (account) {
                API.Accounts.delete(account)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error);
                    });
            };

            self.loadAccounts = function () {
                return API.Accounts.load();
            };

            self.showAccountForm = function (type) {
                self.selectedProviderType = type;
                $( "#accounts-form-container" ).dialog("open");
            }

            self.closeAccountForm = function (type) {
                self.selectedProviderType = type;
                $("#accounts-form-container").dialog("close");
            }

            /*
             *  ==================================================================================
             *  D I A L O G   E L E M E N T S
             *  ==================================================================================
             */
            $("#accounts-form-container").dialog({
                autoOpen: false,
                width: 650,
                modal: false
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});