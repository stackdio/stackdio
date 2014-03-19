define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'store/Accounts',
    'store/Snapshots',
    'api/api'
],
function (Q, ko, $galaxy, alerts, formutils, AccountStore, SnapshotStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedSnapshot = ko.observable(null);
        self.selectedAccount = ko.observable(null);
        self.snapshotTitle = ko.observable(null);

        self.AccountStore = AccountStore;
        self.SnapshotStore = SnapshotStore;

        self.fileSystemChoices = [
            {
                id: 'ext2',
                title: 'ext2'
            },
            {
                id: 'ext3',
                title: 'ext3'
            },
            {
                id: 'ext4',
                title: 'ext4'
            },
            {
                id: 'fuse',
                title: 'fuse'
            },
            {
                id: 'xfs',
                title: 'xfs'
            }
        ];


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'snapshot.detail';
        self.templatePath = 'snapshot.html';
        self.domBindingId = '#snapshot-detail';

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
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var snapshot = null;

            if (data.hasOwnProperty('snapshot')) {
                snapshot = SnapshotStore.collection().filter(function (s) {
                    return s.id === parseInt(data.snapshot, 10);
                })[0];

                self.snapshotTitle(snapshot.title);
            } else {
                self.snapshotTitle('New Snapshot');
            }
            self.selectedSnapshot(snapshot);


            if (data.hasOwnProperty('account')) {
                account = AccountStore.collection().filter(function (s) {
                    return s.id === parseInt(data.account, 10);
                })[0];
            }
            self.selectedAccount(account);

            if (snapshot && snapshot.hasOwnProperty('id')) {

            }
        };

        self.cancelChanges = function () {
            $galaxy.transport('snapshot.list');
        };

        self.updateSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
        };

        self.createSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form),
            snapshot = {
                title: $('#snapshot_title').val(),
                description: $('#snapshot_description').val(),
                cloud_provider: self.selectedAccount().id,
                snapshot_id: $('#snapshot_id').val(),
                size_in_gb: $('#snapshot_size').val(),
                filesystem_type: $('#filesystem_type').val()
            };

            API.Snapshots.save(snapshot).then(function (newSnapshot) {
                SnapshotStore.add(newSnapshot);
                alerts.showMessage('#success', 'Snapshot successfully created', true, 2000);
                $galaxy.transport('snapshot.list');
            })
            .catch(function (errors) {
                alerts.showMessage('#error', errors.join(' '), true, 5000);
            });
        };
    };
    return new vm();
});
