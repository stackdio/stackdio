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
        self.stackHostActions = ['Stop', 'Terminate', 'Start'];
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
                hosts: hosts
            };

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

        self.showStackDetails = function (stack) {
            API.StackHosts.load(stack)
                .then(function (response) {
                    self.showStackHosts();
                });
            return;
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
            var volume = new models.NewHostVolume().create({
                snapshot: record.volume_snapshot.value,
                device: record.volume_device.value,
                mount_point: record.volume_mount_point.value
            });

            volume.snapshot = _.find(stores.Snapshots(), function (s) {
                return s.id === parseInt(record.volume_snapshot.value, 10);
            });

            stores.HostVolumes.push(volume);
        };
        self.removeHostVolume = function (volume) {
            stores.HostVolumes.remove(volume);
        };


        // 
        //      S T A C K   H O S T S
        // 
        self.hostMetaData = function (host) {
            var metadata = '';

            _.each(host.ec2_metadata, function (v, k, l) {
                if (typeof v !== "object") {
                    metadata += '<div class="dotted-border xxsmall-padding">'+k+': '+v+'</div>';
                }
            });
            return metadata;
        };

        self.showHostMetadata = function (host) {
            _.each(host.ec2_metadata, function (v, k, l) {
                if (typeof v !== "object") {
                    stores.HostMetadata.push({ key: k, value: v });
                }
            });

            $("#host-metadata-container").dialog("open");
        };

        self.closeHostMetadata = function () {
            $( "#host-metadata-container" ).dialog("close");
        };


        // 
        //      N E W   H O S T S
        // 
        self.addHost = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);
            var v, vol;

            // Create a new host definition
            var host = new models.NewHost().create({ 
                id: '',
                host_count: record.host_count.value,
                host_pattern: record.host_hostname.value,
                host_size: record.host_instance_size.value,
                cloud_profile: self.selectedProfile.id,
                roles: record.host_roles,
                host_security_groups: record.host_security_groups.value
            });

            host.salt_roles = _.map(host.roles, function (r) { return r.value; });

            // Add the chosen instance size to the host definition
            host.size = _.find(stores.InstanceSizes(), function (i) {
                return i.id === parseInt(record.host_instance_size.value, 10);
            });

            // Add some HTML to display for the chosen roles
            host.flat_roles = _.map(host.roles, function (r) { 
                return '<div style="line-height:15px !important;">' + r.text + '</div>'; 
            }).join('');

            // Add spot instance config
            host.spot_config = {};
            host.spot_config.spot_price = (record.spot_instance_price.value !== '') ? record.spot_instance_price.value : 0;

            // Add volumes to the host
            host.volumes = [];
            for (v in stores.HostVolumes()) {
                vol = stores.HostVolumes()[v];
                host.volumes.push({
                    snapshot: vol.snapshot.id,
                    device: vol.device,
                    mount_point: vol.mount_point
                });
            }

            console.log('new host', host);
            stores.NewHosts.push(host);

            // Clear out the spot instance bid price field
            document.getElementById('spot_instance_price').value = "";
        };

        self.removeHost = function (host) {
            stores.NewHosts.remove(host);
        };


        /*
         *  ==================================================================================
         *  M E T H O D S
         *  ==================================================================================
         */

        self.clearForm = function (id) {
            var i, form = document.getElementById(id), elements = form.elements;

            for (i = 0; i < elements.length; i++) {
                field_type = elements[i].type.toLowerCase();
                switch (field_type) {
                case "text":
                case "password":
                case "textarea":
                case "hidden":
                    elements[i].value = "";
                    break;
                case "radio":
                case "checkbox":
                    if (elements[i].checked) {
                        elements[i].checked = false;
                    }
                    break;
                case "select-one":
                case "select-multi":
                    elements[i].selectedIndex = -1;
                    break;
                default:
                    break;
                }
            }
        };

        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };

        self.showMessage = function (id) {
            $(id).show();
            setTimeout('$("'+id+'").hide()', 3000);
        };

        self.doStackHostAction = function (action, evt, host) {
            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            // $.ajax({
            //     url: '/api/stacks/' + stack.id + '/',
            //     type: 'PUT',
            //     data: data,
            //     headers: {
            //         "X-CSRFToken": stackdio.csrftoken,
            //         "Accept": "application/json",
            //         "Content-Type": "application/json"
            //     },
            //     success: function (response) {
            //         console.log(response);
            //         API.Stacks.load();
            //     }
            // });
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
            // Clear out the host form
            self.clearForm('host-form');

            // Hide the window
            $( "#host-form-container" ).dialog("close");
        }

        self.showVolumeForm = function () {
            $( "#volume-form-container" ).dialog("open");
        }

        self.closeVolumeForm = function () {
            $( "#volume-form-container" ).dialog("close");
        }


        self.showStackHosts = function () {
            $( "#stack-details-container" ).dialog("open");
        }

        self.closeStackHosts = function () {
            $( "#stack-details-container" ).dialog("close");
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
                $('select').selectpicker();
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
            options.trigger = "hover";
            options.placement = "bottom";
            options.html = true;
            options.title = "Stack History";
            $(element).popover(options);
        }
    };

    ko.bindingHandlers.metadataPopover = {
        init: function (element, valueAccessor, allBindingsAccessor, viewModel) {
            var options = valueAccessor();
            var defaultOptions = {};


            options = $.extend(true, {}, defaultOptions, options);
            options.trigger = "click";
            options.placement = "right";
            options.html = true;
            options.title = "Host Metadata";

            console.log(options);
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
    $("#host-form-container").dialog({position: [(window.innerWidth / 2) - 275,50], autoOpen: false, width: 600, modal: true });
    $("#volume-form-container").dialog({position: [(window.innerWidth / 2) - 250,50], autoOpen: false, width: 500, modal: true });
    $("#profile-form-container").dialog({autoOpen: false, width: 650, modal: false });
    $("#stack-details-container").dialog({autoOpen: false, width: 650, modal: false });
    $("#host-metadata-container").dialog({autoOpen: false, width: 500, modal: false });


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

