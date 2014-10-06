define(['q', 'model/models', 'settings'], function (Q, models, settings) {
    return {
        load : function () {
            var deferred = Q.defer();
            
            $.ajax({
                url: settings.api.cloud.provider_types,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var types = response.results.map(function (type) {
                        return new models.ProviderType().create(type);
                    });
                    deferred.resolve(types);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
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