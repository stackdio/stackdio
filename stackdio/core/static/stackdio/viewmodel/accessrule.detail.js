define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Blueprints',
    'store/HostAccessRules',
    'store/BlueprintHosts',
    'api/api',
    'model/models'
],
function (Q, ko, $galaxy, formutils, BlueprintStore, HostRuleStore, BlueprintHostStore, API, models) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedBlueprint = ko.observable();
        self.blueprintTitle = ko.observable();
        self.selectedHost = ko.observable();
        self.hostTitle = ko.observable();
        self.$galaxy = $galaxy;

        self.BlueprintStore = BlueprintStore;
        self.HostRuleStore = HostRuleStore;
        self.BlueprintHostStore = BlueprintHostStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'accessrule.detail';
        self.templatePath = 'accessrule.html';
        self.domBindingId = '#accessrule-detail';

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
            self.init(data);
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var blueprint = null;
            var host = null;


            if (data.hasOwnProperty('blueprint')) {
                blueprint = BlueprintStore.collection().filter(function (p) {
                    return p.id === parseInt(data.blueprint, 10)
                })[0];

                self.blueprintTitle(blueprint.title);
            } else {
                self.blueprintTitle('New Blueprint');
            }
            self.selectedBlueprint(blueprint);


            if (data.hasOwnProperty('host')) {
                host = BlueprintHostStore.collection().filter(function (h) {
                    return h.id === parseInt(data.host, 10)
                })[0];

                self.hostTitle(host.title);
            } else {
                self.hostTitle('New Host');
            }
            self.selectedHost(host);

        };

        self.addRule = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var rule;

            if (record.rule_ip_address.value !== '') {
                rule = record.rule_ip_address.value;
            } else if (record.rule_group.value !== '') {
                rule = record.rule_group.value;
            }

            var accessRule = {
                protocol: record.rule_protocol.value,
                from_port: record.rule_from_port.value,
                to_port: record.rule_to_port.value,
                rule: rule
            };

            HostRuleStore.add(new models.BlueprintHostAccessRule().create(accessRule));

            $('#rule_from_port').val('');
            $('#rule_to_port').val('');
            $('#rule_ip_address').val('');
            $('#rule_group').val('');
            $('#rule_protocol').attr('selectedIndex', '-1').find("option:selected").removeAttr("selected");

            $galaxy.transport('host.detail');
        };

        self.cancelChanges = function (model, evt) {
            $galaxy.transport('host.detail');
        };
    };
    return new vm();
});
