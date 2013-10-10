define([
        "lib/q", 
        "moment", 
        "jquery-ui", 
        "knockout", 
        "bootstrap-typeahead", 
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
        "app/viewmodel/securityGroup",
        "app/viewmodel/stacks"
    ],
    function (Q, moment, jui, ko, typeahead, settings, formutils, models, stores, API, abstractVM, profileVM, accountVM, volumeVM, snapshotVM, securityGroupVM, stackVM) {

        function stackdioModel() {
            var self = this;

            self.stores = stores;
            self.models = models;
            self.API = API;
            self.moment = moment;
            self.isSuperUser = ko.observable(stackdio.settings.superuser);

            self.sections = ['Stacks', 'Security', 'Accounts', 'Profiles', 'Snapshots'];
            self.currentSection = ko.observable();

            self.securityGroup = new securityGroupVM();
            self.profile = new profileVM();
            self.account = new accountVM();
            self.volume = new volumeVM();
            self.snapshot = new snapshotVM();
            self.stack = new stackVM();

            /*
             *  ==================================================================================
             *  U S E R   M A N A G E M E N T
             *  ==================================================================================
             */
            self.showPasswordForm = function () {
                $("#user-password").dialog("open");
            };

            self.closePasswordForm = function () {
                $("#user-password").dialog("close");
                $('#new_password_confirm').popover('hide');
            };

            self.savePassword = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);

                if (record.new_password.value !== record.new_password_confirm.value) {
                    self.showMessage('#password-error', 'Your new passwords do not match', true);
                    return;
                }

                API.Users.savePassword(record.current_password.value, 
                                       record.new_password.value, 
                                       record.new_password_confirm.value)
                    .then(function (error) {
                        if (typeof error !== 'undefined') {
                            self.showMessage('#password-error', error, true, 5000);
                            return;
                        }
                        $("#user-password").dialog("close");
                        self.showSuccess();
                    });
            };


            self.showUserProfile = function () {
                $("#user-profile").dialog("open");
            };

            self.closeProfileForm = function () {
                $("#user-profile").dialog("close");
            };

            self.saveProfile = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                API.Users.saveKey(record.public_key.value);
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
                    $("#alert-no-accounts").show();
                    setTimeout(function () { $("#alert-no-accounts").hide(); }, 3000);
                    return;
                }

                // Force user to create a profile if none exist
                if (section !== "Profiles" && section !== "Accounts" && stores.Profiles().length === 0) {
                    self.currentSection("Profiles")
                    self.showMessage("#alert-no-profiles", "", true);
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
            API.Users.load()
                .then(function (key) {
                    $("#public_key").val(key);
                });
            API.InstanceSizes.load();
            API.Roles.load();

            API.ProviderTypes.load()
                .then(API.Zones.load)
                .then(self.account.loadAccounts)
                .then(self.profile.loadProfiles)
                .then(self.securityGroup.loadSecurityGroups)
                .then(API.Snapshots.load)
                .then(API.Stacks.load)

                // Everything you want to do AFTER all data has loaded
                .then(function () {
                    // Convert select elements to the nice Bootstrappy style
                    $('select[id!="aws_security_group"][id!="stackdio_security_group"][id!="host_security_groups"]').selectpicker();

                    // Remove the hide class from the main sections
                    $("div[class='hide'][data-bind]").removeClass('hide');

                    // Take the user to the stacks section
                    self.gotoSection("Stacks");

                    // self.showMessage("#alert-default-security-groups");
                })
                .catch(function (error) {
                    // Handle any error from all above steps
                    console.error(error.name, error.message);
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

        $("#user-password").dialog({
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
