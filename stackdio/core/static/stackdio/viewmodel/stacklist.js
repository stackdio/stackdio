define([
    'q', 
    'knockout',
    'moment',
    'util/galaxy',
    'store/Stacks',
    'api/api'
],
function (Q, ko, moment, $galaxy, StackStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.StackStore = StackStore;
        self.EnhancedStackStore = ko.observableArray();
        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch', 'Delete'];


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'stacklist.widget';
        self.templatePath = 'stacklist.html';
        self.domBindingId = '.stacklist';
        self.autoLoad = false;
        self.defaultView = false;

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }

        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            self.EnhancedStackStore.removeAll();
            
            StackStore.populate().then(function () {
                StackStore.collection().forEach(function (stack) {
                    API.Stacks.getHistory(stack).then(function (stackwithhistory) {
                        self.EnhancedStackStore.push(stackwithhistory);
                    });
                });
            }).done();
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

        // Performs actions on a stack
        self.doStackAction = function (action, evt, stack) {
            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            /* 
             *  Unless the user wants to delete the stack permanently (see below)
             *  then just PUT to the API with the appropriate action.
             */
                console.log(stack);
            if (action !== 'Delete') {
                // $.ajax({
                //     url: '/api/stacks/' + stack.id + '/',
                //     type: 'PUT',
                //     data: data,
                //     headers: {
                //         "X-CSRFToken": stackdio.settings.csrftoken,
                //         "Accept": "application/json",
                //         "Content-Type": "application/json"
                //     },
                //     success: function (response) {
                //         API.Stacks.load();
                //     }
                // });

            /*
             *  Using the DELETE verb is truly destructive. Terminates all hosts, terminates all 
             *  EBS volumes, and deletes stack/host details from the stackd.io database.
             */
            } else {
                // $.ajax({
                //     url: '/api/stacks/' + stack.id + '/',
                //     type: 'DELETE',
                //     headers: {
                //         "X-CSRFToken": stackdio.settings.csrftoken,
                //         "Accept": "application/json",
                //         "Content-Type": "application/json"
                //     },
                //     success: function (response) {
                //         stores.Stacks.remove(function (s) {
                //             return s.id === stack.id;
                //         });
                //     }
                // });
            }
        };

        self.showStackDetails = function (stack) {
            $galaxy.transport({ location: 'stack.detail', payload: {stack: stack.id}});
        };
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
