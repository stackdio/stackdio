define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/stores',
    'model/models',
    'api/api'
],
function (Q, ko, base, _O_, formutils, stores, models, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stores = stores;
        self.selectedAccount = ko.observable(null);
        self.saveAction = self.createAccount;

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
            if (stores.Accounts().length === 0) {
                [API.Accounts.load, API.Profiles.load].reduce(function (loadData, next) {
                    return loadData.then(next);
                }, Q([])).then(function () {
                    self.init(data);
                });
            } else {
                self.init(data);
            }
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var account = null;

            if (data.hasOwnProperty('account')) {
                account = stores.Accounts().map(function (p) {
                    if (p.id === parseInt(data.account, 10)) {
                        return p;
                    }
                }).reduce(function (p, c) {
                    if (c.hasOwnProperty('id')) {
                        return c;
                    }
                });
            }

            self.selectedAccount = account;

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

            // profile.account = stores.Accounts().map(function (account) {
            //     if (account.id === parseInt(profile.profile_account.value, 10)) {
            //         return account;
            //     }
            // })[0];

            API.Accounts.save(account).then(function (newAccount) {
                stores.Accounts.push(newAccount);
                self.navigate({ view: 'account.list' });
            });
        };

        self.updateAccount = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var account = {};

            // Clone the self.selectedAccount item so we don't modify the item in the store
            for (var key in self.selectedAccount) {
                account[key] = self.selectedAccount[key];
            }

            // Update property values with those submitted from form
            account.provider_type = record.account_provider.value;
            account.title = record.account_title.value;
            account.description = record.account_description.value;
            account.default_availability_zone = record.default_availability_zone.value;

            delete account.yaml;

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
