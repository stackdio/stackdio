define([
    'q', 
    'knockout',
    'util/galaxy',
    'api/api'
],
function (Q, ko, $galaxy, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedStack = ko.observable(null);
        self.stackTitle = ko.observable();

        self.latestLogs = ko.observableArray([]);
        self.historicalLogs = ko.observableArray([]);
        self.selectedLog = ko.observable();
        self.selectedLogText = ko.observable('Loading...');

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
            self.init(data);
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {

            if (data.hasOwnProperty('stack')) {

                API.Stacks.getStack(data.stack).then(function (stack) {

                    self.selectedStack(stack);

                    self.stackTitle(stack.title);

                    API.Stacks.getLogs(stack).then(function (logs) {
                        self.logObject = logs;
                        self.historicalLogs.removeAll();
                        self.logObject.historical.forEach(function(logrecord) {
                            urlarr = logrecord.split('/');
                            self.historicalLogs.push({
                                name: urlarr[urlarr.length-1],
                                url: logrecord
                            });
                        });
                        self.latestLogs.removeAll();
                        self.latestLogs.push({
                            name: 'Launch',
                            url: self.logObject.latest.launch
                        });
                        self.latestLogs.push({
                            name: 'Provisioning',
                            url: self.logObject.latest.provisioning
                        });
                        self.latestLogs.push({
                            name: 'Provisioning Error',
                            url: self.logObject.latest['provisioning-error']
                        });
                        self.latestLogs.push({
                            name: 'Orchestration',
                            url: self.logObject.latest.orchestration
                        });
                        self.latestLogs.push({
                            name: 'Orchestration Error',
                            url: self.logObject.latest['orchestration-error']
                        });

                        // Start out with the latest launch log
                        self.goToLog(self.latestLogs()[0]);
                    }).catch(function(error) {
                        console.error(error);
                    }).done();
                });

            } else {
                $galaxy.transport('stack.list');
            }

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


        self.goToLog = function(obj, evt) {
            self.selectedLog(obj.name);
            self.selectedLogText("Loading...");
            API.Stacks.getLog(obj.url).then(function (log) {
                self.selectedLogText(log);
            });
        };

    };
    return new vm();
});
