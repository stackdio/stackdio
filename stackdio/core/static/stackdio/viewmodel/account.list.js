define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/stores',
    'api/api'
],
function (Q, ko, base, _O_, stores, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stores = stores;
        self.selectedAccount = ko.observable(null);
        self.selectedProviderType = null;
        self.userCanModify = ko.observable(true);

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'account.list';
        self.templatePath = 'accounts.html';
        self.domBindingId = '#account-list';

        try {
            self.$66.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */
        self.accountProfileLink = function (accountId) {
            var profileCount = _.filter(stores.Profiles(), function (profile) {
                return profile.account.id === accountId;
            }).length;

            if (profileCount === 0) {
                return 'Add a profile';
            } else {
                return 'View ' + _.filter(stores.Profiles(), function (profile) {return profile.account.id === accountId; }).length + ' profiles';
            }
        };

        self.addAccount = function (model, evt) {
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

        self.listProfiles = function (account) {
            self.navigate({ view: 'profile.list', data: { account: account } });
        };

        self.editSecurityGroups = function () {
            return true;
        };

    };

    vm.prototype = new base();
    return new vm();
});
