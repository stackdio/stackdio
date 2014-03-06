define([
    'q', 
    'knockout',
    'util/galaxy',
    'store/Accounts',
    'store/Profiles',
    'api/api'
],
function (Q, ko, $galaxy, AccountStore, ProfileStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedAccount = ko.observable(null);
        self.userCanModify = ko.observable(true);
        self.$galaxy = $galaxy;
        self.isSuperUser = stackdio.settings.superuser;

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
            self.EnhancedProfileStore.removeAll();

            AccountStore.populate().then(function () {
                return ProfileStore.populate();
            }).then(function () {
                self.init(data);
            }).catch(function (error) {
                console.log(error)
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */
        self.init = function (data) {
            self.EnhancedProfileStore.removeAll();

            if (data && data.hasOwnProperty('account')) {
                ProfileStore.collection().forEach(function (profile) {
                    profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                    if (profile.account.id === parseInt(data.account, 10)) {
                        self.EnhancedProfileStore.push(profile);
                    }
                });
            } else {
                ProfileStore.collection().forEach(function (profile) {
                    if (!profile.hasOwnProperty('image_id')) {
                        profile.image_id = 'n/a';
                    }
                    profile.account = _.findWhere(AccountStore.collection(), { id: profile.cloud_provider });
                    self.EnhancedProfileStore.push(profile);
                });
            }

        };

        self.newProfile = function () {
            $galaxy.transport('profile.detail');
        };

        self.deleteProfile = function (profile) {
            API.Profiles.delete(profile).then(function () {
                ProfileStore.removeById(profile.id);
                self.init();
            })
            .catch(function (error) {
                self.showError(error);
            });
        };

        self.viewProfile = function (profile) {
            $galaxy.transport({
                location: 'profile.detail',
                payload: {
                    profile: profile.id
                }
            });
        };
    };
    return new vm();
});
