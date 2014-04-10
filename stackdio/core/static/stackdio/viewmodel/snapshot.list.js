define([
    'q', 
    'knockout',
    'bootbox',
    'util/galaxy',
    'util/alerts',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/Snapshots',
    'api/api'
],
function (Q, ko, bootbox, $galaxy, alerts, ProviderTypeStore, AccountStore, ProfileStore, SnapshotStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.userCanModify = ko.observable();
        self.isSuperUser = stackdio.settings.superuser;

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
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
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
        API.Snapshots.options().then(function (allowed) {
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
                location: 'snapshot.detail',
                payload: {
                    account: account.id
                }
            });
        };

        self.removeSnapshot = function (snapshot) {
            bootbox.confirm("Please confirm that you want to delete this snapshot.", function (result) {
                if (result) {
                    API.Snapshots.delete(snapshot).then(function () {
                        SnapshotStore.removeById(snapshot.id);
                        self.init();
                    })
                    .catch(function (error) {
                        alerts.showMessage('#error', 'Unable to delete this snapshot. ' + error, true);
                    });
                }
            });
        };

        self.refresh = function() {
            SnapshotStore.populate(true);
        };

    };
    return new vm();
});
