define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.cloud.zones,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var zones = response.results.map(function (zone) {
                        return new models.Zone().create(zone);
                    });
                    deferred.resolve(zones);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        }
    }
});