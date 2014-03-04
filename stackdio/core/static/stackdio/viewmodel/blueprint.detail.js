define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/HostVolumes',
    'store/HostAccessRules',
    'store/Accounts',
    'store/Profiles',
    'store/InstanceSizes',
    'store/Blueprints',
    'store/BlueprintHosts',
    'store/BlueprintComponents',
    'store/Formulas',
    'api/api'
],
function (Q, ko, base, _O_, formutils, HostVolumeStore, HostRuleStore, AccountStore, ProfileStore, InstanceSizeStore, BlueprintStore, BlueprintHostStore, BlueprintComponentStore, FormulaStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedProfile = null;
        self.selectedAccount = null;
        self.selectedBlueprint = ko.observable(null);
        self.blueprintTitle = ko.observable();
        self.selectedBlueprintHosts = ko.observable();
        self.blueprintProperties = ko.observable();
        self.blueprintPropertiesStringified = ko.observable('');
        self.editMode = 'create';

        self.HostVolumeStore = HostVolumeStore;
        self.HostRuleStore = HostRuleStore;
        self.AccountStore = AccountStore;
        self.ProfileStore = ProfileStore;
        self.InstanceSizeStore = InstanceSizeStore;
        self.BlueprintStore = BlueprintStore;
        self.BlueprintHostStore = BlueprintHostStore;
        self.BlueprintComponentStore = BlueprintComponentStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'blueprint.detail';
        self.templatePath = 'blueprint.html';
        self.domBindingId = '#blueprint-detail';

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
        _O_.subscribe('blueprint.detail.rendered', function (data) {
            AccountStore.populate().then(function () {
                return ProfileStore.populate();
            }).then(function () {
                return InstanceSizeStore.populate();
            }).then(function () {
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

            HostVolumeStore.empty();
            HostRuleStore.empty();

            // Editing existing blueprint
            if (data.hasOwnProperty('blueprint')) {
                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10);
                })[0];

            // New blueprint, so clear form fields and reset observable values
            } else {
                self.blueprintPropertiesStringified('');
                self.blueprintProperties({});
                self.blueprintTitle('New Blueprint');
            }

            self.selectedBlueprint(blueprint);

            if (blueprint && blueprint.hasOwnProperty('id')) {
                // Editing existing blueprint so populate form
                $('#blueprint_title').val(blueprint.title);
                $('#blueprint_purpose').val(blueprint.description);
                $('#public_blueprint').prop('checked', blueprint.public);

                self.blueprintTitle(blueprint.title);
                self.editMode = 'update';

                if (BlueprintHostStore.collection().length === 0) {
                    blueprint.host_definitions.forEach(function (host) {
                        // Add the instance size object to the host so the title can be displayed in UI
                        host.instance_size = _.find(InstanceSizeStore.collection(), function (i) {
                            return i.url === host.size;
                        });

                        // Add some HTML to display for the chosen roles
                        host.flat_components = _.map(host.formula_components, function (fc) { 
                            return '<div style="line-height:15px !important;">' + fc.description + '</div>'; 
                        }).join('');

                        // Add some HTML to display for the chosen security groups
                        host.flat_access_rules = host.access_rules.length + ' access rules';

                        self.BlueprintHostStore.add(host);
                    });
                }

                // Get the properties for the blueprint and then stringify the object for display in the form
                if (self.blueprintPropertiesStringified() === '') {
                    API.Blueprints.getProperties(blueprint).then(function (properties) {
                        self.blueprintProperties(properties);

                        var stringify = JSON.stringify(properties, undefined, 3);
                        self.blueprintPropertiesStringified(stringify);
                    });
                }
            }


            if (BlueprintHostStore.collection().length > 0) {
                var propBuilder = self.blueprintProperties();

                // Get the properties for each formula component in the list of hosts defined by user
                BlueprintHostStore.collection().forEach(function (host) {
                    for (var key in host.properties) {
                        propBuilder[key] = host.properties[key];
                    }
                    self.blueprintProperties(propBuilder);
                    self.blueprintPropertiesStringified(JSON.stringify(propBuilder, undefined, 3));
                });
            }
        };

        self.saveBlueprint = function (model, evt) {
            if (self.editMode === 'create') {
                self.createBlueprint(model, evt);
            } else {
                self.updateBlueprint(model, evt);
            }
        };

        self.cancelChanges = function (model, evt) {
            self.clearEditingData();
            self.navigate({ view: 'blueprint.list' });
        };

        /*
         * This function will empty out any cached collections or observables when
         * the user is done editing the blueprint (save/cancel)
         */
        self.clearEditingData = function () {
            self.BlueprintHostStore.empty();
            self.BlueprintComponentStore.empty();
            self.HostVolumeStore.empty();
            self.HostRuleStore.empty();

            self.blueprintPropertiesStringified('');
            self.selectedBlueprint(null);

            $('#public_blueprint').prop('checked', false);
        };

        self.createBlueprint = function (model, evt) {
           var hosts = BlueprintHostStore.collection(), strippedHosts = [], properties;

            for (var host in hosts) {
                var h = hosts[host];

                strippedHosts.push({
                    access_rules: h.access_rules,
                    cloud_profile: h.cloud_profile,
                    count: h.count,
                    description: h.description,
                    title: h.title,
                    formula_components: h.formula_components,
                    hostname_template: h.hostname_template,
                    size: h.size,
                    spot_config: h.spot_config,
                    volumes: h.volumes,
                    zone: h.zone,
                });
            }

            properties = JSON.parse(document.getElementById('blueprint_properties').value) || '';

            var blueprint = {
                title: document.getElementById('blueprint_title').value,
                description: document.getElementById('blueprint_purpose').value,
                public: document.getElementById('public_blueprint').checked,
                properties: properties,
                hosts: strippedHosts
            };

            API.Blueprints.save(blueprint).then(function (newBlueprint) {
                BlueprintStore.add(newBlueprint);
                self.clearEditingData();
                self.navigate({ view: 'blueprint.list' });
            })
            .catch(function (error) {
                $("#alert-error").show();
            });
        };

        self.updateBlueprint = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var blueprint = {};
            var currentBlueprint = self.selectedBlueprint();
            var hosts = BlueprintHostStore.collection(), strippedHosts = [];


            for (var host in hosts) {
                var h = hosts[host];

                strippedHosts.push({
                    access_rules: h.access_rules,
                    cloud_profile: h.cloud_profile,
                    count: h.count,
                    description: h.description,
                    title: h.title,
                    formula_components: h.formula_components,
                    hostname_template: h.hostname_template,
                    size: h.size,
                    spot_config: h.spot_config,
                    volumes: h.volumes,
                    zone: h.zone,
                });
            }


            // Clone the self.selectedBlueprint() item so we don't modify the item in the store
            for (var key in self.selectedBlueprint()) {
                if (typeof currentBlueprint[key] !== 'function') {
                    blueprint[key] = currentBlueprint[key];
                }
            }

            // Update property values with those submitted from form
            blueprint.title = record.blueprint_title.value;
            blueprint.description = record.blueprint_purpose.value;
            blueprint.public = $('#public_blueprint').prop('checked');
            blueprint.properties = JSON.parse(record.blueprint_properties.value);
            blueprint.hosts = strippedHosts;
            delete blueprint.host_definitions;

            API.Blueprints.update(blueprint).then(function (updatedBlueprint) {
                self.selectedBlueprint(null);               // Clear out selected blueprint
                BlueprintStore.removeById(blueprint.id);    // Remove old blueprint from store
                BlueprintStore.add(updatedBlueprint);       // Add new one to store

                self.clearEditingData();
                self.navigate({ view: 'blueprint.list' });  // Go to the blueprint list
            })
            .catch(function (error) {
                console.log(error);
            }).done();
        };

        self.saveOrchestration = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var orderedComponents = [];

            for (var c in record) {
                var component = {}
                component.formObject = record[c];
                component.id = parseInt(c.split('_')[2], 10);
                component.order = parseInt(component.formObject.value, 10);

                orderedComponents.push(component);
                // component.sourceObject = _.findWhere(stores.BlueprintComponents(), { id: component.id });
            }

            stores.BlueprintHosts().forEach(function (host) {
                host.formula_components.forEach(function (formulaComponent) {
                    orderedComponents.forEach(function (orderedComponent) {
                        if (orderedComponent.id === parseInt(formulaComponent.id, 10)) {
                            formulaComponent.order = orderedComponent.order;
                        }
                    });
                })
            });

            self.closeOrchestration();
        };

        self.addHost = function (profile) {
            if (self.selectedBlueprint() === null) {
                self.navigate({view: 'host.detail', data: { profile: profile.id } });
            } else {
                self.navigate({view: 'host.detail', data: { blueprint: self.selectedBlueprint().id, profile: profile.id } });
            }
        };

        self.removeHost = function (host) {
            BlueprintHostStore.remove(host);
        };

    };

    vm.prototype = new base();
    return new vm();
});
