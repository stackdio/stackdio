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

            self.selectedAccount = null;
            self.selectedProviderType = null;
            self.userCanModify = ko.observable(true);

            self.addSecurityGroup = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                record.providerType = self.selectedProviderType;

                API.Accounts.save(record)
                    .then(function () {
                        $("#accounts-form-container").dialog("close");
                        formutils.clearForm('account-form');
                        self.showSuccess();
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.deleteSecurityGroup = function (group) {
                API.SecurityGroup.delete(group)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error);
                    });
            };

            self.loadSecurityGroups = function () {
                return API.SecurityGroups.load();
            };

            self.showSecurityGroupForm = function (type) {
                self.selectedProviderType = type;
                $("#securitygroup-form-container").dialog("open");
            }

            self.showDefaultGroupForm = function () {
                $("#default-securitygroup-form-container").dialog("open");
            }

            self.closeSecurityGroupForm = function (type) {
                $("#securitygroup-form-container").dialog("close");
            }

            /*
             *  ==================================================================================
             *  D I A L O G   E L E M E N T S
             *  ==================================================================================
             */
            $("#securitygroup-form-container").dialog({
                autoOpen: false,
                width: 400,
                modal: false
            });

            $("#default-securitygroup-form-container").dialog({
                autoOpen: false,
                width: 600,
                modal: false
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});