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

            self.addSecurityGroup = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                record.provider = self.selectedAccount.id;
                record.default = false;

                API.SecurityGroups.save(record)
                    .then(function () {
                        formutils.clearForm('securitygroup-form');
                        stores.SecurityGroups.push(record);
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.addDefaultSecurityGroup = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                // record.provider = self.selectedAccount.id;
                // record.default = true;

                var vefvdf = new models.Role().create({ id: 333, title: 'test', description: 'test'});
                stores.Roles.push(vefvdf);
                console.log(stores.Roles());

                // API.SecurityGroups.save(record)
                //     .then(function () {
                //         formutils.clearForm('default-securitygroup-form');
                //         stores.DefaultSecurityGroups.push(record);
                //     })
                //     .catch(function (error) {
                //         $("#alert-error").show();
                //     })
            };

            self.setForAccount = function (account) {
                API.SecurityGroups.loadByAccount(account)
                    .then(function () {
                        console.log('success');
                    });
                self.showDefaultGroupForm();
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

            self.showSecurityGroupForm = function (account) {
                self.selectedAccount = account;
                $("#securitygroup-form-container").dialog("open");
            }

            self.showDefaultGroupForm = function () {
                $("#default-securitygroup-form-container").dialog("open");
                $("#alert-default-security-groups").hide();
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
                width: 800,
                modal: false
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});