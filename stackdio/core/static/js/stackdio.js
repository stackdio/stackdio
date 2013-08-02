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

        self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
        self.currentSection = ko.observable();

        /*
         *  ==================================================================================
         *  C O L L E C T I O N S
         *  ==================================================================================
         */
        self.stacks = ko.observableArray([]);

        // id, stack, count, cloud_profile, instance_size, roles, hostname, security_groups
        self.newHosts = ko.observableArray([
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg')
        ]);
        self.addHost = function (count, cloud_profile, instance_size, roles, hostname, security_groups) {
            self.newHosts.push(new NewHost(count, cloud_profile, instance_size, roles, hostname, security_groups));
        };
        self.removeHost = function (host) {
            self.newHosts.remove(host);
        };

        self.launchedHosts = ko.observableArray([]);
        self.providers = ko.observableArray([]);
        self.providerAccounts = ko.observableArray([]);
        self.instanceSizes = ko.observableArray([]);

        // id, url, title, description, slug, cloud_provider, default_instance_size, image_id, ssh_user
        self.accountProfiles = ko.observableArray([]);

        /*
         *  ==================================================================================
         *  M E T H O D S
         *  ==================================================================================
         */
        self.gotoSection = function (section) { 
            location.hash = section;
            self.currentSection(section);
        };

        self.profileSelected = function (profile) { 
            console.log(profile);
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

        self.showStackForm = function () {
            self.loadProfiles();
            $( "#stack-form-container" ).dialog( "open" );

        }

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
        }

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

    var InstanceSize = function (id, url, title, description, slug, provider_type, instance_id) {
        var self = this;
        self.id = id;
        self.url = url;
        self.title = title;
        self.description = description;
        self.slug = slug;
        self.provider_type = provider_type;
        self.instance_id = instance_id;
        self.security_groups = security_groups;
    };



    ko.applyBindings(new stackdioModel());

});