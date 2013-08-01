$(document).ready(function () {

    /*
     *  V I E W   M O D E L
     */
    function stackdioModel() {
        var self = this;

        self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
        self.currentSection = ko.observable();

        /*
         *  C O L L E C T I O N S
         */
        self.stacks = ko.observableArray([]);
        self.newHosts = ko.observableArray([]);
        self.launchedHosts = ko.observableArray([]);
        self.providers = ko.observableArray([]);
        self.providerAccounts = ko.observableArray([]);
        self.accountProfiles = ko.observableArray([]);

        self.gotoSection = function (section) { 
            location.hash = section;
            self.currentSection(section);
        };

        /*
         *  N A V I G A T I O N   H A N D L E R
         */
        $.sammy(function() {
            this.get('#:section', function () {
                self.currentSection(this.params.section);
            });

            this.get('', function() { this.app.runRoute('get', '#Stacks') });
        }).run();

        /*
         *  A P I   C A L L S
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

                $('#stacks').dataTable({
                    "bPaginate": false,
                    "bLengthChange": false,
                    "bFilter": true,
                    "bSort": false,
                    "bInfo": false,
                    "bAutoWidth": true
                });
            }
        });

        self.loadProfiles = function () {
            $.ajax({
                url: '/api/profiles/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

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

                    console.log(self.accountProfiles());

                    // $('#stacks').dataTable({
                    //     "bPaginate": false,
                    //     "bLengthChange": false,
                    //     "bFilter": true,
                    //     "bSort": false,
                    //     "bInfo": false,
                    //     "bAutoWidth": true
                    // });
                }
            });
        }

    };

    /*
     *  D A T A   M O D E L S
     */
    var Stack = function (title, description, status, created, host_count, id, slug, user, url) {
        var self = this;
        self.title = ko.observable(title);
        self.description = ko.observable(description);
        self.status = ko.observable(status);
        self.created = created;
        self.host_count = host_count;
        self.id = id;
        self.slug = slug;
        self.user = user;
        self.url = url;
    };

    var AccountProfile = function (id, url, title, description, slug, cloud_provider, default_instance_size, image_id, ssh_user) {
        var self = this;
        self.cloud_provider = ko.observable(cloud_provider);
        self.title = ko.observable(title);
        self.description = ko.observable(description);
        self.default_instance_size = ko.observable(default_instance_size);
        self.image_id = image_id;
        self.ssh_user = ssh_user;
        self.id = id;
        self.slug = slug;
        self.url = url;
    };



    ko.applyBindings(new stackdioModel());

});