define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/stores',
    'api/api'
],
function (Q, ko, base, _O_, stores, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stores = stores;
        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch', 'Delete'];
        self.stackHostActions = ['Stop', 'Terminate', 'Start'];
        self.selectedProfile = null;
        self.selectedAccount = null;
        self.selectedBlueprint = ko.observable({title:''});
        self.blueprintProperties = ko.observable();
        self.selectedStack = ko.observable();

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.list';
        self.templatePath = 'stacks.html';
        self.domBindingId = '#stack-list';
        self.autoLoad = false;
        self.defaultView = false;

        try {
            self.sixtysix.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        // This builds the HTML for the stack history popover element
        self.popoverBuilder = function (stack) {
            return stack.fullHistory.map(function (h) {
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

            API.Blueprints.getProperties(blueprint)
                .then(function (properties) {
                    self.blueprintProperties(properties);
                    self.blueprintHosts(blueprint.host_definitions);
                });

            self.showStackForm();
        };

        self.updateStack = function (obj, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var stack = self.selectedStack();

            stack.title = record.stack_title_edit.value;
            stack.description = record.stack_description_edit.value;
            stack.namespace = record.stack_namespace_edit.value;
            
            if (record.stack_properties_preview_edit.value !== '') {
                stack.properties = JSON.parse(record.stack_properties_preview_edit.value);
            }

            console.log(stack);

            API.Stacks.update(stack)
                .then(function () {
                    self.closeStackForm();
                    _O_.publish('stack.updated');
                });
        };

        self.provisionStack = function (a, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            var stack = {
                title: record.stack_title.value,
                description: record.stack_description.value,
                namespace: record.stack_namespace.value,
                blueprint: self.selectedBlueprint().id
            };

            if (record.stack_properties_preview.value !== '') {
                stack.properties = JSON.parse(record.stack_properties_preview.value);
            }

            API.Stacks.save(stack)
                .then(function () {
                    self.closeStackForm();
                    _O_.publish('stack.updated');
                });
        };

        self.showStackDetails = function (stack) {
            self.selectedStack(stack);

            API.Stacks.getProperties(stack)
                .then(function (properties) {
                    $('#stack_properties_preview_edit').val(JSON.stringify(properties, undefined, 3));
                }).done();

            $('#stack_title_edit').val(stack.title);
            $('#stack_description_edit').val(stack.description);
            $('#stack_namespace_edit').val(stack.id);

            
            API.StackHosts.load(stack)
                .then(function (response) {
                    $("#stack-edit-container").dialog("open");
                });
        };

        // 
        //      S T A C K   H O S T S
        // 
        self.showStackHostMetaData = function (stack) {
            console.log(stack);
            API.Stacks.getHosts(stack).then(function (data) {

            });

            // stores.HostMetadata.removeAll();
            // _.each(host.ec2_metadata, function (v, k, l) {
            //     if (typeof v !== "object") {
            //         stores.HostMetadata.push({ key: k, value: v });
            //     }
            // });

            // $("#host-metadata-container").dialog("open");
        };

        self.showStackDetails = function (stack) {
            _O_.publish('navigate', { view: 'stack.details', stack: stack });
        };

    };

    vm.prototype = new base();
    return new vm();
});
