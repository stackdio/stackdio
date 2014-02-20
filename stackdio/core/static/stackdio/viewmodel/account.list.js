define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'api/api'
],
function (Q, ko, base, _O_, ProviderTypeStore, AccountStore, ProfileStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedAccount = ko.observable(null);
        self.selectedProviderType = null;
        self.userCanModify = ko.observable(true);

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.EnhancedAccountStore = ko.observableArray();

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
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        _O_.subscribe('account.list.rendered', function (data) {
            ProviderTypeStore.populate().then(function () {
                return AccountStore.populate();
            }).then(function () {
                return ProfileStore.populate();
            }).then(function () {
                self.init();
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */
        self.init = function (data) {
            self.EnhancedAccountStore.removeAll();
            
            AccountStore.collection().forEach(function (account) {
                account.profile_count = ProfileStore.collection().map(function (profile) {
                    return profile.cloud_provider === account.id;
                }).length;

                self.EnhancedAccountStore.push(account);
            });
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

        self.listProfiles = function (account) {
            self.navigate({ view: 'profile.list', data: { account: account.id } });
        };

        self.editAccount = function (account) {
            self.navigate({ view: 'account.detail', data: { account: account.id } });
        };

        self.editSecurityGroups = function () {
            return true;
        };

    };

    vm.prototype = new base();
    return new vm();
});
