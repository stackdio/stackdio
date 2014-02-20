define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/Stacks',
    'store/Profiles',
    'store/InstanceSizes',
    'store/Blueprints',
    'store/BlueprintHosts',
    'store/BlueprintComponents',
    'api/api'
],
function (Q, ko, base, _O_, formutils, StackStore, ProfileStore, InstanceSizeStore, BlueprintStore, BlueprintHostStore, BlueprintComponentStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedBlueprint = ko.observable(null);
        self.stackTitle = ko.observable();
        self.blueprintTitle = ko.observable();
        self.blueprintProperties = ko.observable();
        self.blueprintPropertiesStringified = ko.observable();

        self.StackStore = StackStore;
        self.ProfileStore = ProfileStore;
        self.InstanceSizeStore = InstanceSizeStore;
        self.BlueprintHostStore = BlueprintHostStore;
        self.BlueprintComponentStore = BlueprintComponentStore;
        self.BlueprintStore = BlueprintStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.detail';
        self.templatePath = 'stack.html';
        self.domBindingId = '#stack-detail';

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
        _O_.subscribe('stack.detail.rendered', function (data) {
            BlueprintStore.populate().then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var blueprint = null;
            var stack = null;

            console.log(BlueprintStore.collection());

            // Blueprint specified, so creating a new stack
            if (data.hasOwnProperty('blueprint')) {
                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10);
                })[0];

                API.Blueprints.getProperties(blueprint).then(function (properties) {
                    console.log(properties);
                    var stringify = JSON.stringify(properties, undefined, 3);
                    self.blueprintPropertiesStringified(stringify);
                });

                self.blueprintTitle(blueprint.title);
                self.selectedBlueprint(blueprint);
            }

            if (data.hasOwnProperty('stack')) {
                stack = StackStore.collection().map(function (s) {
                    return s.id === parseInt(data.stack, 10);
                })[0];
                self.stackTitle(stack.title);
            } else {
                self.stackTitle('New Stack');
            }
            self.selectedStack(stack);
        };

        self.updateStack = function (obj, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var stack = self.selectedStack();

            stack.title = record.stack_title_edit.value;
            stack.description = record.stack_description_edit.value;
            stack.namespace = record.stack_namespace_edit.value;
            
            if (record.stack_properties_preview_edit.value !== '') {
                stack.properties = JSON.parse(record.stack_properties_preview_edit.value);
            }

            console.log(stack);
            return;

            API.Stacks.update(stack).then(function () {
                self.closeStackForm();
                _O_.publish('stack.updated');
            });
        };

        self.provisionStack = function (a, evt) {
            var record = formutils.collectFormFields(evt.target.form);

            var stack = {
                title: record.stack_title.value,
                description: record.stack_description.value,
                namespace: record.stack_namespace.value,
                blueprint: self.selectedBlueprint().id
            };

            if (record.stack_properties_preview.value !== '') {
                stack.properties = JSON.parse(record.stack_properties_preview.value);
            }

            API.Stacks.save(stack).then(function (newStack) {
                self.StackStore.add(newStack);
                formutils.clearForm('stack-launch-form');
                self.navigate({ view: 'stack.list' });
            });
        };

        self.cancelChanges = function (a, evt) {
            formutils.clearForm('stack-launch-form');
            self.navigate({ view: 'stack.list' });
        };
    };

    vm.prototype = new base();
    return new vm();
});
