define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Accounts',
    'store/Profiles',
    'store/Formulas',
    'store/InstanceSizes',
    'store/Blueprints',
    'store/Zones',
    'store/Snapshots',
    'store/HostAccessRules',
    'store/HostVolumes',
    'store/BlueprintHosts',
    'store/FormulaComponents',
    'store/BlueprintComponents',
    'api/api',
    'model/models'
],
function (Q, ko, $galaxy, formutils, AccountStore, ProfileStore, FormulaStore, InstanceSizeStore, BlueprintStore, ZoneStore, SnapshotStore,
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
        self.blueprintTitle = ko.observable();
        self.blueprintProperties = ko.observable();
        self.blueprintPropertiesStringified = ko.observable();
        self.hostIsSpotInstance = ko.observable(false);
        self.$galaxy = $galaxy;

        self.ProfileStore = ProfileStore;
        self.FormulaStore = FormulaStore;
        self.InstanceSizeStore = InstanceSizeStore;
        self.BlueprintStore = BlueprintStore;
        self.ZoneStore = ZoneStore;
        self.SnapshotStore = SnapshotStore;
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
            FormulaStore.populate().then(function (formulas) {
                FormulaStore.collection().forEach(function (formula) {
                    for (var c in formula.components) {
                        FormulaComponentStore.add(new models.FormulaComponent().create(formula.components[c]));
                    }
                });
            });

            SnapshotStore.populate();

            // Load accounts, profiles, blueprints, instance sizes and availability zones
            AccountStore.populate().then(function () {
                return ProfileStore.populate();    
            }).then(function () {
                return BlueprintStore.populate();    
            }).then(function () {
                return InstanceSizeStore.populate();
            }).then(function () {
                return ZoneStore.populate(); 
            }).then(function () {
                self.init(data);
            });
        });

        $galaxy.network.subscribe('newhost', function () {
            formutils.clearForm('blueprint-host-form');
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
                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10);
                })[0];

                self.selectedBlueprint(blueprint);
                self.blueprintTitle(blueprint.title);
            } else {
                self.blueprintTitle('New Blueprint');
            }

            if (data.hasOwnProperty('profile')) {
                profile = ProfileStore.collection().filter(function (p) {
                    return p.id === parseInt(data.profile, 10);
                })[0];

                self.selectedProfile = profile;
                $('#host_instance_size').val(profile.default_instance_size);
                
                var profileAccount = AccountStore.collection().filter(function (account) {
                    return account.id === profile.cloud_provider;
                })[0];
                $('#availability_zone').val(profileAccount.default_availability_zone);

            }

            // Only show spot instance price box if the spot instance checkbox is checked
            $('#spot_instance').click(function () {
                self.hostIsSpotInstance(this.checked);
            });
        };


        self.resetFormFields = function () {
            $("#formula_components").attr('selectedIndex', '-1').find("option:selected").removeAttr("selected");
            $('#spot_instance_price').val('');

            // Set spot instance boolean to false in order to hide the input field for next time
            self.hostIsSpotInstance(false);
        };

        self.cancelHostCreation = function () {
            formutils.clearForm('blueprint-host-form');
            self.resetFormFields();

            if (self.selectedBlueprint() === null) {
                $galaxy.transport('blueprint.detail');
            } else {
                $galaxy.transport({
                    location: 'blueprint.detail',
                    payload: {
                        blueprint: self.selectedBlueprint().id
                    }
                });
            }
        };

        self.createHost = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var v, vol;

            // Create a new host definition
            var host = new models.BlueprintHost().create({ 
                id: '',
                formulas: [],
                title: record.host_title.value,
                description: record.host_description.value,
                count: parseInt(record.host_count.value, 10),
                size: parseInt(record.host_instance_size.value, 10),
                hostname_template: record.host_hostname.value,
                zone: parseInt(record.availability_zone.value, 10),
                cloud_profile: self.selectedProfile.id,
                access_rules: HostRuleStore.collection().map(function (host) { return host; }),
                volumes: HostVolumeStore.collection().map(function (volume) { return volume; }),
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

                // Provide a default component orchestration order of 0
                component.order = 0;

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

            // Add some HTML to display for the added volumes
            host.flat_volumes = host.volumes.map(function (volume) { 
                var snapshot = SnapshotStore.collection().filter(function (snapshot) {
                    return snapshot.id === parseInt(volume.snapshot, 10);
                })[0];
                return '<div style="line-height:15px !important;">Snapshot '+ snapshot.title + ' (' + volume.device + ') mounted to '+volume.mount_point+'</div>'; 
            }).join('');

            // Add some HTML to display for the chosen security groups
            host.flat_access_rules = HostRuleStore.collection().map(function (rule) {
                return '<div style="line-height:15px !important;">Port(s) '+rule.from_port+'-'+rule.to_port+' allow '+rule.rule+'</div>'; 
            }).join('');

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
                });

                formulaPromises[formulaPromises.length] = promise;
            });

            // Get all formula components and add
            Q.all(formulaPromises).then(function () {

                host.properties = propBuilder;

                // Clear hosts from the store
                self.BlueprintHostStore.add(host);

                // Clear out the forumla select control
                // $('#formula_components').selectpicker('deselectAll');

                self.resetFormFields();

                // Clear volume and access rules stores
                self.HostRuleStore.empty();
                self.HostVolumeStore.empty();

                self.viewBlueprint();
            }).done();

        };

        self.viewBlueprint = function () {
            if (self.selectedBlueprint() === null) {
                $galaxy.transport('blueprint.detail');
            } else {
                $galaxy.transport({
                    location: 'blueprint.detail',
                    payload: {
                        blueprint: self.selectedBlueprint().id
                    }
                });
            }
        };

        self.addAccessRule = function () {
            if (self.selectedBlueprint() === null) {
                $galaxy.transport('accessrule.detail');
            } else {
                $galaxy.transport({
                    location: 'accessrule.detail',
                    payload: {
                        blueprint: self.selectedBlueprint().id
                    }
                });
            }
        };

        self.addVolume = function () {
            if (self.selectedBlueprint() === null) {
                $galaxy.transport('volume.detail');
            } else {
                $galaxy.transport({
                    location: 'volume.detail',
                    payload: {
                        blueprint: self.selectedBlueprint().id
                    }
                });
            }
        };

    };
    return new vm();
});
