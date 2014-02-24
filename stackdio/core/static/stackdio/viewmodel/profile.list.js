define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/Accounts',
    'store/Profiles',
    'api/api'
],
function (Q, ko, base, _O_, AccountStore, ProfileStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedAccount = ko.observable(null);
        self.userCanModify = ko.observable(true);

        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.EnhancedProfileStore = ko.observableArray();

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
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        _O_.subscribe('profile.list.rendered', function (data) {
            self.EnhancedProfileStore.removeAll();

            AccountStore.populate().then(function () {
                return ProfileStore.populate();
            }).then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */
        self.init = function (data) {
            self.EnhancedProfileStore.removeAll();

            if (data.hasOwnProperty('account')) {
                ProfileStore.collection().forEach(function (profile) {
                    profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                    if (profile.account.id === parseInt(data.account, 10)) {
                        self.EnhancedProfileStore.push(profile);
                    }
                });
            } else {
                ProfileStore.collection().forEach(function (profile) {
                    profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                    self.EnhancedProfileStore.push(profile);
                });
            }
        };

        self.newProfile = function () {
            self.navigate({ view: 'profile.detail' });
        };

        self.addProfile = function (model, evt) {
            var profile = formutils.collectFormFields(evt.target.form);
            profile.account = self.selectedAccount();

            API.Profiles.save(profile)
                .then(function (newProfile) {
                    console.log(newProfile);
                    stores.AccountProfiles.push(newProfile);
                    formutils.clearForm('profile-form');
                    self.showSuccess();
                });
        };

        self.deleteProfile = function (profile) {
            API.Profiles.delete(profile)
                .then(self.showSuccess)
                .catch(function (error) {
                    self.showError(error);
                });
        };

        self.viewProfile = function (profile) {
            console.log('profile',profile);
            self.navigate({ view: 'profile.detail', data: { profile: profile.id } });
        };

        self.listProfiles = function (data) {
            stores.AccountProfiles.removeAll();

            if (data && data.hasOwnProperty('account')) {
                stores.Profiles().forEach(function (profile) {
                    if (profile.account.id === parseInt(data.account, 10)) {
                        stores.AccountProfiles.push(profile);
                    }
                });                
            } else {
                stores.Profiles().forEach(function (profile) {
                    stores.AccountProfiles.push(profile);
                });
            }
        };
    };

    vm.prototype = new base();
    return new vm();
});
