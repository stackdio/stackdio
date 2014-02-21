define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/ProviderTypes',
    'store/Accounts',
    'store/Profiles',
    'store/Snapshots',
    'api/api'
],
function (Q, ko, base, _O_, formutils, ProviderTypeStore, AccountStore, ProfileStore, SnapshotStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedSnapshot = ko.observable(null);
        self.snapshotTitle = ko.observable(null);

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.SnapshotStore = SnapshotStore;

        self.osChoices = [
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
            self.$66.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        _O_.subscribe('snapshot.detail.rendered', function (data) {
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

            if (snapshot && snapshot.hasOwnProperty('id')) {
                $('#account_provider').val(snapshot.provider_type);
                $('#account_title').val(snapshot.title);
                $('#account_description').val(snapshot.description);
                $('#account_id').val(snapshot.account_id);
                $('#account_id').attr('disabled', 'disabled');
                $('#access_key_id').attr('disabled', 'disabled');
                $('#secret_access_key').attr('disabled', 'disabled');
                $('#keypair').attr('disabled', 'disabled');
                $('#default_availability_zone').val(snapshot.default_availability_zone);
                $('#route53_domain').val(' ');
                $('#route53_domain').attr('disabled', 'disabled');
                $('#private_key_file').val(snapshot.yaml);

                self.saveAction = self.updateAccount;
            }
        };

        self.cancelChanges = function () {
            self.navigate({ view: 'formula.list' });
        };

        self.updateSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            // API.Snapshots.update(record).then(function () {

            // })
            // .catch(function (error) {
            //     $("#alert-error").show();
            // });
        };

        self.createSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            API.Snapshots.save(snapshot).then(function () {
                SnapshotStore.add(newSnapshot)
            })
            .catch(function (error) {
                $("#alert-error").show();
            });
        };

    };

    vm.prototype = new base();
    return new vm();
});
