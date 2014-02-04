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
        self.userCanModify = ko.observable(true);

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'profile.list';
        self.templatePath = 'profiles.html';
        self.domBindingId = '#profile-list';

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
        self.addProfile = function (model, evt) {
            var profile = formutils.collectFormFields(evt.target.form);
            profile.account = self.selectedAccount();

            API.Profiles.save(profile)
                .then(function (newProfile) {
                    console.log(newProfile);
                    stores.AccountProfiles.push(newProfile);
                    formutils.clearForm('profile-form');
                    self.showSuccess();
                    self.closeProfileForm();
                });
        };

        self.deleteProfile = function (profile) {
            API.Profiles.delete(profile)
                .then(self.showSuccess)
                .catch(function (error) {
                    self.showError(error);
                });
        };

        self.listProfiles = function (account) {
            self.selectedAccount(account);
            stores.AccountProfiles.removeAll();

            _.each(stores.Profiles(), function (profile) {
                if (profile.account.id === account.id) {
                    stores.AccountProfiles.push(profile);
                }
            });

            if (stores.AccountProfiles().length === 0) {
                self.showProfileForm(account);
            }
        };
    };

    vm.prototype = new base();
    return new vm();
});
