define(["knockout",
        "lib/q", 
        "app/util/form",
        "app/viewmodel/abstract",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, Q, formutils, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;

            self.selectedAccount = null;
            self.selectedProviderType = null;
            self.userCanModify = ko.observable(true);

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

            self.deleteAccount = function (account) {
                API.Accounts.delete(account)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error);
                    });
            };

            self.loadAccounts = function () {
                return API.Accounts.load();

                // var deferred = Q.defer();

                // API.Accounts.load()
                //     .then(function (allowHeader) {
                //         // self.userCanModify(!!~allowHeader.split(',').indexOf('DELETE'));
                //         deferred.resolve();
                //     });

                // return deferred.promise;
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
        };

        vm.prototype = new abstractVM();

        return vm;
});