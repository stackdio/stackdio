define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/Zones',
    'api/api'
],
function (Q, ko, base, _O_, formutils, ProviderTypeStore, AccountStore, ProfileStore, ZoneStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedAccount = ko.observable(null);
        self.accountTitle = ko.observable(null);
        self.saveAction = self.createAccount;

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
            self.$66.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        _O_.subscribe('account.detail.rendered', function (data) {
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
            if (data.hasOwnProperty('account')) {
                account = AccountStore.collection().filter(function (a) {
                    return a.id === parseInt(data.account, 10);
                })[0];

                self.accountTitle(account.title);
            }
            self.selectedAccount(account);

            if (account && account.hasOwnProperty('id')) {
                $('#account_provider').val(account.provider_type);
                $('#account_title').val(account.title);
                $('#account_description').val(account.description);
                $('#account_id').val(account.account_id);
                $('#account_id').attr('disabled', 'disabled');
                $('#access_key_id').attr('disabled', 'disabled');
                $('#secret_access_key').attr('disabled', 'disabled');
                $('#keypair').attr('disabled', 'disabled');
                $('#default_availability_zone').val(account.default_availability_zone);
                $('#route53_domain').val(' ');
                $('#route53_domain').attr('disabled', 'disabled');
                $('#private_key_file').val(account.yaml);

                self.saveAction = self.updateAccount;
            }
        };

        self.saveAccount = function (model, evt) {
            self.saveAction(model, evt);
        };

        self.createAccount = function (model, evt) {
            var account = formutils.collectFormFields(evt.target.form);

            API.Accounts.save(account).then(function (newAccount) {
                AccountStore.add(newAccount);
                self.navigate({ view: 'account.list' });
            });
        };

        self.updateAccount = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var account = {};

            // Clone the self.selectedAccount item so we don't modify the item in the store
            // for (var key in self.selectedAccount()) {
            //     account[key] = self.selectedAccount()[key];
            // }

            // Update property values with those submitted from form
            account.id = self.selectedAccount().id;
            account.url = self.selectedAccount().url;
            account.provider_type = record.account_provider.value;
            account.title = record.account_title.value;
            account.description = record.account_description.value;
            account.default_availability_zone = record.default_availability_zone.value;

            // delete account.yaml;

            console.log(account);
            // return;

            // PATCH the update, and on success, replace the current item in the store with new one
            API.Accounts.update(account).then(function () {
                stores.Accounts(_.reject(stores.Accounts(), function (acct) {
                    return acct.id === self.selectedAccount.id;
                }));
                stores.Accounts.push(account);
                self.navigate({ view: 'account.list' });
            });
        };

        self.deleteAccount = function (account) {
            API.Accounts.delete(account).catch(function (error) {
                self.showError(error);
            });
        };
    };

    vm.prototype = new base();
    return new vm();
});
