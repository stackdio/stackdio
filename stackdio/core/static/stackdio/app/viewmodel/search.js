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

define(['knockout', '../../bower_components/q/q', 'util/galaxy', 'bootstrap-typeahead'],
function (ko, Q, $galaxy) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'search';
        self.templatePath = 'omnibox.html';
        self.domBindingId = '.omnibox';
        self.autoRender = true;

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.search = function (model, evt) {

        };

        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            $('#omnibox_search').typeahead({
                name: 'search',
                valueKey: 'title',
                engine: _,
                minLength: 1,
                template: '<div class="search-result-<%= result_type %>"><%= result_type %> | <%= title %></div>',
                remote: '/api/search/?q=%QUERY',
                limit: 10
            }).on('typeahead:selected', function (object, selectedItem) {
                switch (selectedItem.result_type) {
                    case 'formula':
                        $galaxy.transport({
                            location: 'formula.detail',
                            payload: {
                                formula: selectedItem.id
                            }
                        });
                        break;
                    case 'blueprint':
                        $galaxy.transport({
                            location: 'blueprint.detail',
                            payload: {
                                blueprint: selectedItem.id
                            }
                        });
                        break;
                    case 'stack':
                        $galaxy.transport({
                            location: 'stack.detail',
                            payload: {
                                stack: selectedItem.id
                            }
                        });
                        break;
                }
            });
        });
    };
    return new vm();
});
