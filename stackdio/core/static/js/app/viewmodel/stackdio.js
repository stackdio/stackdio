define([
        "lib/q", 
        "moment", 
        "jquery-ui", 
        "knockout", 
        "app/settings",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api",
        "app/viewmodel/abstract",
        "app/viewmodel/profiles",
        "app/viewmodel/accounts",
        "app/viewmodel/volumes",
        "app/viewmodel/snapshots",
        "app/viewmodel/stacks"
    ],
    function (Q, moment, jui, ko, settings, formutils, models, stores, API, abstractVM, profileVM, accountVM, volumeVM, snapshotVM, stackVM) {

        function stackdioModel() {
            var self = this;

            self.stores = stores;
            self.models = models;
            self.API = API;
            self.moment = moment;
            self.isSuperUser = ko.observable(stackdio.settings.superuser);

            self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
            self.currentSection = ko.observable();

            self.profile = new profileVM();
            self.account = new accountVM();
            self.volume = new volumeVM();
            self.snapshot = new snapshotVM();
            self.stack = new stackVM();

            /*
             *  ==================================================================================
             *  N A V I G A T I O N   H A N D L E R
             *  ==================================================================================
             */
            self.showUserProfile = function () {
                $("#user-profile").dialog("open");
            };

            self.closeProfileForm = function () {
                $("#user-profile").dialog("close");
            };

            self.saveProfile = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);

                API.Users.save(record.public_key.value);

                $("#user-profile").dialog("close");
            };

            /*
             *  ==================================================================================
             *  N A V I G A T I O N   H A N D L E R
             *  ==================================================================================
             */
            self.gotoSection = function (section) {

                // Force user to create a account if none exist
                if (section !== "Accounts" && stores.Accounts().length === 0) {
                    self.currentSection("Accounts")
                    self.showMessage("#alert-no-accounts");
                    return;
                }

                // Force user to create a profile if none exist
                if (section !== "Profiles" && section !== "Accounts" && stores.Profiles().length === 0) {
                    self.currentSection("Profiles")
                    self.showMessage("#alert-no-profiles");
                    return;
                }

                location.hash = section;
                self.currentSection(section);
            };


            /*
             *  ==================================================================================
             *  L O A D I N G   D A T A . . .   I N   O R D E R 
             *  ==================================================================================
             */
            API.Users.load();
            API.InstanceSizes.load();
            API.Roles.load();

            API.ProviderTypes.load()
                .then(API.Zones.load)
                .then(self.account.loadAccounts)
                .then(self.profile.loadProfiles)
                .then(API.Snapshots.load)
                .then(API.Stacks.load)

                // Everything you want to do AFTER all data has loaded
                .then(function () {
                    // Convert select elements to the nice Bootstrappy style
                    $('select').selectpicker();

                    // Remove the hide class from the main sections
                    $("div[class='hide'][data-bind]").removeClass('hide');

                    // Take the user to the stacks section
                    self.gotoSection("Stacks");
                })

                .catch(function (error) {
                    // Handle any error from all above steps
                    console.log(error);
                });
        };

        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#user-profile").dialog({
            autoOpen: false,
            width: 500,
            modal: true
        });


        /*
         *  ==================================================================================
         *  C U S T O M   B I N D I N G S
         *  ==================================================================================
         */
        ko.bindingHandlers.bootstrapPopover = {
            init: function (element, valueAccessor, allBindingsAccessor, viewModel) {
                var options = valueAccessor();
                var defaultOptions = {};
                options = $.extend(true, {}, defaultOptions, options);
                options.trigger = "click";
                options.placement = "bottom";
                options.html = true;
                options.title = "Stack History";
                $(element).popover(options);
            }
        };

        stackdioModel.prototype = new abstractVM();
        stackdio.mainModel = new stackdioModel();

        ko.applyBindings(stackdio.mainModel);

});
