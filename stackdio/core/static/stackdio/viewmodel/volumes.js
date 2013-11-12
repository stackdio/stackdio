define(["knockout",
        "util/form",
        "model/models",
        "store/stores",
        "api/api"], 
    function (ko, formutils, models, stores, API) {

    return function volumeViewModel () {
        var self = this;

        self.stores = stores;

        self.addHostVolume = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var volume = new models.NewHostVolume().create({
                snapshot: record.volume_snapshot.value,
                device: record.volume_device.value,
                mount_point: record.volume_mount_point.value
            });

            volume.snapshot = _.find(stores.Snapshots(), function (s) {
                return s.id === parseInt(record.volume_snapshot.value, 10);
            });

            stores.HostVolumes.push(volume);
        };

        self.removeHostVolume = function (volume) {
            stores.HostVolumes.remove(volume);
        };

        self.showVolumeForm = function () {
            $( "#volume-form-container" ).dialog("open");
        };

        self.closeVolumeForm = function () {
            $( "#volume-form-container" ).dialog("close");
        };

        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#volume-form-container").dialog({
            position: [(window.innerWidth / 2) - 250,50],
            autoOpen: false,
            width: 500,
            modal: true
        });

   }
});