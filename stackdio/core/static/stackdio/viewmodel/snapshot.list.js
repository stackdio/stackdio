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
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        self.$66.news.subscribe('snapshot.list.rendered', function (data) {
            ProviderTypeStore.populate().then(function () {
                return AccountStore.populate();
            }).then(function () {
                return ProfileStore.populate();
            }).then(function () {
                return SnapshotStore.populate();
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
            var enhancedSnapshot = {};

            self.EnhancedSnapshotStore.removeAll();

            SnapshotStore.collection().forEach(function (snapshot) {
                // Clone each snapshot into an enhancedSnapshot object for populating the UI
                enhancedSnapshot = {};
                for (var key in snapshot) {
                    enhancedSnapshot[key] = snapshot[key];
                }

                enhancedSnapshot.account = AccountStore.collection().filter(function (account) {
                    return enhancedSnapshot.cloud_provider === account.id;
                })[0];

                self.EnhancedSnapshotStore.push(enhancedSnapshot);
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

        self.createSnapshot = function (account) {
            $galaxy.transport({
                view: 'snapshot.detail',
                data: {
                    account: account.id
                }
            });
        };

        self.updateSnapshot = function (model, evt) {
            // PATCH the update, and on success, replace the current item in the store with new one
            // API.Accounts.update(account).then(function () {
            //     stores.Accounts(_.reject(stores.Accounts(), function (acct) {
            //         return acct.id === self.selectedAccount.id;
            //     }));
            //     stores.Accounts.push(account);
            //     $galaxy.transport({ view: 'account.list' });
            // });
        };

        self.removeSnapshot = function (snapshot) {
            API.Snapshots.delete(snapshot).then(function () {
                SnapshotStore.removeById(snapshot.id);
                self.init();
            })
            .catch(function (error) {
                $("#alert-error").show();
            });
        };

    };

    vm.prototype = new base();
    return new vm();
});
