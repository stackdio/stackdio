define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/Snapshots',
    'api/api'
],
function (Q, ko, base, _O_, ProviderTypeStore, AccountStore, ProfileStore, SnapshotStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.userCanModify = ko.observable();

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.SnapshotStore = SnapshotStore;
        self.EnhancedSnapshotStore = ko.observableArray();



        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'snapshot.list';
        self.templatePath = 'snapshots.html';
        self.domBindingId = '#snapshot-list';

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
        _O_.subscribe('snapshot.list.rendered', function (data) {
            ProviderTypeStore.populate().then(function () {
                return AccountStore.populate();
            }).then(function () {
                return ProfileStore.populate();
            }).then(function () {
                return SnapshotStore.populate();
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
            
            SnapshotStore.collection().forEach(function (snapshot) {
                snapshot.account = AccountStore.collection().map(function (account) {
                    return snapshot.cloud_provider === account.id;
                }).length;

                self.EnhancedSnapshotStore.push(snapshot);
            });
        };

        // Query OPTIONS on /providers and if DELETE is not in allowed verb list, user is not admin
        API.Snapshots.options()
            .then(function (allowed) {
                self.userCanModify(allowed.verbs.indexOf('DELETE') !== -1);
            });

        self.addSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            record.account = self.selectedAccount;

            console.log('record',record);

            API.Snapshots.save(record)
                .then(function () {
                    $("#snapshot-form-container").dialog("close");
                    self.showSuccess();
                })
                .catch(function (error) {
                    $("#alert-error").show();
                });
        };

        self.createSnapshot = function (snapshot) {
            self.navigate({
                view: 'snapshot.detail'
            });
        };

        self.updateSnapshot = function (model, evt) {
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

        self.removeSnapshot = function (snapshot) {
            API.Snapshots.delete(snapshot)
            .then(self.showSuccess)
            .catch(function (error) {
                $("#alert-error").show();
            });
        };

    };

    vm.prototype = new base();
    return new vm();
});
