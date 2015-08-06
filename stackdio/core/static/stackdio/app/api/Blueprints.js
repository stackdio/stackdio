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
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.blueprints.blueprints,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var blueprints = response.results.map(function (blueprint) {
                        return new models.Blueprint().create(blueprint);
                    });
                    deferred.resolve(blueprints);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        getBlueprint: function (blueprintId) {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.blueprints.blueprints+blueprintId.toString()+'/',
                type: 'GET',
                dataType: 'json',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (blueprint) {
                    deferred.resolve(blueprint);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        getBlueprintFromUrl: function (blueprintUrl) {
            var deferred = Q.defer();

            $.ajax({
                url: blueprintUrl,
                type: 'GET',
                dataType: 'json',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (blueprint) {
                    deferred.resolve(blueprint);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;

        },
        getProperties: function (blueprint) {
            var deferred = Q.defer();

            $.ajax({
                url: blueprint.properties,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (properties) {
                    deferred.resolve(properties); 
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        save: function (blueprint) {
            var deferred = Q.defer();
            var blueprint = JSON.stringify(blueprint);

            $.ajax({
                url: settings.api.blueprints.blueprints,
                type: 'POST',
                data: blueprint,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(new models.Blueprint().create(response));
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        update: function (blueprint) {
            var deferred = Q.defer();

            $.ajax({
                url: blueprint.url,
                type: 'PUT',
                data: JSON.stringify(blueprint),
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
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

            return deferred.promise;
        },
        delete: function (blueprint) {
            var deferred = Q.defer();

            $.ajax({
                url: blueprint.url,
                type: 'DELETE',
                dataType: 'json',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': stackdio.settings.csrftoken,
                    'Accept': 'application/json'
                },
                success: function (response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    deferred.reject(JSON.parse(request.responseText).detail);
                }
            });

            return deferred.promise;
        }
    }
});
