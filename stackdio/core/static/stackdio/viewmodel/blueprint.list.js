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
            V I E W   V A R I A B L E S
        */
        var self = this;
        self.stores = stores;


        /*
            R E G I S T R A T I O N   S E C T I O N
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
            V I E W   M E T H O D S
        */


    };

    vm.prototype = new base();
    return new vm();
});
