define(["knockout",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, formutils, models, stores, API) {

    return function profileViewModel () {
        var self = this;

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


        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#profile-form-container").dialog({
            autoOpen: false,
            width: 650,
            modal: false
        });
   }
});