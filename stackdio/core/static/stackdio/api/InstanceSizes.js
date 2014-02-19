define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.cloud.instance_sizes,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var sizes = response.results.map(function (size) {
                        return new models.InstanceSize().create(size);
                    });
                    deferred.resolve(sizes);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        }
    }
});