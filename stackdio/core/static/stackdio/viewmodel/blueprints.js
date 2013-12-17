define(["knockout",
        "q", 
        "util/form",
        "viewmodel/abstract",
        "model/models",
        "store/stores",
        "api/api"], 
    function (ko, Q, formutils, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;
            self.selectedProfile = null;
            self.selectedAccount = null;
            self.selectedBlueprintHosts = ko.observable();
            self.blueprintProperties = ko.observable();


            // 
            //      N E W   H O S T S
            // 
            self.addHost = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                var v, vol;

                // Create a new host definition
                var host = new models.NewHost().create({ 
                    id: '',
                    title: 'title',
                    description: 'description',
                    count: record.host_count.value,
                    size: record.host_instance_size.value,
                    hostname_template: record.host_hostname.value,
                    zone: record.availability_zone.value,
                    cloud_profile: self.selectedProfile.id,
                    access_rules: stores.HostAccessRules(),
                    volumes: stores.HostVolumes(),
                    formula_components: record.formula_components.map(function (g) { return { id: g.value.split('|')[1], order: 0 }; })
                });

                console.log('record',record);
                console.log('stores.Formulae()',stores.Formulae());

                // Get the properties for each formula component the user chose
                record.formula_components.forEach(function (component) {
                    var formulaId = parseInt(component.value.split('|')[0], 10);

                    var formula = _.find(stores.Formulae(), function (formula) {
                        return formula.id === formulaId;
                    });
                    console.log('formula',formula);

                    API.Formulae.getProperties(formula)
                        .then(function (properties) {
                            console.log('properties',properties);
                            
                            // self.blueprintProperties
                        })
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
                    host.spot_config.spot_price = record.spot_instance_price.value;
                }

                stores.NewHosts.push(host);

                // Clear volume and access rules stores
                stores.HostAccessRules.removeAll();
                stores.HostVolumes.removeAll();

                self.closeHostForm();

                // Clear out the spot instance bid price field
                document.getElementById('spot_instance_price').value = "";
            };

            self.removeHost = function (host) {
                stores.NewHosts.remove(host);
            };

            self.saveBlueprint = function (model, evt) {
                // var blueprint = formutils.collectFormFields(evt.target.form);
                var hosts = stores.NewHosts();

                var blueprint = {
                    title: document.getElementById('blueprint_title').value,
                    description: document.getElementById('blueprint_purpose').value,
                    public: document.getElementById('public_blueprint').checked,
                    properties: {},     // TODO
                    hosts: hosts
                };

                console.log(blueprint);
                // return;

                API.Blueprints.save(blueprint)
                    .then(function (blueprint) {
                        // Close the form and clear it out
                        self.closeBlueprintForm();
                        self.showMessage('#alert-success', 'Blueprint successfully saved.');
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.deleteBlueprint = function (blueprint) {
                API.Blueprints.delete(blueprint)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error);
                    });
            };

            self.loadBlueprint = function () {
                return API.Accounts.load();
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


            self.showBlueprintForm = function () {
                $("#blueprint-form-container").dialog("open");
            }

            self.closeBlueprintForm = function () {
                formutils.clearForm('blueprint-form');
                $("#blueprint-form-container").dialog("close");
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
                height: 500,
                position: ['center', 60],
                modal: false
            });

            $("#blueprint-host-list-container").dialog({
                position: 'center',
                autoOpen: false,
                width: 800,
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
                width: 500,
                modal: true
            });
        };

        vm.prototype = new abstractVM();

        return vm;
});