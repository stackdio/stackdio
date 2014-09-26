define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/alerts',
    'util/form',
    'util/util',
    'store/ProviderTypes',
    'store/Accounts',
    'store/GlobalFormulas',
    'api/api'
],
function (Q, ko, $galaxy, alerts, formutils, utils, ProviderTypeStore, AccountStore, GlobalFormulaStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
         */
        self.selectedAccount = ko.observable(null);
        self.selectedProviderType = ko.observable(null);
        self.accountTitle = ko.observable(null);
        self.saveAction = self.createAccount;
        self.componentOptions = ko.observableArray();
        self.addedComponents = ko.observableArray();
        self.globalProperties = ko.observable();
        self.$galaxy = $galaxy;

        self.ProviderTypeStore = ProviderTypeStore;
        self.AccountStore = AccountStore;
        self.GlobalFormulaStore = GlobalFormulaStore;


        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
         */
        self.id = 'account.globalorchestration';
        self.templatePath = 'globalOrchestration.html';
        self.domBindingId = '#account-globalorchestration';

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
            ProviderTypeStore.populate().then(function () {
                return AccountStore.populate();
            }).then(function () {
                return GlobalFormulaStore.populate();
            }).then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */


        function compare_order(l, r) {
            if (l.order < r.order) {
                return -1;
            } else if (l.order > r.order) {
                return 1;
            } else {
                if (l.sls_path < r.sls_path) {
                    return -1;
                } else {
                    return 1;
                }
            }
        }

        self.init = function (data) {
            var account = null;
            var provider_type = null;


            if (data.hasOwnProperty('account')) {
                account = AccountStore.collection().filter(function (a) {
                    return a.id === parseInt(data.account, 10);
                })[0];

                self.accountTitle(account.title);
                self.selectedAccount(account);
            }

            self.componentOptions.removeAll();
            self.addedComponents.removeAll();

            self.GlobalFormulaStore.collection().forEach(function (formula) {
                formula.components.forEach(function (component) {
                    component.formula = formula;
                    component.order = 0;
                    component.existing = false;

                    // Remove function
                    component.remove = function(obj, evt) {
                        self.componentOptions.push(component);
                        self.addedComponents.remove(component);
                        self.componentOptions.sort(compare_order);
                        self.addedComponents.sort(compare_order);
                    };

                    self.componentOptions.push(component);
                });
                self.componentOptions.sort(compare_order);
            });

            API.Accounts.getGlobalProperties(account).then(function (props) {
                self.globalProperties(JSON.stringify(props, null, 4));
            });

            API.Accounts.getGlobalComponents(account).then(function (components) {
                components.forEach(function (component) {
                    var matching = self.componentOptions().filter(function (item) { return item.id === component.component.id; } )[0];

                    self.componentOptions.remove(matching);
                    matching.order = component.order;
                    matching.existing = true;
                    // Add in the id in case we need it later to delete this component
                    matching.global_id = component.id;
                    self.addedComponents.push(matching);
                });
                self.addedComponents.sort(compare_order);
            });
        };

        self.addComponent = function (model, evt) {
            var selectedId = parseInt(document.getElementById('global_components').value);

            var selectedComponent = self.componentOptions().filter(function (component) {
                return component.id === selectedId;
            })[0];

            self.componentOptions.remove(selectedComponent);
            self.addedComponents.push(selectedComponent);

            API.Formulas.getProperties(selectedComponent.formula).then(function (properties) {
                var props = {};
                if (self.globalProperties() != null) {
                    props = JSON.parse(self.globalProperties());
                }
                self.globalProperties(JSON.stringify(utils.recursive_update(properties, props), null, 4));
            });
        };

        self.save = function () {
            var componentPromises = [];

            self.addedComponents().forEach(function (component) {
                componentPromises[componentPromises.length] = API.Accounts.addGlobalComponent(self.selectedAccount(), component);
            });

            self.componentOptions().forEach(function (component) {
                if (component.existing) {
                    componentPromises[componentPromises.length] = API.Accounts.deleteGlobalComponent(component.global_id);
                }
            });

            componentPromises[componentPromises.length] = API.Accounts.setGlobalProperties(self.selectedAccount(), self.globalProperties());

            Q.all(componentPromises).then(function() {
                $galaxy.transport('account.list');
            });

        };

    };
    return new vm();
});
