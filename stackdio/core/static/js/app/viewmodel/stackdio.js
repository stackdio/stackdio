define([
        "moment", 
        "jquery-ui", 
        "knockout", 
        "app/settings",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api",
        "app/viewmodel/profiles",
        "app/viewmodel/accounts",
        "app/viewmodel/volumes",
        "app/viewmodel/snapshots",
        "app/viewmodel/stacks"
    ],
    function (moment, jui, ko, settings, formutil, models, stores, API, profileVM, accountVM, volumeVM, snapshotVM, stackVM) {

    /*
     *  ==================================================================================
     *  V I E W   M O D E L
     *  ==================================================================================
     */
    function stackdioModel() {
        var self = this;

        self.stores = stores;
        self.models = models;
        self.API = API;
        self.moment = moment;

        self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch'];
        self.stackHostActions = ['Stop', 'Terminate', 'Start'];
        self.currentSection = ko.observable();

        self.profile = new profileVM();
        self.account = new accountVM();
        self.volume = new volumeVM();
        self.snapshot = new snapshotVM();
        self.stack = new stackVM();

        /*
         *  ==================================================================================
         *  M E T H O D S
         *  ==================================================================================
         */
        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };

        self.showMessage = function (id) {
            $(id).show();
            setTimeout('$("'+id+'").hide()', 3000);
        };

        self.closeError = function () {
            $("#alert-error").hide();
        };

        self.closeSuccess = function () {
            $("#alert-success").hide();
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
        API.InstanceSizes.load();
        API.Roles.load();

        API.ProviderTypes.load()
            .then(API.Zones.load)
            .then(API.Accounts.load)
            .then(API.Profiles.load)
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
            });
    };

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

    stackdio.mainModel = new stackdioModel();
    ko.applyBindings(stackdio.mainModel);

});
