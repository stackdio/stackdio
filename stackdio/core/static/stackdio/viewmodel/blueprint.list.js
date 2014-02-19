define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'api/api',
    'store/BlueprintComponents',
    'store/BlueprintHosts',
    'store/Blueprints'
],
function (Q, ko, base, _O_, API, BlueprintComponentStore, BlueprintHostStore, BlueprintStore) {
    console.log(arguments);
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
            self.$66.register(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        _O_.subscribe('blueprint.list.rendered', function (data) {
            BlueprintStore.populate().then(function () {
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */
        self.editBlueprint = function (blueprint) {
            self.navigate({ view: 'blueprint.detail', data: { blueprint: blueprint.id } });
        };

        self.deleteBlueprint = function (blueprint) {
            API.Blueprints.delete(blueprint)
                .then(self.showSuccess)
                .catch(function (error) {
                    self.showError(error);
                });
        };

        self.newBlueprint = function () {
            $('#blueprint_title').val('');
            $('#blueprint_purpose').val('');
            BlueprintHostStore.empty();
            BlueprintComponentStore.empty();

            self.navigate({ view: 'blueprint.detail' });
        }

    };

    vm.prototype = new base();
    return new vm();
});
