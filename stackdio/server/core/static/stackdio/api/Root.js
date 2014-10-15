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

define(['q', 'settings'], function (Q, settings) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api',
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    settings.api = response;
                    deferred.resolve(response);
                }
            });

            return deferred.promise;
        },
        save: function (record) {

        },
        delete: function (record) {

        }
    }
});