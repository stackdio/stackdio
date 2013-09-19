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
                record.provider_id = self.selectedAccount.id;
                record.is_default = false;

                API.SecurityGroups.save(record)
                    .then(function () {
                        formutils.clearForm('securitygroup-form');
                        stores.SecurityGroups.push(record);
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.addDefaultSecurityGroup = function (name, evt) {
                var record = {};
                record.name = name;
                record.cloud_provider = self.selectedAccount.id;
                record.is_default = true;
                record.description = "";

                API.SecurityGroups.save(record)
                    .then(function () {
                        formutils.clearForm('default-securitygroup-form');
                        stores.DefaultSecurityGroups.push(record);
                        $('#default_group_list').append('<span style="margin: 0 5px;" class="label label-inverse">'+ record.name +'</span>');
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.setForAccount = function (account) {
                self.selectedAccount = account;

                $('#default_group_list').empty();

                API.SecurityGroups.loadByAccount(account)
                    .then(function () {
                        // For each security group that is default, add a label styled span element in the UI
                        _.each(stores.SecurityGroups(), function (g) {
                            if (g.is_default && g.provider_id === account.id) {
                                $('#default_group_list').append('<span style="margin: 0 5px;" class="label label-inverse"><span class="iconic-x"></span> '+ g.name +'</span>');
                            }
                        })
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