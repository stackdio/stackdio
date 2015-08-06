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

define(['../../bower_components/q/q', 'settings', 'model/models'], function (Q, settings, models) {
    return {
        loadByAccount : function (account) {
            var self = this;
            var deferred = Q.defer();
            var group;

            $.ajax({
                url: account.security_groups,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise
        },
        save : function (group) {
            var self = this;
            var deferred = Q.defer();
            var securityGroup = JSON.stringify(group);

            $.ajax({
                url: settings.api.cloud.security_groups,
                type: 'POST',
                data: securityGroup,
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise
        },
        updateRule : function (group, ruleData) {
            var deferred = Q.defer();
            var newRule = JSON.stringify(ruleData);
           
            $.ajax({
                url: group.rules_url,
                type: 'PUT',
                data: newRule,
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        updateDefault : function (group) {
            var self = this;
            var deferred = Q.defer();
            var securityGroup = JSON.stringify(group);

            $.ajax({
                url: group.url,
                type: 'PUT',
                data: securityGroup,
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                }
            });

            return deferred.promise
        },
        delete : function (group) {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/security_groups/' + group.id + '/',
                type: 'DELETE',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    // Remove the Security Group from the local array
                    stores.SecurityGroups.remove(function (g) {
                        return g.id === group.id;
                    });

                    // Resolve the promise
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    console.log(arguments);

                    deferred.reject(new Error(JSON.parse(request.responseText).detail));
                }
            });

            return deferred.promise
        }
    }
});
