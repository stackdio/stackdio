define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'store/stores',
    'api/api'
],
function (Q, ko, base, _O_, stores, API) {
    var vm = function () {

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        var self = this;
        self.stores = stores;


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
        _O_.subscribe('account.list.rendered', function (data) {
            if (stores.Accounts().length === 0) {
                [API.Accounts.load, API.Profiles.load].reduce(function (loadData, next) {
                    return loadData.then(next);
                }, Q([])).then(function () {
                    
                });
            }
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */
        self.editBlueprint = function (blueprint) {
            self.navigate({ view: 'blueprint.detail', data: { blueprint: blueprint.id } });
        };


    };

    vm.prototype = new base();
    return new vm();
});
