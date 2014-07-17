define([
    'q',
    'settings',
    'knockout',
    'bootbox',
    'util/alerts',
    'util/galaxy',
    'api/api',
    'model/models',
],
function (Q, settings, ko, bootbox, alerts, $galaxy, API, models) {
    var vm = function () {
        if (!settings.superuser) {
            $galaxy.transport('welcome');
        }

        var self = this;


        /*
           V I E W  V A R I A B L E S
        */
        self.tabs = ko.observableArray([
            {
                title: 'Stacks',
                url: settings.api.admin.stacks,
                view_name: 'stack.detail',
                param_name: 'stack',
                fields: ['Host Count'],
                actions: ['Stop', 'Terminate', 'Start', 'Launch', 'Delete', 'Provision']
            },
            {
                title: 'Blueprints',
                url: settings.api.admin.blueprints,
                view_name: 'blueprint.detail',
                param_name: 'blueprint',
                fields: ['public'],
                actions: ['Delete']
            },
            {
                title: 'Formulas',
                url: settings.api.admin.formulas,
                view_name: 'formula.detail',
                param_name: 'formula',
                fields: [],
                actions: ['Delete']
            },
            {
                title: 'Snapshots',
                url: settings.api.admin.snapshots,
                fields: ['size_in_gb'],
                actions: ['Delete']
            },
            {
                title: 'Volumes',
                url: settings.api.admin.volumes,
                fields: [],
                actions: ['Delete']
            }
        ]);

        self.selectedTab = ko.observable(self.tabs()[0]);

        self.selectedFields = ko.computed(function() {
            return self.selectedTab().fields;
        });

        self.actions = ko.computed(function() {
            return self.selectedTab().actions;
        });

        self.tableData = ko.observableArray();

        /*
            R E G I S T R A T I O N   S E C T I O N
        */
        self.id = 'admin';
        self.templatePath = 'admin.html';
        self.domBindingId = '#admin';
        self.children = [];

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);
        }

        /*
            F U N C T I O N S
        */

        self.switchTab = function(obj, evt) {
            
            self.tableData.removeAll();
            self.selectedTab(obj);

            $.ajax({
                url: obj.url,
                type: 'GET',
                headers: {
                    "Accept": "application/json",
                },
                success: function (response) {
                    if (obj.title === 'Stacks') {
                        var historyPromises = [];
                        var stacks = [];

                        response.results.forEach(function (stack) {
                            historyPromises[historyPromises.length] = API.Stacks.getHistory(stack).then(function (stackWithHistory) {
                                stacks[stacks.length] = new models.Stack().create(stackWithHistory);
                                stacks[stacks.length-1]['Host Count'] = stacks[stacks.length-1].host_count;
                            });
                        });

                        Q.all(historyPromises).then(function () {
                            // Make sure the user hasn't clicked away from the current tab
                            if (self.selectedTab() === obj) {
                                self.tableData(stacks);
                            }
                        }).done();
                    } else {
                        // Make sure the user hasn't clicked away from the current tab
                        if (self.selectedTab() === obj) {
                            self.tableData(response.results);
                        }
                    }
                },
                error: function (response, status, error) {
                    alerts.showMessage('#error', response.responseJSON.detail, true, 7000);
                }
            });
        };

        self.goToDetail = function(obj, evt) {
            var payload = {};
            payload[self.selectedTab().param_name] = obj.id;

            $galaxy.transport({
                location: self.selectedTab().view_name,
                payload: payload
            });

        };

        self.doAction = function(action, evt, parent) {

            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            /*
             *  Unless the user wants to delete the stack permanently (see below)
             *  then just POST to the API with the appropriate action.
             */

            var title = self.selectedTab().title;
            title = title.substring(0, title.length-1);
            if (action !== 'Delete') {
                bootbox.confirm("Please confirm that you want to perform this action on the stack.", function (result) {
                    if (result) {
                        $.ajax({
                            url: parent.action,
                            type: 'POST',
                            data: data,
                            headers: {
                                "X-CSRFToken": stackdio.settings.csrftoken,
                                "Accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            success: function (response) {
                                alerts.showMessage('#success', 'Stack ' + action.toLowerCase() + ' has been initiated.', true);
                                StackStore.populate(true);
                            },
                            error: function (request, status, error) {
                                alerts.showMessage('#error', 'Unable to perform ' + action.toLowerCase() + ' action on that stack. ' + JSON.parse(request.responseText).detail, true, 5000);
                            }
                        });
                    }
                });

            /*
             *  Using the DELETE verb is truly destructive. Terminates all hosts, terminates all
             *  EBS volumes, and deletes stack/host details from the stackd.io database.
             */
            } else {
                bootbox.confirm("Please confirm that you want to delete this "+title.toLowerCase()+". Be advised that this is a completely destructive act.", function (result) {
                    if (result) {
                        $.ajax({
                            url: parent.url,
                            type: 'DELETE',
                            headers: {
                                "X-CSRFToken": stackdio.settings.csrftoken,
                                "Accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            success: function (response) {
                                alerts.showMessage('#success', title+' is currently being deleted.', true, 5000);
                                // Reload the table
                                self.refresh();
                            },
                            error: function (request, status, error) {
                                alerts.showMessage('#error', request.responseJSON.detail, true, 5000);
                            }
                        });
                    }
                });
            }
        };

        self.refresh = function() {
            self.switchTab(self.selectedTab());
        };

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

        self.switchTab(self.tabs()[0]);

    };

    /*
     *  ==================================================================================
     *  C U S T O M   B I N D I N G S
     *  ==================================================================================
     */
    ko.bindingHandlers.bootstrapPopover = {
        init: function (element, valueAccessor, allBindingsAccessor, viewModel) {
            var options = valueAccessor();
            var defaultOptions = {};
            options = $.extend(true, {}, defaultOptions, options);
            options.trigger = "click";
            options.placement = "bottom";
            options.html = true;
            $(element).popover(options);
        }
    };

    return new vm();
});
