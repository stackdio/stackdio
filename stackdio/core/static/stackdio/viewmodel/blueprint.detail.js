define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/form',
    'store/stores',
    'model/models',
    'api/api'
],
function (Q, ko, base, _O_, formutils, stores, models, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stores = stores;
        self.selectedProfile = null;
        self.selectedAccount = null;
        self.selectedBlueprint = null;
        self.selectedBlueprintHosts = ko.observable();
        self.blueprintProperties = ko.observable({});
        self.blueprintPropertiesStringified = ko.observable('');
        self.saveAction = self.createBlueprint;

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
            var promisesToRun = [];

            if (stores.Accounts().length === 0) {
                promisesToRun[promisesToRun.length] = API.Accounts.load;
            }

            if (stores.Profiles().length === 0) {
                promisesToRun[promisesToRun.length] = API.Profiles.load;
            }

            if (stores.InstanceSizes().length === 0) {
                promisesToRun[promisesToRun.length] = API.InstanceSizes.load;
            }

            if (stores.Blueprints().length === 0) {
                promisesToRun[promisesToRun.length] = API.Blueprints.load;
            }

            promisesToRun.reduce(function (loadData, next) {
                return loadData.then(next);
            }, Q([])).then(function () {
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

            if (data.hasOwnProperty('blueprint')) {
                blueprint = stores.Blueprints().map(function (p) {
                    if (p.id === parseInt(data.blueprint, 10)) {
                        return p;
                    }
                }).reduce(function (p, c) {
                    if (c.hasOwnProperty('id')) {
                        return c;
                    }
                });
            }

            self.selectedBlueprint = blueprint;

            if (blueprint && blueprint.hasOwnProperty('id')) {
                $('#blueprint_title').val(blueprint.title);
                $('#blueprint_purpose').val(blueprint.description);
                $('#public_blueprint').val(blueprint.public);

                self.saveAction = self.updateAccount;

                stores.BlueprintHosts.removeAll();

                blueprint.host_definitions.forEach(function (host) {

                    // Add the instance size object to the host so the title can be displayed in UI
                    host.instance_size = _.find(stores.InstanceSizes(), function (i) {
                        return i.url === host.size;
                    });

                    // Add some HTML to display for the chosen roles
                    host.flat_components = _.map(host.formula_components, function (fc) { 
                        return '<div style="line-height:15px !important;">' + fc.description + '</div>'; 
                    }).join('');

                    // Add some HTML to display for the chosen security groups
                    host.flat_access_rules = host.access_rules.length + ' access rules';

                    stores.BlueprintHosts.push(host);
                });

                API.Blueprints.getProperties(blueprint).then(function (properties) {
                    // console.log(properties);
                    self.blueprintPropertiesStringified(JSON.stringify(properties, undefined, 3));
                });

            }
        };

        self.saveBlueprint = function (model, evt) {
            self.saveAction(model, evt);
        };

        self.createBlueprint = function (model, evt) {
           var hosts = stores.BlueprintHosts(), strippedHosts = [], properties;

            if (self.selectedBlueprint === null) {
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

                API.Blueprints.save(blueprint)
                    .then(function () {
                        self.closeBlueprintForm();

                        // Alert the user about success
                        self.showMessage('#alert-success', 'Blueprint successfully saved.');

                        _O_.publish('blueprint.updated');
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    });
            } else {
                self.selectedBlueprint.title = document.getElementById('blueprint_title').value;
                self.selectedBlueprint.description = document.getElementById('blueprint_purpose').value;
                self.selectedBlueprint.public = document.getElementById('public_blueprint').checked;
                self.selectedBlueprint.properties = JSON.parse(document.getElementById('blueprint_properties').value) || '';

                console.log(self.selectedBlueprint);
                return;

                API.Blueprints.update(self.selectedBlueprint)
                    .then(function () {
                        self.selectedBlueprint = null;
                        self.closeBlueprintForm();
                        self.showMessage('#alert-success', 'Blueprint successfully saved.');
                        _O_.publish('blueprint.updated');
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    });
            }
        };

        self.updateBlueprint = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var account = {};

            // Clone the self.selectedAccount item so we don't modify the item in the store
            for (var key in self.selectedAccount) {
                account[key] = self.selectedAccount[key];
            }

            // Update property values with those submitted from form
            account.provider_type = record.account_provider.value;
            account.title = record.account_title.value;
            account.description = record.account_description.value;
            account.default_availability_zone = record.default_availability_zone.value;

            delete account.yaml;

            // PATCH the update, and on success, replace the current item in the store with new one
            API.Accounts.update(account).then(function () {
                stores.Accounts(_.reject(stores.Accounts(), function (acct) {
                    return acct.id === self.selectedAccount.id;
                }));
                stores.Accounts.push(account);
                self.navigate({ view: 'account.list' });
            });
        };

        self.deleteBlueprint = function (account) {
            API.Blueprints.delete(account).catch(function (error) {
                self.showError(error);
            });
        };

        // Only show spot instance price box if the spot instance checkbox is checked
        self.hostIsSpotInstance = ko.observable(false);
        $('#spot_instance').click(function () {
            self.hostIsSpotInstance(this.checked);
        });

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

        self.addHost = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var v, vol;

            // Create a new host definition
            var host = new models.BlueprintHost().create({ 
                id: '',
                formulas: [],
                formulaComponents: [],
                title: 'title',
                description: 'description',
                count: parseInt(record.host_count.value, 10),
                size: parseInt(record.host_instance_size.value, 10),
                hostname_template: record.host_hostname.value,
                zone: parseInt(record.availability_zone.value, 10),
                cloud_profile: self.selectedProfile.id,
                access_rules: _.map(stores.HostAccessRules(), function (rule) { return rule; }),
                volumes: stores.HostVolumes(),
                formula_components: record.formula_components.map(function (g) { return { id: g.value.split('|')[1], order: 0 }; })
            });


            // Get the properties for each formula component the user chose
            record.formula_components.forEach(function (component) {
                var formulaId = parseInt(component.value.split('|')[0], 10);
                var componentId = parseInt(component.value.split('|')[1], 10);
                var propBuilder = self.blueprintProperties();

                // Find the formula matching the id chosen in the component field
                var formula = _.find(stores.Formulae(), function (formula) {
                    return formula.id === formulaId;
                });

                // Find the formula matching the id chosen in the component field
                var component = _.find(stores.FormulaComponents(), function (comp) {
                    return comp.id === componentId;
                });

                if (typeof _.findWhere(stores.BlueprintComponents(), { id: component.id }) === "undefined") {
                    stores.BlueprintComponents.push(component);
                }
                host.formulas.push(formula);

                // Request the forumula properties
                API.Formulae.getProperties(formula)
                    .then(function (properties) {
                        // Loop through the received properties and assign them to self.blueprintProperties
                        for (var key in properties) {
                            propBuilder[key] = properties[key];
                        }

                        self.blueprintProperties(propBuilder);
                        self.blueprintPropertiesStringified(JSON.stringify(propBuilder, undefined, 3));
                    });
            });


            // Add the instance size object to the host so the title can be displayed in UI
            host.instance_size = _.find(stores.InstanceSizes(), function (i) {
                return i.id === parseInt(record.host_instance_size.value, 10);
            });

            // Add some HTML to display for the chosen roles
            host.flat_components = _.map(record.formula_components, function (fc) { 
                return '<div style="line-height:15px !important;">' + fc.text + '</div>'; 
            }).join('');

            // Add some HTML to display for the chosen security groups
            host.flat_access_rules = stores.HostAccessRules().length + ' access rules';

            // Add spot instance config
            if (record.spot_instance_price.value !== '') {
                host.spot_config = {};
                host.spot_config.spot_price = parseFloat(record.spot_instance_price.value);
            }

            // Clear hosts from the store
            stores.BlueprintHosts.push(host);

            // Clear out the forumla select control
            $('#formula_components').selectpicker('deselectAll');

            // Set spot instance boolean to false in order to hide the input field for next time
            self.hostIsSpotInstance(false);


            // Clear volume and access rules stores
            stores.HostAccessRules.removeAll();
            stores.HostVolumes.removeAll();

            self.closeHostForm();

            // Clear out the spot instance bid price field
            document.getElementById('spot_instance_price').value = "";
        };

        self.removeHost = function (host) {
            stores.BlueprintHosts.remove(host);
        };

    };

    vm.prototype = new base();
    return new vm();
});
