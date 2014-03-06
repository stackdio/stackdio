define(['q', 'knockout', 'util/galaxy', 'viewmodel/stacklist', 'store/Blueprints'],
function (Q, ko, $galaxy, stacklist, BlueprintStore) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'welcome';
        self.templatePath = 'welcome.html';
        self.domBindingId = '#welcome';
        self.children = [stacklist];
        self.defaultView = true;

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
        $galaxy.network.subscribe(self.id + '.docked', function () {
            BlueprintStore.populate().then(function () {
                // Specify a flattened array of Blueprint name as the store for the typeahead on the welcome page
                $('#blueprint_search').typeahead({
                    name: 'blueprints',
                    local: BlueprintStore.collection().map(function (b) {return b.title; }),
                    limit: 10
                }).on('typeahead:selected', function (object, selectedItem) {
                    var foundBlueprint = _.findWhere(BlueprintStore.collection(), { title: $('#blueprint_search').val() });
                    $galaxy.transport({
                        view: 'stack.detail',
                        data: {
                            blueprint: foundBlueprint.id
                        }
                    });
                });
            });



            // When user presses enter in the Launch Blueprint typeahead, start the process of launching a Stack
            $("#blueprint_search").keypress(function (evt) {
                if (evt.keyCode === 13) {
                    var foundBlueprint = _.findWhere(BlueprintStore.collection(), { title: $('#blueprint_search').val() });
                    $galaxy.transport({
                        location: 'stack.detail',
                        payload: {
                            blueprint: foundBlueprint.id
                        }
                    });
                }
            });
        });
    };
    return new vm();
});
