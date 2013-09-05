define(["knockout",
        "app/settings",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, settings, formutils, models, stores, API) {

    return function profileViewModel () {
        var self = this;

        self.Accounts = stores.Accounts();
        self.Profiles = stores.Profiles();
        self.InstanceSizes = stores.InstanceSizes();

        self.addProfile = function (model, evt) {
            var profile = formutils.collectFormFields(evt.target.form);
            profile.account = self.selectedAccount;

            API.Profiles.save(profile)
                .then(function () {
                    $("#profile-form-container").dialog("close");
                    self.showSuccess();

                    if (stores.Accounts().length > 0) {
                        $("#alert-no-accounts").show();
                        self.gotoSection("Accounts");
                    }
                });
        };

        self.deleteProfile = function (profile) {
            API.Profiles.delete(profile)
                .then(self.showSuccess);
        };

        self.showProfileForm = function (account) {
            console.log(account);
            self.selectedAccount = account;
            $( "#profile-form-container" ).dialog("open");
        };

        self.closeProfileForm = function () {
            $("#profile-form-container").dialog("close");
        };


        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };


        $("#profile-form-container").dialog({autoOpen: false, width: 650, modal: false });

        // $('#profiles').dataTable({
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