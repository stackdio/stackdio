$(document).ready(function () {


    $('#stacks').dataTable({
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

    $( "#stack-form-container" ).dialog({
        autoOpen: false,
        width: 1200,
        position: [200,50],
        // height: 500,
        modal: false
    });

    $( "#host-form-container" ).dialog({
        autoOpen: false,
        width: 800,
        modal: false
    });

    /*
     *  ==================================================================================
     *  V I E W   M O D E L
     *  ==================================================================================
     */
    function stackdioModel() {
        var self = this;

        self.showVolumes = ko.observable(false);
        self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
        self.currentSection = ko.observable();

        /*
         *  ==================================================================================
         *  C O L L E C T I O N S
         *  ==================================================================================
         */
        self.stacks = ko.observableArray([]);
        self.roles = ko.observableArray([]);
        self.launchedHosts = ko.observableArray([]);
        self.providers = ko.observableArray([]);
        self.providerAccounts = ko.observableArray([]);
        self.instanceSizes = ko.observableArray([]);
        self.accountProfiles = ko.observableArray([]);
        self.snapshots = ko.observableArray([]);

        self.newHostVolumes = ko.observableArray([]);
        self.addHostVolume = function (model, evt) {
            var form = self.collectFormFields(evt.target.form);

            self.newHostVolumes.push(new NewHostVolume(0, form['volume-snapshot'], form['volume-device'], form['volume-mount-point']));
        };
        self.removeHostVolume = function (volume) {
            self.newHostVolumes.remove(volume);
        };


        // id, stack, count, cloud_profile, instance_size, roles, hostname, security_groups
        self.newHosts = ko.observableArray([
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg')
        ]);

        self.addHost = function (model, evt) {
            var form = self.collectFormFields(evt.target.form);
            console.log(form);
            self.newHosts.push(new NewHost(0, 0, count, cloud_profile, instance_size, roles, hostname, security_groups));
        };
        self.removeHost = function (host) {
            self.newHosts.remove(host);
        };


        /*
         *  ==================================================================================
         *  M E T H O D S
         *  ==================================================================================
         */

        self.collectFormFields = function (obj) {
            var i, item, el, form = {};

            // Collect the fields from the form
            for (i in obj) {
                item = obj[i];
                if (item !== null && item.hasOwnProperty('localName') && ['select','input'].indexOf(item.localName) !== -1) {
                    switch (item.localName) {
                        case 'input':
                            form[item.id] = item.value;
                            break;
                        case 'select':
                            var el = document.getElementById(item.id);
                            if (el.selectedIndex !== -1) {
                                form[item.id] = el[el.selectedIndex].text;
                            }
                            break;
                    }
                }
            }

            return form;
        }

        self.showStackForm = function () {
            self.loadProfiles();
            self.loadInstanceSizes();
            self.loadRoles();
            self.loadSnapshots();

            $( "#stack-form-container" ).dialog( "open" );
        }

        self.showHostForm = function () {
            self.loadProfiles();
            $( "#host-form-container" ).dialog( "open" );
        }

        self.gotoSection = function (section) { 
            location.hash = section;
            self.currentSection(section);
        };

        self.profileSelected = function (profile) { 
            console.log(profile);
        };

        self.toggleVolumeForm = function () { 
            self.showVolumes(!self.showVolumes());
        };

        /*
         *  ==================================================================================
         *  N A V I G A T I O N   H A N D L E R
         *  ==================================================================================
         */
        $.sammy(function() {
            this.get('#:section', function () {
                self.currentSection(this.params.section);
            });

            this.get('', function() { this.app.runRoute('get', '#Stacks') });
        }).run();

        /*
         *  ==================================================================================
         *  A P I   C A L L S
         *  ==================================================================================
         */
        $.ajax({
            url: '/api/stacks/',
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password'),
                "Accept": "application/json"
            },
            success: function (response) {
                var s, stack, stacks = response.results;

                for (s in stacks) {
                    stack = stacks[s];
                    self.stacks.push(new Stack(stack.title, stack.description, stack.status, stack.created, stack.host_count, stack.id, stack.slug, stack.user, stack.url));
                }
            }
        });

        self.loadSnapshots = function () {
            $.ajax({
                url: '/api/snapshots/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    self.snapshots.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.snapshots.push(new Snapshot(item.id, item.url, item.title, item.description, item.cloud_provider, item.size_in_gb, item.snapshot_id));
                    }
                }
            });
        };

        self.loadRoles = function () {
            $.ajax({
                url: '/api/roles/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    self.roles.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.roles.push(new Role(item.id, item.url, item.title, item.role_name));
                    }
                }
            });
        };

        self.loadInstanceSizes = function () {
            $.ajax({
                url: '/api/instance_sizes/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    self.instanceSizes.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.instanceSizes.push(new InstanceSize(item.id,
                                                                 item.url,
                                                                 item.title, 
                                                                 item.description,
                                                                 item.slug,
                                                                 item.provider_type,
                                                                 item.instance_id
                                                                )
                        );
                    }
                }
            });
        };


        self.loadProfiles = function () {
            $.ajax({
                url: '/api/profiles/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    self.accountProfiles.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.accountProfiles.push(new AccountProfile(item.id,
                                                                    item.url,
                                                                    item.title, 
                                                                    item.description,
                                                                    item.slug,
                                                                    item.cloud_provider,
                                                                    item.default_instance_size,
                                                                    item.image_id,
                                                                    item.ssh_user
                                                                    )
                        );
                    }
                }
            });
        };

    };

    /*
     *  ==================================================================================
     *  D A T A   M O D E L S
     *  ==================================================================================
     */
    var Stack = function (title, description, status, created, host_count, id, slug, user, url) {
        var self = this;
        self.id = id;
        self.title = ko.observable(title);
        self.description = ko.observable(description);
        self.slug = slug;
        self.url = url;
        self.created = created;
        self.status = ko.observable(status);
        self.host_count = host_count;
        self.user = user;
    };

    var AccountProfile = function (id, url, title, description, slug, cloud_provider, default_instance_size, image_id, ssh_user) {
        var self = this;
        self.cloud_provider = cloud_provider;
        self.title = title;
        self.description = description;
        self.default_instance_size = default_instance_size;
        self.image_id = image_id;
        self.ssh_user = ssh_user;
        self.id = id;
        self.slug = slug;
        self.url = url;
    };

    var NewHost = function (id, stack, count, cloud_profile, instance_size, roles, hostname, security_groups) {
        var self = this;
        self.id = id;
        self.stack = stack;
        self.count = count;
        self.cloud_profile = cloud_profile;
        self.instance_size = instance_size;
        self.roles = roles;
        self.hostname = hostname;
        self.security_groups = security_groups;
    };

    var NewHostVolume = function (id, snapshot, device, mount_point) {
        var self = this;
        self.id = id;
        self.snapshot = snapshot;
        self.device = device;
        self.mount_point = mount_point;
    };

    var InstanceSize = function (id, url, title, description, slug, provider_type, instance_id) {
        var self = this;
        self.id = id;
        self.url = url;
        self.title = title;
        self.description = description;
        self.slug = slug;
        self.provider_type = provider_type;
        self.instance_id = instance_id;
    };

    var Role = function (id, url, title, role_name) {
        var self = this;
        self.id = id;
        self.url = url;
        self.title = title;
        self.role_name = role_name;
    };

    var Snapshot = function (id, url, title, description, cloud_provider, size_in_gb, snapshot_id) {
        var self = this;
        self.id = id;
        self.url = url;
        self.title = title;
        self.description = description;
        self.cloud_provider = cloud_provider;
        self.size_in_gb = size_in_gb;
        self.snapshot_id = snapshot_id;
    };



    ko.applyBindings(new stackdioModel());

});