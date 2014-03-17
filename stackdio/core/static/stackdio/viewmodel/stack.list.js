define(['q', 'knockout', 'util/galaxy', 'util/alerts', 'store/Blueprints', 'store/Stacks', 'api/api'],
function (Q, ko, $galaxy, alerts, BlueprintStore, StackStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch', 'Delete', 'Provision'];
        self.stackHostActions = ['Stop', 'Terminate', 'Start'];
        self.selectedProfile = null;
        self.selectedAccount = null;
        self.selectedBlueprint = ko.observable({title:''});
        self.blueprintProperties = ko.observable();
        self.selectedStack = ko.observable();
        self.BlueprintStore = BlueprintStore;
        self.StackStore = StackStore;
        self.$galaxy = $galaxy;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.list';
        self.templatePath = 'stacks.html';
        self.domBindingId = '#stack-list';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }

        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            BlueprintStore.populate().then(function () {
                $('span').popover('hide');
                return StackStore.populate(true);
            }).catch(function (err) {
                console.error(err);
            });
        });

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
                    url: stack.url,
                    type: 'PUT',
                    data: data,
                    headers: {
                        "X-CSRFToken": stackdio.settings.csrftoken,
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    success: function (response) {
                        alerts.showMessage('#success', 'Stack is currently being torn down and will deleted soon.', true);
                        StackStore.populate();
                    }
                });

            /*
             *  Using the DELETE verb is truly destructive. Terminates all hosts, terminates all 
             *  EBS volumes, and deletes stack/host details from the stackd.io database.
             */
            } else {
                $.ajax({
                    url: stack.url,
                    type: 'DELETE',
                    headers: {
                        "X-CSRFToken": stackdio.settings.csrftoken,
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    success: function (response) {
                        alerts.showMessage('#success', 'Stack is currently being torn down and will be deleted once all hosts are terminated.', true, 5000);
                        StackStore.populate();
                    },
                    error: function (request, status, error) {
                        alerts.showMessage('#error', 'Unable to delete this stack.', true, 2000);
                    }
                });
            }
        };

        self.showStackDetails = function (stack) {
            self.selectedStack(stack);

            API.Stacks.getProperties(stack).then(function (properties) {
                $('#stack_properties_preview_edit').val(JSON.stringify(properties, undefined, 3));
            }).done();

            $('#stack_title_edit').val(stack.title);
            $('#stack_description_edit').val(stack.description);
            $('#stack_namespace_edit').val(stack.id);

            
            API.StackHosts.load(stack).then(function (response) {
                $("#stack-edit-container").dialog("open");
            });
        };

        self.showStackDetails = function (stack) {
            $galaxy.transport({
                location: 'stack.detail',
                payload: {
                    stack: stack.id
                }
            });
        };

        self.createNewStack = function (blueprint) {
            API.Users.load().then(function (public_key) {
                if (public_key === '') {
                    alerts.showMessage('#error', 'You have not saved your public key, and cannot launch any new stacks. Please open your user profile to save one.', true, 4000);
                } else {
                    $galaxy.transport({
                        location: 'stack.detail', 
                        payload: { 
                            blueprint: blueprint.id 
                        }
                    });
                }
            });
        };

    };
    return new vm();
});
