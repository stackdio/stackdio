define([
    'q', 
    'knockout',
    'util/postOffice',
    'viewmodel/base',
    'viewmodel/stacklist'
],
function (Q, ko, _O_, base, stacklist) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'welcome.main';
        self.templatePath = 'welcome.html';
        self.domBindingId = '#welcome';
        self.children = [stacklist];
        self.defaultView = true;

        _O_.subscribe('welcome.main.registered', function () {
        });

        _O_.subscribe('welcome.main.loaded', function () {
        });

        try {
            self.sixtysix.register(self);
        } catch (ex) {
            console.log(ex);            
        }

    };

    vm.prototype = new base();
    return new vm();
});
