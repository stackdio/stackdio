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

define(['q', 'model/models'], function (Q, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/settings/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response.public_key);
                }
            });

            return deferred.promise;
        },
        saveKey: function (public_key) {
            var deferred = Q.defer();

            var data = JSON.stringify({'public_key': public_key});

            $.ajax({
                url: '/api/settings/',
                type: 'PUT',
                data: data,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        savePassword: function (oldpw, newpw, confirmpw) {
            var deferred = Q.defer();

            var data = JSON.stringify({
                'current_password': oldpw,
                'new_password': newpw,
                'confirm_password': confirmpw
            });

            $.ajax({
                url: '/api/settings/change_password/',
                type: 'PUT',
                data: data,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    var response;

                    try {
                        response = JSON.parse(request.responseText);
                        deferred.resolve(response.detail.errors[0]);
                    }
                    catch (e) {
                        deferred.resolve();
                    }
                }
            });

            return deferred.promise;
        }
    }
});
