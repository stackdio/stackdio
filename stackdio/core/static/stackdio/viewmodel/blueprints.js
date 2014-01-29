define(["knockout",
        "q", 
        "util/form",
        "util/postOffice",
        "viewmodel/abstract",
        "model/models",
        "store/stores",
        "api/api"], 
function (ko, Q, formutils, _O_, abstractVM, models, stores, API) {
    var vm = function () {
        var self = this;
        self.selectedProfile = null;
        self.selectedAccount = null;
        self.selectedBlueprint = null;
        self.selectedBlueprintHosts = ko.observable();
        self.blueprintProperties = ko.observable({});
        self.blueprintPropertiesStringified = ko.observable('');

        // Only show spot instance price box if the spot instance checkbox is checked
        self.hostIsSpotInstance = ko.observable(false);
        $('#spot_instance').click(function () {
            self.hostIsSpotInstance(this.checked);
        });


        // 
        //      O R C H E S T R A T I O N
        // 
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

        // 
        //      N E W   H O S T S
        // 
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

        self.updateBlueprint = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var blueprint = self.selectedBlueprint;
            console.log(blueprint);
            return;


            blueprint.title = record.stack_title_edit.value;
            blueprint.description = record.stack_description_edit.value;
            blueprint.namespace = record.stack_namespace_edit.value;
            
            if (record.stack_properties_preview_edit.value !== '') {
                blueprint.properties = JSON.parse(record.stack_properties_preview_edit.value);
            }

            console.log(blueprint);

            API.Stacks.update(blueprint)
                .then(function () {
                    self.closeStackForm();
                    _O_.publish('blueprint.updated');
                });

        };

        self.saveBlueprint = function (model, evt) {
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

        self.resetBlueprintForm = function () {
            // Clear the new Blueprint Host store
            stores.BlueprintHosts.removeAll();

            // Empty out the store that tracks components for current Blueprint
            stores.BlueprintComponents.removeAll();

            // Clear the orchestration form
            formutils.clearForm('orchestration-form');

            // Manually clear the blueprint form so I don't lose Knockout bindings
            $('#blueprint_title').val('');
            $('#blueprint_purpose').val('');

            // Clear the blueprint properties
            self.blueprintProperties({});
            self.blueprintPropertiesStringified('');
        };

        self.deleteBlueprint = function (blueprint) {
            API.Blueprints.delete(blueprint)
                .then(self.showSuccess)
                .catch(function (error) {
                    self.showError(error);
                });
        };

        self.loadBlueprint = function (blueprint) {
            return API.Blueprints.load(blueprint);
        };

        self.showBlueprintHostList = function (blueprint) {
            blueprint.host_definitions.forEach(function (host) {
                host.instance_size = _.find(stores.InstanceSizes(), function (size) {
                    return host.size === size.url;
                });

                host.rules = host.access_rules.forEach(function (rule) {
                    return rule.rule;
                });
            });
            self.selectedBlueprintHosts(blueprint.host_definitions);

            $("#blueprint-host-list-container").dialog("open");
        }

        self.closeBlueprintHostList = function () {
            $("#blueprint-host-list-container").dialog("close");
        }

        self.showBlueprintForm = function (blueprint) {
            /*
                If blueprint argument exists, and it is a blueprint, then the user 
                clicked on an existing blueprint, so set the model level blueprint
                to the argument, and load the properties from the API
            */
            if (blueprint instanceof models.Blueprint) {
                self.selectedBlueprint = blueprint;

                $('#blueprint_title').val(self.selectedBlueprint.title);
                $('#blueprint_purpose').val(self.selectedBlueprint.description);
                $('#public_blueprint').attr('checked', self.selectedBlueprint.public);

                self.selectedBlueprint.host_definitions.forEach(function (host) {

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

                API.Blueprints.getProperties(blueprint)
                    .then(function (properties) {
                        console.log(properties);
                        self.blueprintPropertiesStringified(JSON.stringify(properties, undefined, 3));
                    });
            }


            $("#blueprint-form-container").dialog("open");
        }

        self.closeBlueprintForm = function () {
            self.resetBlueprintForm();
            $("#blueprint-form-container").dialog("close");
        }

        self.closeEditForm = function () {
            $("#blueprint-edit-container").dialog("close");
        }

        self.showOrchestration = function () {
            $("#component-orchestration-container").dialog("open");
        }

        self.closeOrchestration = function () {
            $("#component-orchestration-container").dialog("close");
        }

        self.showHostForm = function (profile) {
            self.selectedProfile = profile;
            self.selectedAccount = profile.account;

            // Choose the default instance size assigned to the chosen profile
            $('#host_instance_size').selectpicker('val', profile.default_instance_size);

            // Choose the default zone assigned to the chosen account
            $('#availability_zone').selectpicker('val', self.selectedAccount.default_availability_zone);

            $( "#host-form-container" ).dialog("open");
        };

        self.closeHostForm = function () {
            formutils.clearForm('blueprint-host-form');
            $( "#host-form-container" ).dialog("close");
        };

        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#blueprint-form-container").dialog({
            autoOpen: false,
            width: window.innerWidth - 225,
            height: 800,
            position: ['center', 60],
            modal: false
        });

        $("#blueprint-edit-container").dialog({
            autoOpen: false,
            width: window.innerWidth - 225,
            height: 800,
            position: ['center', 60],
            modal: false
        });

        $("#blueprint-host-list-container").dialog({
            position: 'center',
            autoOpen: false,
            width: window.innerWidth - 200,
            modal: true
        });


        $("#host-form-container").dialog({
            position: [(window.innerWidth / 2) - 275, 60],
            autoOpen: false,
            width: 600,
            modal: true
        });

        $("#host-access-rule-container").dialog({
            autoOpen: false,
            width: 600,
            modal: true
        });

        $("#component-orchestration-container").dialog({
            autoOpen: false,
            width: 600,
            modal: true
        });
    };

    vm.prototype = new abstractVM();
    return vm;
});
