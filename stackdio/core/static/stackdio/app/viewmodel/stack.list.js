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

define(['../../bower_components/q/q', 'knockout', 'bootbox', 'util/galaxy', 'util/alerts', 'util/stack', 'ladda', 'store/Blueprints', 'store/Stacks', 'api/api'],
function (Q, ko, bootbox, $galaxy, alerts, stackutils, Ladda, BlueprintStore, StackStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch', 'Delete', 'Provision'];
        self.stackHostActions = ['Stop', 'Terminate', 'Start'];
        self.selectedProfile = null;
        self.selectedAccount = null;
        self.selectedBlueprint = ko.observable({title:''});
        self.blueprintProperties = ko.observable();
        self.selectedStack = ko.observable();
        self.BlueprintStore = BlueprintStore;
        self.StackStore = StackStore;
        self.$galaxy = $galaxy;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.list';
        self.templatePath = 'stacks.html';
        self.domBindingId = '#stack-list';

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
            StackStore.populate(true).catch(function (err) {
                console.error(err);
            });
            BlueprintStore.populate().then(function () {
                $('span').popover('hide');
            }).catch(function (err) {
                console.error(err);
            }).done();
        });

        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
        */

        self.popoverBuilder = stackutils.popoverBuilder;

        self.doStackAction = stackutils.doStackAction;

        self.showStackDetails = stackutils.showStackDetails;

        self.createNewStack = function (blueprint) {
            API.Users.load().then(function (public_key) {
                if (public_key === '') {
                    alerts.showMessage('#error', 'You have not saved your public key, and cannot launch any new stacks. Please open your user profile to save one.', true, 4000);
                } else {
                    $galaxy.transport({
                        location: 'stack.detail',
                        payload: {
                            blueprint: blueprint.id
                        }
                    });
                }
            });
        };

        self.getStatusType = stackutils.getStatusType;

        self.refresh = function(obj, evt) {
            evt.preventDefault();
            var l = Ladda.create(evt.currentTarget);
            l.start();
            StackStore.populate(true).then(function() {
                l.stop();
            }).catch(function (err) {
                console.error(err);
                alerts.showMessage('#error', err, true, 4000);
                l.stop();
            }).done();
        };

    };
    return new vm();
});
