define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Stacks',
    'store/StackHosts',
    'store/StackSecurityGroups',
    'store/StackActions',
    'store/Profiles',
    'store/InstanceSizes',
    'store/Blueprints',
    'store/BlueprintHosts',
    'store/BlueprintComponents',
    'api/api'
],
function (Q, ko, $galaxy, formutils, StackStore, StackHostStore, StackSecurityGroupStore, StackActionStore, ProfileStore, InstanceSizeStore, BlueprintStore, BlueprintHostStore, BlueprintComponentStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedBlueprint = ko.observable(null);
        self.blueprintHostDefinitions = ko.observable(null);
        self.selectedStack = ko.observable(null);
        self.stackTitle = ko.observable();
        self.blueprintTitle = ko.observable();
        self.blueprintProperties = ko.observable();
        self.stackPropertiesStringified = ko.observable();
        self.editMode = ko.observable('create');

        self.historicalLogText = ko.observable();
        self.launchLogText = ko.observable();
        self.orchestrationLogText = ko.observable();
        self.orchestrationErrorLogText = ko.observable();
        self.provisioningLogText = ko.observable();
        self.provisioningErrorLogText = ko.observable();

        self.StackStore = StackStore;
        self.StackHostStore = StackHostStore;
        self.StackSecurityGroupStore = StackSecurityGroupStore;
        self.StackActionStore = StackActionStore;
        self.ProfileStore = ProfileStore;
        self.InstanceSizeStore = InstanceSizeStore;
        self.BlueprintHostStore = BlueprintHostStore;
        self.BlueprintComponentStore = BlueprintComponentStore;
        self.BlueprintStore = BlueprintStore;
        self.$galaxy = $galaxy;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.actions';
        self.templatePath = 'stack.actions.html';
        self.domBindingId = '#stack-actions';

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
                return StackStore.populate();
            }).then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var blueprint = null;
            var stack = null;
            var stackHosts = [];

            // Automatically select the first tab in the view so that if the user had
            // clicked on the logs or orchestraton tab previously, it doesn't end up
            // showing a blank view
            $('#stack-tabs a[id="actions"]').tab('show');

            self.stackPropertiesStringified('');

            if (data.hasOwnProperty('stack')) {
                self.editMode('update');

                stack = StackStore.collection().filter(function (s) {
                    return s.id === parseInt(data.stack, 10);
                })[0];

                self.stackTitle(stack.title);

                // Get actions
                getActions(stack);

            } else {
                $galaxy.transport('stack.list');
            }

            self.selectedStack(stack);
        };
 
        self.goToTab = function (obj, evt) {
            var tab=evt.target.id;
            $galaxy.transport({
                location: 'stack.'+tab,
                payload: {
                    stack: self.selectedStack().id
                }
            });
        };

        function getActions(stack) {
            API.Stacks.getActions(stack).then(function (actions) {
                self.StackActionStore.collection.removeAll();
                self.StackActionStore.add(actions.results);
            }).then(function () {
                self.StackActionStore.collection.sort(function (left, right) {
                    return left.id < right.id ? 1 : -1;
                });
            });
        }

        self.runActionAgain = function (action, evt) {

            var data = {
                action: "custom",
                args: [
                    {
                        host_target: action.host_target,
                        command: action.command
                    }
                ]
            };

            startAction(data);
        };

        self.runAction = function (obj, evt) {
            var record = formutils.collectFormFields(evt.target.form);
        
            var data = {
                action: "custom",
                args: [
                    {
                        host_target: record.host_target.value,
                        command: record.command.value
                    }
                ]
            };

           startAction(data);

           formutils.clearForm('action-form');
        };

        self.deleteAction = function (action, evt) {
            console.log(action);
            $.ajax({
                url: action.url,
                type: 'DELETE',
                headers: {
                    "Accept": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken
                },
                success: function (response) {
                    getActions(self.selectedStack());
                },
                error: function (response, status, error) {
                    alerts.showMessage('#error', 'Unable to delete command', true, 7000);
                }
            });

        };

        function startAction(data) {
             $.ajax({
                url: self.selectedStack().action,
                type: 'POST',
                data: JSON.stringify(data),
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    getActions(self.selectedStack());
                },
                error: function (request, status, error) {
                    console.log(error);
                    alerts.showMessage('#error', 'Unable to run command', true, 7000);
                }
            });

        }

        self.refreshActions = function () {
            getActions(self.selectedStack());
        };   

        self.goToAction = function (action) {
            $galaxy.transport({
                location: 'stack.action.detail',
                payload: {
                    stack: self.selectedStack().id,
                    action: action.id
                }
            });
        };

        self.getStatusType = function(status) {
            switch(status) {
                case 'waiting':
                    return 'info';
                case 'running':
                    return 'warning';
                case 'finished':
                    return 'success';
                default:
                    return 'default';
            }
	    };

    };
    return new vm();
});
