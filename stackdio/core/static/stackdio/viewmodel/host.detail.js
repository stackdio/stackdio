define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/Profiles',
    'store/Formulas',
    'store/InstanceSizes',
    'store/Blueprints',
    'store/Zones',
    'store/HostAccessRules',
    'store/HostVolumes',
    'store/BlueprintHosts',
    'store/FormulaComponents',
    'store/BlueprintComponents',
    'api/api',
    'model/models'
],
function (Q, ko, base, _O_, formutils, ProfileStore, FormulaStore, InstanceSizeStore, BlueprintStore, ZoneStore, 
          HostRuleStore, HostVolumeStore, BlueprintHostStore, FormulaComponentStore, BlueprintComponentStore, API, models) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedProfile = null;
        self.selectedBlueprint = ko.observable(null);
        self.blueprintProperties = ko.observable();
        self.blueprintPropertiesStringified = ko.observable();
        self.hostIsSpotInstance = ko.observable(false);

        self.ProfileStore = ProfileStore;
        self.FormulaStore = FormulaStore;
        self.InstanceSizeStore = InstanceSizeStore;
        self.BlueprintStore = BlueprintStore;
        self.ZoneStore = ZoneStore;
        self.HostRuleStore = HostRuleStore;
        self.HostVolumeStore = HostVolumeStore;
        self.BlueprintHostStore = BlueprintHostStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'host.detail';
        self.templatePath = 'host.html';
        self.domBindingId = '#host-detail';

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
        _O_.subscribe('host.detail.rendered', function (data) {

            // Ensure formulas are loaded
            FormulaStore.populate().then(function (formulas) {
                FormulaStore.collection().forEach(function (formula) {
                    for (var c in formula.components) {
                        FormulaComponentStore.add(new models.FormulaComponent().create(formula.components[c]));
                    }
                });
            });

            // Load instance sizes and availability zones
            InstanceSizeStore.populate();
            ZoneStore.populate();

            // Load profiles, and then blueprints
            ProfileStore.populate().then(function () {
                return BlueprintStore.populate();    
            }).then(function () {
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
            var profile = null;

            // $('#formula_components').selectpicker();
            // $('#host_instance_size').selectpicker();
            // $('#availability_zone').selectpicker();

            if (data.hasOwnProperty('blueprint')) {
                blueprint = BlueprintStore.collection().map(function (p) {
                    if (p.id === parseInt(data.blueprint, 10)) {
                        return p;
                    }
                }).reduce(function (p, c) {
                    if (p.hasOwnProperty('id')) {
                        return p;
                    }
                });

                self.selectedBlueprint(blueprint);
            }


            if (data.hasOwnProperty('profile')) {
                profile = ProfileStore.collection().map(function (p) {
                    if (p.id === parseInt(data.profile, 10)) {
                        return p;
                    }
                }).reduce(function (p, c) {
                    if (p.hasOwnProperty('id')) {
                        return p;
                    }
                });

                self.selectedProfile = profile;
            }

        };

        self.createHost = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var v, vol;

            // Create a new host definition
            var host = new models.BlueprintHost().create({ 
                id: '',
                formulas: [],
                title: 'title',
                description: 'description',
                count: parseInt(record.host_count.value, 10),
                size: parseInt(record.host_instance_size.value, 10),
                hostname_template: record.host_hostname.value,
                zone: parseInt(record.availability_zone.value, 10),
                cloud_profile: self.selectedProfile.id,
                access_rules: _.map(HostRuleStore.collection(), function (rule) { return rule; }),
                volumes: HostVolumeStore.collection(),
                formula_components: record.formula_components.map(function (g) { return { id: g.value.split('|')[1], order: 0 }; })
            });


            // Get the properties for each formula component the user chose
            record.formula_components.forEach(function (component) {
                var formulaId = parseInt(component.value.split('|')[0], 10);
                var componentId = parseInt(component.value.split('|')[1], 10);
                var propBuilder = self.blueprintProperties();

                // Find the formula matching the id chosen in the component field
                var formula = _.find(FormulaStore.collection(), function (formula) {
                    return formula.id === formulaId;
                });

                // Find the formula matching the id chosen in the component field
                var component = _.find(FormulaComponentStore.collection(), function (comp) {
                    return comp.id === componentId;
                });

                if (typeof _.findWhere(BlueprintComponentStore.collection(), { id: component.id }) === "undefined") {
                    BlueprintComponentStore.add(component);
                }

                host.formulas.push(formula);
            });


            // Add the instance size object to the host so the title can be displayed in UI
            host.instance_size = _.find(InstanceSizeStore.collection(), function (i) {
                return i.id === parseInt(record.host_instance_size.value, 10);
            });

            // Add some HTML to display for the chosen roles
            host.flat_components = _.map(record.formula_components, function (fc) { 
                return '<div style="line-height:15px !important;">' + fc.text + '</div>'; 
            }).join('');

            // Add some HTML to display for the chosen security groups
            host.flat_access_rules = HostRuleStore.collection().length + ' access rules';

            // Add spot instance config
            if (record.spot_instance_price.value !== '') {
                host.spot_config = {};
                host.spot_config.spot_price = parseFloat(record.spot_instance_price.value);
            }

            // Request the forumula properties
            var formulaPromises = [];
            var propBuilder = {};

            host.formulas.forEach(function (formula) {
                var promise = API.Formulas.getProperties(formula).then(function (properties) {

                    // Loop through the received properties and assign them to self.blueprintProperties
                    for (var key in properties) {
                        propBuilder[key] = properties[key];
                    }
                    // self.blueprintProperties(propBuilder);
                    // self.blueprintPropertiesStringified(JSON.stringify(propBuilder, undefined, 3));
                });

                formulaPromises[formulaPromises.length] = promise;
            });

            // Get all formula components and add
            Q.all(formulaPromises).then(function () {

                host.properties = propBuilder;

                // Clear hosts from the store
                self.BlueprintHostStore.add(host);

                // Clear out the forumla select control
                $('#formula_components').selectpicker('deselectAll');

                // Set spot instance boolean to false in order to hide the input field for next time
                self.hostIsSpotInstance(false);

                // Clear volume and access rules stores
                self.HostRuleStore.empty();
                self.HostVolumeStore.empty();

                // Clear out the spot instance bid price field
                document.getElementById('spot_instance_price').value = "";

                self.viewBlueprint();
            }).done();

        };


        self.viewBlueprint = function () {
            if (self.selectedBlueprint() === null) {
                self.navigate({view: 'blueprint.detail'});
            } else {
                self.navigate({view: 'blueprint.detail', data: {blueprint: self.selectedBlueprint().id} });
            }

        };

    };

    vm.prototype = new base();
    return new vm();
});
