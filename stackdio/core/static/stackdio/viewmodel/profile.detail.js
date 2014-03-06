define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Accounts',
    'store/Profiles',
    'store/InstanceSizes',
    'api/api',
    'model/models'
],
function (Q, ko, $galaxy, formutils, AccountStore, ProfileStore, InstanceSizeStore, API, models) {
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
        self.saveAction = 'create';
        self.$galaxy = $galaxy;

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
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }

        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            AccountStore.populate().then(function () {
                return ProfileStore.populate();
            }).then(function () {
                return InstanceSizeStore.populate();
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
            var profile = null;

            if (data.hasOwnProperty('profile')) {
                profile = ProfileStore.collection().filter(function (p) {
                    return p.id === parseInt(data.profile, 10);
                })[0];

                profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                self.profileTitle(profile.title);
            } else {
                self.profileTitle('New Profile');
                self.saveAction = 'create';
            }

            self.selectedProfile(profile);

            if (profile && profile.hasOwnProperty('id')) {
                $('#profile_account').val(profile.account.id);
                $('#profile_title').val(profile.title);
                $('#profile_description').val(profile.description);
                $('#image_id').val(profile.image_id);
                $('#ssh_user').val(profile.ssh_user);
                $('#default_instance_size').val(profile.default_instance_size);

                self.saveAction = 'update';
            }
        };

        self.saveProfile = function (model, evt) {
            if (self.saveAction === 'create') {
                self.createProfile(model, evt);
            } else {
                self.updateProfile(model,evt);
            }
        };

        self.createProfile = function (model, evt) {
            var profile = formutils.collectFormFields(evt.target.form);

            profile.account = AccountStore.collection().filter(function (account) {
                return account.id === parseInt(profile.profile_account.value, 10);
            })[0];

            API.Profiles.save(profile).then(function (newProfile) {
                ProfileStore.add(new models.Profile().create(newProfile));
                $galaxy.transport('profile.list');
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
                $galaxy.transport('profile.list');
            });
        };

        self.deleteProfile = function (profile) {
            API.Profiles.delete(profile).catch(function (error) {
                self.showError(error);
            });
        };

        self.cancelChanges = function (model, evt) {
            formutils.clearForm('profile-form');
            $galaxy.transport('profile.list');
        };
    };
    return new vm();
});
