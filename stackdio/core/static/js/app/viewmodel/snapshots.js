define(["knockout",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, formutils, models, stores, API) {

    return function snapshotViewModel () {
        var self = this;

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


        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#snapshot-form-container").dialog({
            autoOpen: false,
            width: 650,
            modal: false
        });

   }
});