define(["knockout",
        "util/form",
        "viewmodel/abstract",
        "model/models",
        "store/stores",
        "api/api"], 
    function (ko, formutils, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;

            self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch', 'Delete'];
            self.stackHostActions = ['Stop', 'Terminate', 'Start'];
            self.selectedProfile = null;
            self.selectedAccount = null;
            self.selectedBlueprint = ko.observable({title:''});
            self.blueprintProperties = ko.observable();

            // This builds the HTML for the stack history popover element
            self.popoverBuilder = function (stack) { 
                return stack.history.map(function (h) {
                    var content = [];

                    content.push("<div class=\'dotted-border xxsmall-padding\'>");
                    content.push("<div");
                    if (h.level === 'ERROR') {
                        content.push(" class='btn-danger'");
                    
                    }
                    content.push('>');
                    content.push(h.status);
                    content.push('</div>');
                    content.push("<div class='grey'>");
                    content.push(moment(h.created).fromNow());
                    content.push('</div>');
                    content.push('</div>');

                    return content.join('');

                }).join('');
            };

            self.doStackAction = function (action, evt, stack) {
                var data = JSON.stringify({
                    action: action.toLowerCase()
                });

                /* 
                 *  Unless the user wants to delete the stack permanently (see below)
                 *  then just PUT to the API with the appropriate action.
                 */
                if (action !== 'Delete') {
                    $.ajax({
                        url: '/api/stacks/' + stack.id + '/',
                        type: 'PUT',
                        data: data,
                        headers: {
                            "X-CSRFToken": stackdio.settings.csrftoken,
                            "Accept": "application/json",
                            "Content-Type": "application/json"
                        },
                        success: function (response) {
                            API.Stacks.load();
                        }
                    });

                /*
                 *  Using the DELETE verb is truly destructive. Terminates all hosts, terminates all 
                 *  EBS volumes, and deletes stack/host details from the stackd.io database.
                 */
                } else {
                    $.ajax({
                        url: '/api/stacks/' + stack.id + '/',
                        type: 'DELETE',
                        headers: {
                            "X-CSRFToken": stackdio.settings.csrftoken,
                            "Accept": "application/json",
                            "Content-Type": "application/json"
                        },
                        success: function (response) {
                            stores.Stacks.remove(function (s) {
                                return s.id === stack.id;
                            });
                        }
                    });
                    
                }

            };

            self.launchStack = function (blueprint) {
                self.selectedBlueprint(blueprint);

                API.Blueprints.getProperties(blueprint.id)
                    .then(function (properties) {
                        self.blueprintProperties(properties);
                        self.blueprintHosts(blueprint.host_definitions);
                    });

                self.showStackForm();
            };

            self.provisionStack = function (a, evt) {
                var record = formutils.collectFormFields(evt.target.form);


                var stack = {
                    title: record.stack_title.value,
                    description: record.stack_description.value,
                    namespace: record.stack_namespace.value,
                    properties: JSON.parse(record.stack_properties_preview.value),
                    blueprint: self.selectedBlueprint().id
                };

                API.Stacks.save(stack)
                    .then(function () {
                        self.closeStackForm();
                    });

            };

            self.showStackForm = function (blueprint) {
                self.selectedBlueprint(blueprint);
                $("#stack-launch-container").dialog("open");
            };

            self.closeStackForm = function () {
                $("#stack-launch-container").dialog("close");
            };

            self.showStackDetails = function (stack) {
                API.StackHosts.load(stack)
                    .then(function (response) {
                        self.showStackHosts();
                        $('select').selectpicker();
                    });
                return;
            };

            // 
            //      S T A C K   H O S T S
            // 
            self.showStackHostMetaData = function (stack) {
                console.log(stack);
                API.Stacks.getHosts(stack)
                    .then(function (data) {

                    });


                // stores.HostMetadata.removeAll();
                // _.each(host.ec2_metadata, function (v, k, l) {
                //     if (typeof v !== "object") {
                //         stores.HostMetadata.push({ key: k, value: v });
                //     }
                // });

                // $("#host-metadata-container").dialog("open");
            };

            self.closeHostMetadata = function () {
                $("#host-metadata-container").dialog("close");
            };


            self.showStackHosts = function () {
                $("#stack-details-container").dialog("open");
            };

            self.closeStackHosts = function () {
                $("#stack-details-container").dialog("close");
            };


            /*
             *  ==================================================================================
             *  D I A L O G   E L E M E N T S
             *  ==================================================================================
             */
            $("#stack-details-container").dialog({
                autoOpen: false,
                width: 650,
                modal: false
            });

            $("#stack-launch-container").dialog({
                autoOpen: false,
                width: 650,
                modal: false
            });

            $("#host-metadata-container").dialog({
                autoOpen: false,
                width: 500,
                height: 600,
                modal: true
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});
