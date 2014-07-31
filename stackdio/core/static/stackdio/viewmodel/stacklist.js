define(['q', 'knockout', 'bootbox', 'moment', 'util/galaxy', 'util/stack', 'store/Stacks', 'api/api'],
function (Q, ko, bootbox, moment, $galaxy, stackutils, StackStore, API) {
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
            
            StackStore.populate(true).then(function () {
                StackStore.collection().forEach(function (stack) {
                    self.EnhancedStackStore.push(stack);
                });
            }).done();
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        // This builds the HTML for the stack history popover element
        self.popoverBuilder = stackutils.popoverBuilder;

        // Performs actions on a stack
        self.doStackAction = stackutils.doStackAction;

        self.showStackDetails = stackutils.showStackDetails;

        self.getStatusType = stackutils.getStatusType;
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
