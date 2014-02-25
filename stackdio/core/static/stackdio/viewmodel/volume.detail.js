define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/Blueprints',
    'store/HostVolumes',
    'store/Snapshots',
    'store/BlueprintHosts',
    'api/api',
    'model/models'
],
function (Q, ko, base, _O_, formutils, BlueprintStore, VolumeStore, SnapshotStore, BlueprintHostStore, API, models) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedBlueprint = ko.observable();
        self.blueprintTitle = ko.observable();
        self.selectedHost = ko.observable();
        self.hostTitle = ko.observable();

        self.BlueprintStore = BlueprintStore;
        self.VolumeStore = VolumeStore;
        self.SnapshotStore = SnapshotStore;
        self.BlueprintHostStore = BlueprintHostStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'volume.detail';
        self.templatePath = 'volume.html';
        self.domBindingId = '#volume-detail';

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
        _O_.subscribe('volume.detail.rendered', function (data) {
            SnapshotStore.populate().then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var blueprint = null;
            var host = null;


            if (data.hasOwnProperty('blueprint')) {
                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10)
                })[0];

                self.blueprintTitle(blueprint.title);
            } else {
                self.blueprintTitle('New Blueprint');
            }
            self.selectedBlueprint(blueprint);


            if (data.hasOwnProperty('host')) {
                host = BlueprintHostStore.collection().filter(function (h) {
                    return h.id === parseInt(data.host, 10)
                })[0];

                self.hostTitle(host.title);
            } else {
                self.hostTitle('New Host');
            }
            self.selectedHost(host);

        };

        self.addVolume = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            var volume = new models.BlueprintHostVolume().create({
                snapshot: record.volume_snapshot.value,
                device: record.volume_device.value,
                mount_point: record.volume_mount_point.value
            });

            // volume.snapshot = SnapshotStore.collection().filter(function (s) {
            //     return s.id === parseInt(record.volume_snapshot.value, 10);
            // })[0].id;

            VolumeStore.add(volume);
            self.navigate({ view: 'host.detail' });
        };

        self.cancelChanges = function (model, evt) {
            self.navigate({ view: 'host.detail' });
        };


    };

    vm.prototype = new base();
    return new vm();
});
