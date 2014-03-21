define([
    'q', 
    'knockout',
    'bootbox',
    'util/galaxy',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'api/api'
],
function (Q, ko, bootbox, $galaxy, ProviderTypeStore, AccountStore, ProfileStore, API) {
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
        self.isSuperUser = stackdio.settings.superuser;
        self.$galaxy = $galaxy;

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
                account.profile_count = ProfileStore.collection().filter(function (profile) {
                    return profile.cloud_provider === account.id;
                }).length;

                self.EnhancedAccountStore.push(account);
            });
        };

        self.deleteAccount = function (account) {
            bootbox.confirm("Please confirm that you want to delete this provider.", function (result) {
                if (result) {
                    API.Accounts.delete(account).then(function () {
                        AccountStore.removeById(account.id);
                        self.init();
                    })
                    .catch(function (error) {
                        self.showError(error);
                    });
                }
            });
        };

        self.listProfiles = function (account) {
            $galaxy.transport({ location: 'profile.list', payload: { account: account.id } });
        };

        self.createAccount = function (providerType) {
            $galaxy.transport({
                location: 'account.detail',
                payload: {
                    type: providerType.id
                }
            });
        };

        self.editAccount = function (account) {
            $galaxy.transport({ location: 'account.detail', payload: { account: account.id } });
        };

        self.editSecurityGroups = function (account) {
            $galaxy.transport({ location: 'account.securitygroup', payload: { account: account.id } });
        };
    };
    return new vm();
});
