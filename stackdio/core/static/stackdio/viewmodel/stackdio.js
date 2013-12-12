define([
        "q", 
        "moment", 
        "jui/dialog", 
        "knockout", 
        "bootstrap-typeahead", 
        "settings",
        "util/form",
        "model/models",
        "store/stores",
        "api/api",
        "viewmodel/abstract",
        "viewmodel/profiles",
        "viewmodel/accounts",
        "viewmodel/volumes",
        "viewmodel/snapshots",
        "viewmodel/securityGroup",
        "viewmodel/formulae",
        "viewmodel/stacks",
        "viewmodel/blueprints"
    ],
    function (Q, moment, jui, ko, typeahead, settings, formutils, models, stores, API, abstractVM, profileVM, accountVM, volumeVM, snapshotVM, securityGroupVM, formulaVM, stackVM, blueprintVM) {

        function stackdioModel() {
            var self = this;

            self.stores = stores;
            self.models = models;
            self.API = API;
            self.moment = moment;
            self.isSuperUser = ko.observable(stackdio.settings.superuser);

            self.sections = [{
                id:'Blueprints',
                icon: 'glyphicon glyphicon-tower',
                visible: true
            },
            {
                id:'Stacks',
                icon: 'glyphicon glyphicon-th-list',
                visible: true
            },
            {
                id:'Accounts',
                icon: 'glyphicon glyphicon-tower',
                visible: false
            },
            {
                id:'Profiles',
                icon: 'glyphicon glyphicon-tower',
                visible: false
            },
            {
                id:'Formula',
                icon: 'glyphicon glyphicon-tint',
                visible: true
            },
            {
                id:'Snapshots',
                icon: 'glyphicon glyphicon-camera',
                visible: true
            }];
            self.currentSection = ko.observable();

            self.securityGroup = new securityGroupVM();
            self.profile = new profileVM();
            self.account = new accountVM();
            self.volume = new volumeVM();
            self.snapshot = new snapshotVM();
            self.stack = new stackVM();
            self.formula = new formulaVM();
            self.blueprint = new blueprintVM();

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
                console.log('section',section);
                // Force user to create an account if none exist
                if (section.id !== "Accounts" && stores.Accounts().length === 0) {
                    section = _.findWhere(self.sections, {id:'Accounts'});
                    $("#alert-no-accounts").show();
                    setTimeout(function () { $("#alert-no-accounts").hide(); }, 3000);
                }

                // Force user to create a profile if none exist
                if (section.id !== "Profiles" && section.id !== "Accounts" && stores.Profiles().length === 0) {
                    section = _.findWhere(self.sections, {id:'Profiles'});
                    self.showMessage("#alert-no-profiles", "", true);
                }

                location.hash = section.id;
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
            API.Formulae.load();

            API.ProviderTypes.load()
                .then(API.Zones.load)
                .then(self.account.loadAccounts)
                .then(self.profile.loadProfiles)
                .then(self.securityGroup.loadSecurityGroups)
                .then(API.Snapshots.load)
                .then(API.Blueprints.load)
                .then(API.Stacks.load)

                // Everything you want to do AFTER all data has loaded
                .then(function () {
                    // Convert select elements to the nice Bootstrappy style
                    $('select[id!="aws_security_group"][id!="host_security_groups"][id!="stackdio_security_group"]').selectpicker();

                    // Remove the hide class from the main sections
                    $("div[class*='hide'][data-bind]").removeClass('hide');

                    // Take the user to the stacks section
                    self.gotoSection(_.findWhere(self.sections, { id: 'Blueprints' }));
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
            width: 700,
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
                $(element).popover(options);
            }
        };

        stackdioModel.prototype = new abstractVM();
        stackdio.mainModel = new stackdioModel();

        ko.applyBindings(stackdio.mainModel);

});
