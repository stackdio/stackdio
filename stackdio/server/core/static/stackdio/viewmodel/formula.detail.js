define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/alerts',
    'store/Formulas',
    'api/api'
],
function (Q, ko, $galaxy, alerts, FormulaStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.FormulaStore = FormulaStore;
        self.formulaComponents = ko.observable();

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'formula.detail';
        self.templatePath = 'formula.detail.html';
        self.domBindingId = '#formula-detail';

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
            self.formulaComponents([]);
            API.Formulas.getFormula(data.formula).then(function (formula) {
                self.formulaComponents(formula.components);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.cancelChanges = function () {
            $galaxy.transport('formula.list');
        };
    };
    return new vm();
});
