define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/Accounts',
    'store/Profiles',
    'store/InstanceSizes',
    'api/api'
],
function (Q, ko, base, _O_, formutils, AccountStore, ProfileStore, InstanceSizeStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedAccount = ko.observable(null);
        self.selectedProfile = ko.observable(null);
        self.userCanModify = ko.observable(true);
        self.profileTitle = ko.observable();
        self.saveAction = self.createProfile;

        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.InstanceSizeStore = InstanceSizeStore;

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
        _O_.subscribe('profile.detail.rendered', function (data) {
            AccountStore.populate().then(function () {
                return ProfileStore.populate();
            }).then(function () {
                return InstanceSizeStore.populate();
            }).then(function () {            
                self.init(data);
            });



            // if (stores.Accounts().length === 0) {
            //     [API.Accounts.load, API.Profiles.load].reduce(function (loadData, next) {
            //         return loadData.then(next);
            //     }, Q([])).then(function () {
            //         self.init(data);
            //     });
            // } else {
            //     self.init(data);
            // }
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var profile = null;

            if (data.hasOwnProperty('profile')) {
                profile = ProfileStore.collection().filter(function (p) {
                    return p.id === parseInt(data.profile, 10);
                })[0];

                profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                self.profileTitle(profile.title);
            } else {
                self.profileTitle('New Profile');
            }

            self.selectedProfile(profile);

            if (profile && profile.hasOwnProperty('id')) {
                $('#profile_account').val(profile.account.id);
                $('#profile_title').val(profile.title);
                $('#profile_description').val(profile.description);
                $('#image_id').val(profile.image_id);
                $('#ssh_user').val(profile.ssh_user);
                $('#default_instance_size').val(profile.default_instance_size);

                self.saveAction = self.updateProfile;
            }
        };

        self.saveProfile = function (model, evt) {
            self.saveAction(model, evt);
        };

        self.createProfile = function (model, evt) {
            var profile = formutils.collectFormFields(evt.target.form);

            profile.account = stores.Accounts().map(function (account) {
                if (account.id === parseInt(profile.profile_account.value, 10)) {
                    return account;
                }
            })[0];

            API.Profiles.save(profile).then(function (newProfile) {
                stores.Profiles.push(newProfile);
                self.navigate({ view: 'profile.list' });
            });
        };

        self.updateProfile = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var profile = {};

            // Update property values with those submitted from form
            profile.id = self.selectedProfile().id;
            profile.url = self.selectedProfile().url;
            profile.cloud_provider = self.selectedProfile().cloud_provider;
            profile.title = record.profile_title.value;
            profile.description = record.profile_description.value;
            profile.image_id = record.image_id.value;
            profile.ssh_user = record.ssh_user.value;
            profile.default_instance_size = record.default_instance_size.value;

            // PUT the update, and on success, replace the current item in the store with new one
            API.Profiles.update(profile).then(function (newProfile) {
                self.ProfileStore.remove(self.selectedProfile());
                self.ProfileStore.add(newProfile);
                formutils.clearForm('profile-form');
                self.navigate({ view: 'profile.list' });
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
