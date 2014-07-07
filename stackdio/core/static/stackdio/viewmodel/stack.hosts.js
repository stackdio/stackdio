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
        self.id = 'stack.hosts';
        self.templatePath = 'stack.hosts.html';
        self.domBindingId = '#stack-hosts';

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
            $('#stack-tabs a[id="hosts"]').tab('show');

            self.stackPropertiesStringified('');

            if (data.hasOwnProperty('stack')) {
                self.editMode('update');

                stack = StackStore.collection().filter(function (s) {
                    return s.id === parseInt(data.stack, 10);
                })[0];
                
                // Find the corresponding blueprint
                blueprint = BlueprintStore.collection().filter(function (b) {
                    return b.url === stack.blueprint;
                })[0];

                self.stackTitle(stack.title);

                self.blueprintHostDefinitions(blueprint.host_definitions);

            } else {
                $galaxy.transport('stack.list');
            }

            self.selectedStack(stack);
            self.loadHosts();
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

        self.loadHosts = function() {
            // Get the hosts for the stack
            API.StackHosts.load(self.selectedStack()).then(function (hosts) {
                self.StackHostStore.collection.removeAll();
                self.StackHostStore.add(hosts);
            }).then(function () {
                self.StackHostStore.collection.sort(function (left, right) {
                    return left.hostname < right.hostname ? -1 : 1;
                });
            });
        };

        self.addHosts = function(model, evt) {
            var record = self._getModifyHostsRecord(evt.target.form, 'add');
            self._modifyHosts(record);
        };

        self.removeHosts = function(model, evt) {
            var record = self._getModifyHostsRecord(evt.target.form, 'remove');
            self._modifyHosts(record);
        };

        self._modifyHosts = function(record) {
            API.StackHosts.modifyHosts(record).then(function() {
                formutils.clearForm('modify_hosts_form');
                setTimeout(self.loadHosts, 1000);
            });
        };

        self._getModifyHostsRecord = function(form, action) {
            var record = formutils.collectFormFields(form);
            return {
                action: action,
                stack: self.selectedStack(),
                host_definition: parseInt($('#host_definition').val(), 10),
                count: parseInt($('#host_count').val(), 10)
            };
        };
    };
    return new vm();
});
