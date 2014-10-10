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

define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    var self = this;

    return {
        load: function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.formulas.formulas,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var formulas = response.results.map(function (formula) {
                        return new models.Formula().create(formula);
                    });
                    deferred.resolve(formulas);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        load_global: function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.admin.global_orchestration_formulas,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var formulas = response.results.map(function (formula) {
                        return new models.Formula().create(formula);
                    });
                    deferred.resolve(formulas);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        import: function (uri, git_username, git_password) {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.formulas.formulas,
                type: 'POST',
                data: JSON.stringify({
                    uri: uri,
                    git_username: git_username,
                    git_password: git_password
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': stackdio.settings.csrftoken,
                    'Accept': 'application/json'
                },
                success: function (data, status, response) {
                    deferred.resolve(new models.Formula().create(data));
                },
                error: function (request, status, error) {
                    var response = '';

                    try {
                        response = JSON.parse(request.responseText).detail;
                    } catch (ex) {
                        response = request.responseText.substr(0,100);
                    }
                    deferred.reject(response);
                }
            });

            return deferred.promise;
        },
        import_global: function (uri, git_username, git_password) {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.admin.global_orchestration_formulas,
                type: 'POST',
                data: JSON.stringify({
                    uri: uri,
                    git_username: git_username,
                    git_password: git_password
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': stackdio.settings.csrftoken,
                    'Accept': 'application/json'
                },
                success: function (data, status, response) {
                    deferred.resolve(new models.Formula().create(data));
                },
                error: function (request, status, error) {
                    var response = '';

                    try {
                        response = JSON.parse(request.responseText).detail;
                    } catch (ex) {
                        response = request.responseText.substr(0,100);
                    }
                    deferred.reject(response);
                }
            });

            return deferred.promise;
        },
        delete: function (formula) {
            var deferred = Q.defer();

            $.ajax({
                url: formula.url,
                type: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': stackdio.settings.csrftoken,
                    'Accept': 'application/json'
                },
                success: function (data, status, response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    deferred.reject(JSON.parse(request.responseText).detail);
                }
            });

            return deferred.promise;
        },
        getFormula: function (formulaId) {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.formulas.formulas + formulaId + '/',
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    deferred.resolve(new models.Formula().create(response));
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        getProperties: function (formula) {
            var deferred = Q.defer();
            var self = this;

            $.ajax({
                url: formula.properties,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (data, status, response) {
                    deferred.resolve(data.properties);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        update: function (formula) {
            var deferred = Q.defer();
            var self = this;

            $.ajax({
                url: formula.url,
                type: 'PUT',
                data: JSON.stringify({public: !formula.public}),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': stackdio.settings.csrftoken,
                    'Accept': 'application/json'
                },
                success: function (data, status, response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    deferred.reject(JSON.parse(request.responseText).detail);
                }
            });

            return deferred.promise;
        },
        updateFromRepo: function (formula, git_password) {
            var deferred = Q.defer();

            $.ajax({
                url: formula.action,
                type: 'POST',
                data: JSON.stringify({
                    action: 'update',
                    git_password: git_password
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': stackdio.settings.csrftoken,
                    'Accept': 'application/json'
                },
                success: function (data, status, response) {
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