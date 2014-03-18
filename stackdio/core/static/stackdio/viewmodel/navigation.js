define([
    'q', 
    'knockout',
    'util/galaxy',
    'viewmodel/search',
    'viewmodel/welcome'
],
function (Q, ko, $galaxy, search, welcome) {
    var vm = function () {
        var self = this;

        /*
            R E G I S T R A T I O N   S E C T I O N
        */
        self.id = 'navigation';
        self.templatePath = 'navigation.html';
        self.domBindingId = '#navigation';
        self.children = [search];
        self.autoRender = true;

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }

        self.sections = [
            {
                id:'Welcome',
                view: 'welcome',
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
                id:'Providers',
                view: 'account.list',
                icon: null,
                visible: false
            },
            {
                id:'Profiles',
                view: 'profile.list',
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
                view: 'snapshot.list',
                icon: 'glyphicon glyphicon-camera',
                visible: true
            }
        ];
        self.currentSection = ko.observable(self.sections[0]);

        self.changeView = function (section) {
            if (!section.hasOwnProperty('id')) {
                section = _.findWhere(self.sections, {view: section});
            }
            $galaxy.transport(section.view);
        };

        self.showUserProfile = function () {
            $galaxy.transport('user.profile');
        };

        self.showUserPassword = function () {
            $galaxy.transport('user.password');
        };

        self.showUserPassword = function () {
            $galaxy.transport('user.password');
        };

    };
    return new vm();
});
