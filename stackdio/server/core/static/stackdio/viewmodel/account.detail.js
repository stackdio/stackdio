define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/Regions',
    'api/api'
],
function (Q, ko, $galaxy, alerts, formutils, ProviderTypeStore, AccountStore, ProfileStore, RegionStore, API) {
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
        self.vpcId = ko.observable(null);
        self.$galaxy = $galaxy;

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.RegionStore = RegionStore;


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
            RegionStore.populate();

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
                $('#region').val('');
                $('#route53_domain').val('');
                $('#private_key_file').val('');
                self.vpcId(null);
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
                $('#region').val(account.region);
                $('#private_key_file').val(account.yaml);
                $('#private_key_file').attr('disabled', 'disabled');
                self.vpcId(account.vpc_id);

                self.currentMode('edit');
            } else if (provider_type && provider_type.hasOwnProperty('id')) {
                $('#private_key_file').removeAttr('disabled');                
                $('#account_provider').val(provider_type.id);
                self.currentMode('create');
            }
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
            account.region = record.region.value;
            account.account_id = record.account_id.value;
            account.access_key_id = record.access_key_id.value;
            account.secret_access_key = record.secret_access_key.value;
            account.keypair = record.keypair.value;
            account.route53_domain = record.route53_domain.value;
            account.private_key = record.private_key_file.value;
            account.vpc_id = record.vpc_id.value;

            API.Accounts.save(account).then(function (newAccount) {
                AccountStore.add(newAccount);
                $galaxy.transport({
                    location: 'account.securitygroup',
                    payload: {
                        account: newAccount.id
                    }
                });

                alerts.showMessage('#success', 'Provider account successfully created. You are strongly urged to specify at least one default security group for this provider that opens ports for SSH and Salt so that hosts can successfully be provisioned.', false);
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
            account.region = record.region.value;

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
