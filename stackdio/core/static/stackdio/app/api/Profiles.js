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
                url: settings.api.cloud.profiles,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var profiles = response.results.map(function (profile) {
                        return new models.Profile().create(profile);
                    });
                    deferred.resolve(profiles);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        update: function (profile) {
            var deferred = Q.defer();
            var _profile = {
                title: profile.title,
                description: profile.description,
                ssh_user: profile.ssh_user
            };

            $.ajax({
                url: profile.url,
                type: 'PATCH',
                data: JSON.stringify(_profile),
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
        save: function (record) {
            var deferred = Q.defer();

            $.ajax({
                url:  settings.api.cloud.profiles,
                type: 'POST',
                data: {
                    title: record.profile_title.value,
                    description: record.profile_description.value,
                    cloud_provider: record.cloud_provider,
                    image_id: record.image_id.value,
                    default_instance_size: record.default_instance_size.value,
                    ssh_user: record.ssh_user.value
                },
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                },
                error: function (request, status, error) {
                    deferred.reject(JSON.parse(request.responseText));
                }
            });

            return deferred.promise;
        },
        delete: function (profile) {
            var deferred = Q.defer();

            $.ajax({
                url: profile.url,
                type: 'DELETE',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
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