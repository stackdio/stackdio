define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/stores',
    'api/api'
],
function (Q, ko, base, _O_, formutils, stores, API) {
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
        self.id = 'profile.detail';
        self.templatePath = 'profile.html';
        self.domBindingId = '#profile-detail';

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
            formutils.clearForm('profile-form');
            if (stores.Accounts().length === 0) {
                [API.Accounts.load, API.Profiles.load].reduce(function (loadData, next) {
                    return loadData.then(next);
                }, Q([])).then(function () {
                });
            }
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */
        self.saveProfile = function (model, evt) {
            var profile = formutils.collectFormFields(evt.target.form);
            profile.account = self.selectedAccount();

            console.log(profile);

            API.Profiles.save(profile).then(function (newProfile) {
                console.log(newProfile);
                stores.AccountProfiles.push(newProfile);
                formutils.clearForm('profile-form');
                self.showSuccess();
            });
        };

        self.deleteProfile = function (profile) {
            API.Profiles.delete(profile).catch(function (error) {
                self.showError(error);
            });
        };
    };

    vm.prototype = new base();
    return new vm();
});
