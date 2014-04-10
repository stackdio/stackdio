define(['q', 'knockout', 'bootbox', 'util/galaxy', 'api/api', 'store/BlueprintComponents', 'store/BlueprintHosts', 'store/Blueprints'],
function (Q, ko, bootbox, $galaxy, API, BlueprintComponentStore, BlueprintHostStore, BlueprintStore) {
    var vm = function () {
        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        var self = this;
        self.BlueprintStore = BlueprintStore;


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'blueprint.list';
        self.templatePath = 'blueprint.list.html';
        self.domBindingId = '#blueprint-list';

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
            BlueprintStore.populate().then(function () {}).catch(function (err) {console.error(err); });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */
        self.editBlueprint = function (blueprint) {
            BlueprintHostStore.empty();
            BlueprintComponentStore.empty();
            $galaxy.transport({
                location: 'blueprint.detail',
                payload: {
                    blueprint: blueprint.id
                }
            });
        };


        self.deleteBlueprint = function (blueprint) {
            bootbox.confirm("Please confirm that you want to delete this blueprint", function (result) {
                if (result) {
                    API.Blueprints.delete(blueprint).then(function () {
                        BlueprintStore.remove(blueprint);
                    }).catch(function (error) {
                        self.showMessage('#error', error, true, 3000);
                    });

                }
            });
        };

        self.newBlueprint = function () {
            $('#blueprint_title').val('');
            $('#blueprint_purpose').val('');
            BlueprintHostStore.empty();
            BlueprintComponentStore.empty();

            $galaxy.transport('blueprint.detail');
        }

        self.showMessage = function (id, content, autohide, delay) {
            var timeout = (autohide && typeof delay === 'undefined') ? 3000 : delay;
            if (typeof content !== 'undefined' && content !== '') $(id+'-content').append(content);
            $(id).removeClass('hide');
            if (autohide) setTimeout(function () { $(id).addClass('hide'); $(id+'-content').empty(); }, timeout);
        };

        self.refresh = function() {
            BlueprintStore.populate(true);
        };
    };
    return new vm();
});
