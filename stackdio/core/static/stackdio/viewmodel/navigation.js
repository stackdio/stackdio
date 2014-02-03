define([
    'q', 
    'knockout',
    'viewmodel/base',
    'util/postOffice',
    'util/66'
],
function (Q, ko, base, _O_, $66) {
    var vm = function () {
        var self = this;

        /*
            R E G I S T R A T I O N   S E C T I O N
        */
        self.id = 'navigation';
        self.templatePath = 'navigation.html';
        self.domBindingId = '#navigation';
        self.autoRender = true;

        try {
            self.sixtysix.register(self);
        } catch (ex) {
            console.log(ex);            
        }

        self.sections = [
            {
                id:'Welcome',
                view: 'welcome.main',
                icon: null,
                visible: false
            },
            {
                id:'Blueprints',
                view: 'blueprint.list',
                icon: 'glyphicon glyphicon-tower',
                visible: true
            },
            {
                id:'Stacks',
                view: 'stack.list',
                icon: 'glyphicon glyphicon-th-list',
                visible: true
            },
            {
                id:'Accounts',
                view: 'accounts.main',
                icon: null,
                visible: false
            },
            {
                id:'Profiles',
                view: 'profiles.main',
                icon: null,
                visible: false
            },
            {
                id:'Formulas',
                view: 'formula.list',
                icon: 'glyphicon glyphicon-tint',
                visible: true
            },
            {
                id:'Snapshots',
                view: 'snapshots.main',
                icon: 'glyphicon glyphicon-camera',
                visible: true
            }
        ];
        self.currentSection = ko.observable(self.sections[0]);

        self.navigate = function (section) {
            if (!section.hasOwnProperty('id')) {
                section = _.findWhere(self.sections, {view: section});
            }
            // _O_.publish('navigate', { view: section.view });
            $66.navigate({ view: section.view });
        };

    };

    vm.prototype = new base();
    return new vm();
});
