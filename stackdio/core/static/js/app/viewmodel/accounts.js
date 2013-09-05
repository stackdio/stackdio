define(["knockout",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, formutils, models, stores, API) {

    return function accountViewModel () {
        var self = this;

        self.selectedAccount = null;
        self.selectedProviderType = null;

        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };
        
        self.addAccount = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            record.providerType = self.selectedProviderType;

            API.Accounts.save(record)
                .then(function () {
                    $("#accounts-form-container").dialog("close");
                    self.showSuccess();
                })
                .catch(function (error) {
                    $("#alert-error").show();
                })
        };

        self.removeAccount = function (account) {
            API.Accounts.delete(account)
                .then(self.showSuccess)
                .catch(function (error) {
                    $("#alert-error").show();
                }).done();
        };

        self.showAccountForm = function (type) {
            self.selectedProviderType = type;
            $( "#accounts-form-container" ).dialog("open");
        }

        self.closeAccountForm = function (type) {
            self.selectedProviderType = type;
            $( "#accounts-form-container" ).dialog("close");
        }

        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#accounts-form-container").dialog({
            autoOpen: false,
            width: 650,
            modal: false
        });
   }
});