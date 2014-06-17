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
        self.id = 'stack.detail';
        self.templatePath = 'stack.html';
        self.domBindingId = '#stack-detail';

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
            $('#stack-tabs a:first').tab('show');

            self.stackPropertiesStringified('');

            // Blueprint specified, so creating a new stack
            if (data.hasOwnProperty('blueprint')) {
                self.editMode('create');

                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10);
                })[0];

                API.Blueprints.getProperties(blueprint).then(function (properties) {
                    var stringify = JSON.stringify(properties, undefined, 3);
                    self.blueprintProperties(properties);
                    self.stackPropertiesStringified(stringify);
                });

                self.blueprintTitle(blueprint.title);
                self.selectedBlueprint(blueprint);
            }

            if (data.hasOwnProperty('stack')) {
                self.editMode('update');

                stack = StackStore.collection().filter(function (s) {
                    return s.id === parseInt(data.stack, 10);
                })[0];

                self.stackTitle(stack.title);

                // Populate the form
                $('#stack_title').val(stack.title);
                $('#stack_description').val(stack.description);
                $('#stack_namespace').val(stack.namespace);

                // Get stack properties
                API.Stacks.getProperties(stack).then(function (properties) {
                    $('#stack_properties_preview').val(JSON.stringify(properties, undefined, 3));
                }).then(function () {
                    return API.Stacks.getLogs(stack);
                }).then(function (logs) {
                    self.logObject = logs;
                    self.getLogs();
                }).catch(function(error) {
                    console.error(error);
                }).done();

                // Get security groups 
                getSecurityGroups(stack);

                // Get actions
                getActions(stack);

                // Find the corresponding blueprint
                blueprint = BlueprintStore.collection().filter(function (b) {
                    return b.url === stack.blueprint;
                })[0];

                // Get the hosts for the stack
                self.StackHostStore.collection.removeAll();
                API.StackHosts.load(stack).then(function (hosts) {
                    self.StackHostStore.add(hosts);
                }).then(function () {
                    self.StackHostStore.collection.sort(function (left, right) {
                        return left.hostname < right.hostname ? -1 : 1;
                    });
                });

                // Update observables
                self.selectedBlueprint(blueprint);
                self.blueprintTitle(blueprint.title);
            } else {
                self.stackTitle('New Stack');
            }

            self.selectedStack(stack);
        };
    
        self.addRule = function (obj, evt) {
            var curId = evt.target.form.id;
            var col = self.StackSecurityGroupStore.collection();
            var curGroup = null;

            for (var i = 0; i < col.length; ++i) {
                if (col[i].id.toString() === curId) {
                    curGroup = col[i];
                    break;
                }
            }
            
            var record = formutils.collectFormFields(evt.target.form);
            
            var from_port = null;
            var to_port = null;

            if (record.add_rule_port_range.value.indexOf("-") > -1) {
                var spl = record.add_rule_port_range.value.split("-");
                from_port = parseInt(spl[0]);
                to_port = parseInt(spl[1]);
            } else {
                from_port = parseInt(record.add_rule_port_range.value);
                to_port = from_port;
            }

            API.SecurityGroups.updateRule(curGroup, {
                "action" : "authorize",
                "protocol": record.add_rule_protocol.value,
                "from_port": from_port,
                "to_port": to_port,
                "rule": record.add_rule_ip_address.value === "" ? record.add_rule_group.value : record.add_rule_ip_address.value
            }).then(function () {
                formutils.clearForm(curId);
                getSecurityGroups(self.selectedStack());
            });
        };

        self.deleteRule = function (obj, evt) {
            var curId = evt.target.form.id.split("_")[0];
            var col = self.StackSecurityGroupStore.collection();
            var curGroup = null;

            for (var i = 0; i < col.length; ++i) {
                if (col[i].id.toString() === curId) {
                    curGroup = col[i];
                    break;
                }
            }

            var record = formutils.collectFormFields(evt.target.form);

            API.SecurityGroups.updateRule(curGroup, {
                "action" : "revoke",
                "protocol": record.rule_protocol.value,
                "from_port": parseInt(record.rule_from_port.value),
                "to_port": parseInt(record.rule_to_port.value),
                "rule": record.rule_rule.value
            }).then(function () {
                getSecurityGroups(self.selectedStack());
            });

        }

        function getSecurityGroups(stack) {
            API.Stacks.getSecurityGroups(stack).then(function (groups) {
                
                groups.results.forEach(function (group) {
                    group.rules.forEach(function (rule) {
                        rule.uid = group.id + "_" + rule.protocol + "-" + rule.from_port + "-" + rule.to_port;
                    });
                });

                self.StackSecurityGroupStore.collection.removeAll();
                self.StackSecurityGroupStore.add(groups.results);
            }).then(function () {
                self.StackSecurityGroupStore.collection.sort(function (left, right) {
                    return left.blueprint_host_definition.title < right.blueprint_host_definition.title ? -1 : 1;   
                });
            });

        }

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
                    action.host_target,
                    action.command
                ]
            };

            startAction(data);
        };

        self.runAction = function (obj, evt) {
            var record = formutils.collectFormFields(evt.target.form);
        
            var data = {
                action: "custom",
                args: [
                    record.host_target.value,
                    record.command.value
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

        self.updateStack = function (obj, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var stack = {};

            // Create a new, complete stack representation for a PUT
            stack.id = self.selectedStack().id;
            stack.url = self.selectedStack().url;
            stack.owner = self.selectedStack().owner;
            stack.host_count = self.selectedStack().host_count;
            stack.volume_count = self.selectedStack().volume_count;
            stack.created = self.selectedStack().created;
            stack.blueprint = self.selectedStack().blueprint;
            stack.fqdns = self.selectedStack().fqdns;
            stack.hosts = self.selectedStack().hosts;
            stack.volumes = self.selectedStack().volumes;
            stack.properties = self.selectedStack().properties;
            stack.history = self.selectedStack().history;
            stack.title = record.stack_title.value;
            stack.description = record.stack_description.value;
            stack.namespace = record.stack_namespace.value;
            
            if (record.stack_properties_preview.value !== '') {
                stack.properties = JSON.parse(record.stack_properties_preview.value);
            }

            API.Stacks.update(stack).then(function (newStack) {
                self.StackStore.remove(self.selectedStack());
                self.StackStore.add(newStack);
                formutils.clearForm('stack-launch-form');
                $galaxy.transport('stack.list');
            });
        };

        self.provisionStack = function (a, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            var stack = {
                title: record.stack_title.value,
                description: record.stack_description.value,
                blueprint: self.selectedBlueprint().id
            };

            // Only send in the namespace if user provided one
            if(record.stack_namespace.value != '') {
                stack.namespace = record.stack_namespace.value;
            }

            if (record.stack_properties_preview.value !== '') {
                stack.properties = JSON.parse(record.stack_properties_preview.value);
            }

            API.Stacks.save(stack).then(function (newStack) {
                self.StackStore.add(newStack);
                
                $('#stack_title').val('');
                $('#stack_description').val('');
                $('#stack_namespace').val('');
                $('#stack_properties_preview').text('');

                $galaxy.transport('stack.list');
            });
        };

        self.cancelChanges = function (a, evt) {
            formutils.clearForm('stack-launch-form');
            $galaxy.transport('stack.list');
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
