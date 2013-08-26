define(["knockout", "datatables", "jquery-ui", "app/settings", "app/models", "app/stores", "app/api/api"], 
    function (ko, datatables, jUI, settings, models, stores, API) {

    /*
     *  **********************************************************************************
     *  ==================================================================================
     *  V I E W   M O D E L
     *  ==================================================================================
     *  **********************************************************************************
     */
    function stackdioModel() {
        var self = this;

        self.stores = stores;
        self.models = models;
        self.API = API;

        self.showVolumes = ko.observable(false);
        self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch'];
        self.currentSection = ko.observable();

        self.selectedProviderType = null;
        self.selectedProfile = null;
        self.selectedAccount = null;


        //
        //      S T A C K S
        //
        self.saveStack = function (autoLaunch) {
            var h, host, hosts = stores.NewHosts();

            var stack = {
                cloud_provider: self.selectedAccount.id,
                auto_launch: autoLaunch === true,
                title: document.getElementById('stack_title').value,
                description: document.getElementById('stack_purpose').value,
                hosts: []
            };

            for (h in hosts) {
                host = hosts[h];
                stack.hosts.push({
                     host_count: host.count
                    ,host_size: host.instance_size
                    ,host_pattern: host.hostname
                    ,cloud_profile: self.selectedProfile.id
                    ,salt_roles: _.map(host.roles, function (r) { return r.value; })
                    ,host_security_groups: host.security_groups
                });
            }

            API.Stacks.save(stack)
                .then(function () {
                    stores.NewHosts.removeAll();

                    // Clear the stack form
                    $('#stack_title').val('');
                    $('#stack_purpose').val('');

                    // Hide the stack form
                    $( "#stack-form-container" ).dialog("close");

                    $("#alert-success").show();
                });
        }
        self.launchStack = function (model, evt) {
            self.saveStack(true);
        };


        // 
        //      P R O F I L E S
        // 
        self.addProfile = function (model, evt) {
            var profile = self.collectFormFields(evt.target.form);
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

        self.closeError = function () {
            $("#alert-error").hide();
        };

        self.closeSuccess = function () {
            $("#alert-success").hide();
        };

        // 
        //      A C C O U N T S
        // 
        self.addAccount = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);
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


        // 
        //      S N A P S H O T S
        // 
        self.addSnapshot = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);
            record.account = self.selectedAccount;
            console.log(record);
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



        // 
        //      N E W   H O S T   V O L U M E S
        // 
        self.addHostVolume = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);
            var volume = new NewHostVolume(0, record.volume_snapshot.value, record.volume_device.value, record.volume_mount_point.value);

            volume.snapshot = _.find(self.snapshots(), function (s) {
                return s.id === parseInt(record.volume_snapshot.value, 10);
            });

            stores.NewHostVolumes.push(volume);
        };
        self.removeHostVolume = function (volume) {
            self.newHostVolumes.remove(volume);
        };


        // 
        //      N E W   H O S T S
        // 
        self.addHost = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);

            var host = new models.NewHost().create({ 
                id: '',
                count: record.host_count.value,
                cloud_profile: self.selectedProfile.id,
                instance_size: record.host_instance_size.value,
                roles: record.host_roles,
                hostname: record.host_hostname.value,
                security_groups: record.host_security_groups.value
            });

            host.size = _.find(stores.InstanceSizes(), function (i) {
                return i.id === parseInt(record.host_instance_size.value, 10);
            });

            host.flat_roles = _.map(host.roles, function (r) { 
                return '<div style="line-height:15px !important;">' + r.text + '</div>'; 
            }).join('');

            console.log('new host', host);

            stores.NewHosts.push(host);
        };

        self.removeHost = function (host) {
            stores.NewHosts.remove(host);
        };


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

        self.doStackAction = function (action, evt, stack) {
            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            $.ajax({
                url: '/api/stacks/' + stack.id + '/',
                type: 'PUT',
                data: data,
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    console.log(response);
                    API.Stacks.load();
                }
            });
        };

        self.collectFormFields = function (obj) {
            var i, item, el, form = {}, id, idx;
            var o, option, options, selectedOptions;

            // Collect the fields from the form
            for (i in obj) {
                item = obj[i];
                if (item !== null && item.hasOwnProperty('localName') && ['select','input'].indexOf(item.localName) !== -1) {

                    id = item.id;
                    form[id] = {};

                    switch (item.localName) {
                        case 'input':
                            if (item.files === null) {
                                form[id].text = item.text;
                                form[id].value = item.value;
                            } else {
                                form[id].text = '';
                                form[id].value = '';
                                form[id].files = item.files;
                            }
                            break;
                        case 'select':
                            el = document.getElementById(id);

                            if (el.multiple) {
                                form[id] = [];
                                options = el.selectedOptions;
                                for (o in options) {
                                    option = options[o];
                                    if (typeof option.text !== 'undefined') {
                                        form[id].push({ text: option.text, value: option.value });
                                    }
                                }
                            } else {
                                idx = el.selectedIndex;
                                if (idx !== -1) {
                                    form[id].text = el[idx].text;
                                    form[id].value = el[idx].value;
                                    form[id].selectedIndex = idx;
                                }
                            }

                            break;
                    }
                }
            }

            return form;
        }

        self.showProfileForm = function (account) {
            self.selectedAccount = account;
            $( "#profile-form-container" ).dialog("open");
        }

        self.closeProfileForm = function () {
            $( "#profile-form-container" ).dialog("close");
        }

        self.showSnapshotForm = function (account) {
            self.selectedAccount = account;
            $( "#snapshot-form-container" ).dialog("open");
        }

        self.closeSnapshotForm = function () {
            self.selectedAccount = account;
            $( "#snapshot-form-container" ).dialog("close");
        }

        self.showAccountForm = function (type) {
            self.selectedProviderType = type;
            $( "#accounts-form-container" ).dialog("open");
        }

        self.closeAccountForm = function (type) {
            self.selectedProviderType = type;
            $( "#accounts-form-container" ).dialog("close");
        }

        self.showStackForm = function (account) {
            self.selectedAccount = account;
            $( "#stack-form-container" ).dialog("open");
        }

        self.closeStackForm = function () {
            $( "#stack-form-container" ).dialog("close");
        }

        self.showHostForm = function (profile) {
            self.selectedProfile = profile;
            $( "#host-form-container" ).dialog("open");
        }

        self.closeHostForm = function () {
            $( "#host-form-container" ).dialog("close");
        }

        self.showVolumeForm = function () {
            $( "#volume-form-container" ).dialog("open");
        }

        self.closeVolumeForm = function () {
            $( "#volume-form-container" ).dialog("close");
        }

        self.profileSelected = function (profile) { 
            self.selectedProfile = profile;
        };

        self.toggleVolumeForm = function () { 
            self.showVolumes(!self.showVolumes());
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
            .then(API.Accounts.load)
            .then(API.Profiles.load)
            .then(API.Snapshots.load)
            .then(API.Stacks.load)
            .then(function () {
                self.gotoSection("Stacks");
            });
    };












    /*
     *  ==================================================================================
     *  C U S T O M   B I N D I N G S
     *  ==================================================================================
     */
    ko.bindingHandlers.bootstrapPopover = {
        init: function(element, valueAccessor, allBindingsAccessor, viewModel) {
            var options = valueAccessor();
            var defaultOptions = {};
            options = $.extend(true, {}, defaultOptions, options);
            options.trigger = "hover";
            options.placement = "bottom";
            options.html = true;
            options.title = "Stack History";
            $(element).popover(options);
        }
    };








    /*
     *  ==================================================================================
     *  D I A L O G   E L E M E N T S
     *  ==================================================================================
     */
    $("#stack-form-container").dialog({autoOpen: false, width: window.innerWidth - 225, height: 500, position: [200,50], modal: false });
    $("#snapshot-form-container").dialog({autoOpen: false, width: 650, modal: false });
    $("#accounts-form-container").dialog({autoOpen: false, width: 650, modal: false });
    $("#host-form-container").dialog({position: [(window.innerWidth / 2) - 275,50], autoOpen: false, width: 550, modal: true });
    $("#volume-form-container").dialog({position: [(window.innerWidth / 2) - 250,50], autoOpen: false, width: 500, modal: true });
    $("#profile-form-container").dialog({autoOpen: false, width: 650, modal: false });


    /*
     *  ==================================================================================
     *  D A T A   T A B L E   E L E M E N T S
     *  ==================================================================================
     */
    $('#snapshots').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#stacks').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#accounts').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#stack-hosts').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#profiles').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });


    stackdio.mainModel = new stackdioModel();
    ko.applyBindings(stackdio.mainModel);

});

