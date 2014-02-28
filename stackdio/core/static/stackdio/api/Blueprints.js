define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.blueprints,
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
                    deferred.resolve(properties);   // Resolve promise and pass back properties
                }
            });

            return deferred.promise;
        },
        save: function (blueprint) {
            var deferred = Q.defer();
            var blueprint = JSON.stringify(blueprint);

            $.ajax({
                url: settings.api.blueprints,
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
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        }
    }
});