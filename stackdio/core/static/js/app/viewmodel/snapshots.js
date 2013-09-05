define(["knockout",
        "app/settings",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, settings, formutils, models, stores, API) {

    return function snapshotViewModel () {
        var self = this;

        self.stores = stores;

        self.addSnapshot = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            record.account = self.selectedAccount;
            API.Snapshots.save(record)
                .then(function () {
                    $("#snapshot-form-container").dialog("close");
                    self.showSuccess();
                })
                .catch(function (error) {
                    $("#alert-error").show();
                });
        };

        self.removeSnapshot = function (snapshot) {
            API.Snapshots.delete(snapshot)
                .then(self.showSuccess)
                .catch(function (error) {
                    $("#alert-error").show();
                });
        };

        self.showSnapshotForm = function (account) {
            self.selectedAccount = account;
            $( "#snapshot-form-container" ).dialog("open");
        };

        self.closeSnapshotForm = function () {
            $( "#snapshot-form-container" ).dialog("close");
        };

        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };


        $("#snapshot-form-container").dialog({autoOpen: false, width: 650, modal: false });

        // $('#snapshots').dataTable({
        //     "bPaginate": false,
        //     "bLengthChange": false,
        //     "bFilter": true,
        //     "bSort": false,
        //     "bInfo": false,
        //     "bAutoWidth": true,
        //     "bFilter": false
        // });

   }
});