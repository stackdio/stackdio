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
        self.id = 'stack.logs';
        self.templatePath = 'stack.logs.html';
        self.domBindingId = '#stack-logs';

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
            $('#stack-tabs a[id="logs"]').tab('show');

            self.stackPropertiesStringified('');

            if (data.hasOwnProperty('stack')) {
                self.editMode('update');

                stack = StackStore.collection().filter(function (s) {
                    return s.id === parseInt(data.stack, 10);
                })[0];

                self.stackTitle(stack.title);

                API.Stacks.getLogs(stack).then(function (logs) {
                    self.logObject = logs;
                    self.getLogs();
                }).catch(function(error) {
                    console.error(error);
                }).done();

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


        self.getLogs = function () {
            // Query param ?tail=20&head=20

            var promises = [];
            var historical = [];

            self.logObject.historical.forEach(function (url) {
                promises[promises.length] = API.Stacks.getLog(url).then(function (log) {
                    historical[historical.length] = log;
                });
            });

            Q.all(promises).then(function () {
                $('#historical_logs').text(historical.join(''));
            }).catch(function (error) {
                console.log('error', error.toString());
            }).done();

            API.Stacks.getLog(self.logObject.latest.launch).then(function (log) {
                $('#launch_logs').text(log);
            }).catch(function (error) {
                $('#launch_logs').text(error);
            });

            API.Stacks.getLog(self.logObject.latest.orchestration).then(function (log) {
                $('#orchestration_logs').text(log);
            }).catch(function (error) {
                $('#orchestration_logs').text(error);
            });

            API.Stacks.getLog(self.logObject.latest["orchestration-error"]).then(function (log) {
                $('#orchestration_error_logs').text(log);
            }).catch(function (error) {
                $('#orchestration_error_logs').text(error);
            });

            API.Stacks.getLog(self.logObject.latest.provisioning).then(function (log) {
                $('#provisioning_logs').text(log);
            }).catch(function (error) {
                $('#provisioning_logs').text(error);
            });

            API.Stacks.getLog(self.logObject.latest["provisioning-error"]).then(function (log) {
                $('#provisioning_error_logs').text(log);
            }).catch(function (error) {
                $('#provisioning_error_logs').text(error);
            });            
        };

    };
    return new vm();
});
