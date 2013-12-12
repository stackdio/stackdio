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
            self.selectedProfile = null;
            self.selectedAccount = null;

            self.addBlueprint = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);

                record.title = record.account_title;
                record.description = record.account_description;
                record.providerType = self.selectedProviderType.id;

                API.Accounts.save(record)
                    .then(function (account) {
                        // Close the form and clear it out
                        $("#accounts-form-container").dialog("close");
                        formutils.clearForm('account-form');

                        // Query user if default security groups should be chosen for account
                        self.showMessage("#alert-default-security-groups", "", false);

                        // Set the saved account as the "selected" account for display in the default security group dialog
                        self.selectedAccount(account);
                        $('#default_groups_account_title').val(account.title);

                        // self.showSuccess();
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.deleteBlueprint = function (account) {
                API.Accounts.delete(account)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error);
                    });
            };

            self.loadBlueprint = function () {
                return API.Accounts.load();
            };

            self.showBlueprintForm = function () {
                $("#blueprint-form-container").dialog("open");
            }

            self.closeBlueprintForm = function (type) {
                formutils.clearForm('blueprint-form');
                $("#blueprint-form-container").dialog("close");
            }

            self.showHostForm = function (profile) {
                self.selectedProfile = profile;
                self.selectedAccount = profile.account;

                // Choose the default instance size assigned to the chosen profile
                $('#host_instance_size').selectpicker('val', profile.default_instance_size);

                // Choose the default zone assigned to the chosen account
                $('#availability_zone').selectpicker('val', self.selectedAccount.default_availability_zone);

                $( "#host-form-container" ).dialog("open");
            };

            self.closeHostForm = function () {
                formutils.clearForm('blueprint-host-form');
                $( "#host-form-container" ).dialog("close");
            };

            /*
             *  ==================================================================================
             *  D I A L O G   E L E M E N T S
             *  ==================================================================================
             */
            $("#blueprint-form-container").dialog({
                autoOpen: false,
                width: window.innerWidth - 225,
                height: 500,
                position: [200,50],
                modal: false
            });

            $("#host-form-container").dialog({
                position: [(window.innerWidth / 2) - 275,50],
                autoOpen: false,
                width: 600,
                modal: true
            });


            $("#host-access-rule-container").dialog({
                autoOpen: false,
                width: 500,
                modal: true
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});