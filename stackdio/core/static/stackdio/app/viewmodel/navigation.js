/*!
  * Copyright 2014,  Digital Reasoning
  * 
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  * 
  *     http://www.apache.org/licenses/LICENSE-2.0
  * 
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  * 
*/

define([
    'q',
    'settings',
    'knockout',
    'util/galaxy',
    'viewmodel/search',
    'viewmodel/welcome'
],
function (Q, settings, ko, $galaxy, search, welcome) {
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

        self.sections = ko.observableArray([
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
        ]);
        self.currentSection = ko.observable(self.sections()[0]);


        if (settings.superuser) {
            self.sections.push({
                id:'Admin',
                view: 'admin',
                icon: 'glyphicon glyphicon-list-alt',
                visible: true
            });
        }


        self.changeView = function (section) {
            if (!section.hasOwnProperty('id')) {
                section = _.findWhere(self.sections(), {view: section});
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
