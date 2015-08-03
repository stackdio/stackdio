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
    '../../bower_components/q/q',
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Stacks',
    'store/StackActions',
    'api/api'
],
function (Q, ko, $galaxy, formutils, StackStore, StackActionStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
       
        self.actionTitle = ko.observable();
        self.stackTitle = ko.observable();

        self.selectedStack = ko.observable(null);
        self.selectedAction = ko.observable(null);

        self.selectedOutput = ko.observableArray();

        self.StackStore = StackStore;
        self.StackActionStore = StackActionStore;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.action.detail';
        self.templatePath = 'stack.action.detail.html';
        self.domBindingId = '#stack-action-detail';

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

            if (data.hasOwnProperty('stack')) {
                API.Stacks.getStack(data.stack).then(function (stack) {
                    self.selectedStack(stack);
                    self.stackTitle(stack.title);

                    if (data.hasOwnProperty('action')) {
                        API.Stacks.getAction(data.action).then(function (action) {

                            if (action) {
                                self.actionTitle(action.host_target+" "+action.command);
                            } else {
                                self.actionTitle('UNKNOWN ACTION');
                            }

                            self.selectedAction(action);
                            self.selectedOutput(action.std_out);

                        });
                    } else {
                        self.actionTitle('UNKNOWN ACTION');
                    }

                });

            } else {
                self.stackTitle('UNKNOWN STACK');
            }

        };
    

        self.goToStack = function() {
            $galaxy.transport({
                location: 'stack.actions',
                payload: {
                    stack: self.selectedStack().id
                }
            });
        };

        self.goToStackList = function() {
            $galaxy.transport({
                location: 'stack.list'
            });
        };

        self.convertDate = function(dateStr) {
            if (dateStr === "")
                return "";

            d = new Date(dateStr);
            return d.toLocaleString();
        };

        self.getStatusType = function(status) {
            switch(status) {
                case 'waiting':
                    return 'info';
                case 'running':
                    return 'warning';
                case 'finished':
                    return 'success';
                default:
                    return 'default';
            }
        };

    };
    return new vm();
});
