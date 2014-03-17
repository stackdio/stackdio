define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/Zones',
    'api/api'
],
function (Q, ko, $galaxy, formutils, ProviderTypeStore, AccountStore, ProfileStore, ZoneStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedAccount = ko.observable(null);
        self.selectedProviderType = ko.observable(null);
        self.accountTitle = ko.observable(null);
        self.currentMode = ko.observable('create');
        self.$galaxy = $galaxy;

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.ZoneStore = ZoneStore;


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'account.detail';
        self.templatePath = 'account.html';
        self.domBindingId = '#account-detail';

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
            ZoneStore.populate();

            ProviderTypeStore.populate().then(function () {
                return AccountStore.populate();
            }).then(function () {
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
            var account = null;
            var provider_type = null;

            if (data.hasOwnProperty('account')) {
                account = AccountStore.collection().filter(function (a) {
                    return a.id === parseInt(data.account, 10);
                })[0];

                self.accountTitle(account.title);
                self.selectedAccount(account);
            } else {
                self.accountTitle('New Account');

                $('#account_title').val('');
                $('#account_description').val('');
                $('#account_id').val('');
                $('#access_key_id').val('');
                $('#secret_access_key').val('');
                $('#keypair').val('');
                $('#default_availability_zone').val('');
                $('#route53_domain').val('');
                $('#private_key_file').val('');
            }

            if (data.hasOwnProperty('type')) {
                provider_type = ProviderTypeStore.collection().filter(function (a) {
                    return a.id === parseInt(data.type, 10);
                })[0];

                self.selectedProviderType(provider_type);
            }

            if (account && account.hasOwnProperty('id')) {
                $('#account_provider').val(account.provider_type);
                $('#account_title').val(account.title);
                $('#account_description').val(account.description);
                $('#account_id').val(account.account_id);
                $('#default_availability_zone').val(account.default_availability_zone);
                $('#private_key_file').val(account.yaml);
                $('#private_key_file').attr('disabled', 'disabled');

                self.currentMode('edit');
            } else if (provider_type && provider_type.hasOwnProperty('id')) {
                $('#private_key_file').removeAttr('disabled');                
                $('#account_provider').val(provider_type.id);
                self.currentMode('create');
            }

            console.log('self.currentMode',self.currentMode());
        };

        self.saveAccount = function (model, evt) {
            if (self.currentMode() === 'create') {
                self.createAccount(model, evt);
            } else {
                self.updateAccount(model, evt);
            }
        };

        self.createAccount = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form), account = {};

            account.provider_type = record.account_provider.value;
            account.title = record.account_title.value;
            account.description = record.account_description.value;
            account.default_availability_zone = record.default_availability_zone.value;
            account.account_id = record.account_id.value;
            account.access_key_id = record.access_key_id.value;
            account.secret_access_key = record.secret_access_key.value;
            account.keypair = record.keypair.value;
            account.route53_domain = record.route53_domain.value;
            account.private_key = record.private_key_file.value;

            API.Accounts.save(account).then(function (newAccount) {
                AccountStore.add(newAccount);
                $galaxy.transport('account.list');
            });
        };

        self.updateAccount = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var account = {};

            // Update property values with those submitted from form
            account.id = self.selectedAccount().id;
            account.url = self.selectedAccount().url;
            account.provider_type = record.account_provider.value;
            account.title = record.account_title.value;
            account.description = record.account_description.value;
            account.default_availability_zone = record.default_availability_zone.value;

            // PATCH the update, and on success, replace the current item in the store with new one
            API.Accounts.update(account).then(function () {
                $galaxy.transport('account.list');
            }).catch(function (err) {
                console.log(err);
            });
        };

        self.cancelChanges = function (model, evt) {
            $galaxy.transport('account.list');
        };
    };
    return new vm();
});
