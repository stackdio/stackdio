define(["q", "store/stores", "model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/blueprints/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var blueprints = response.results;

                    // Clear the store and the grid
                    stores.Blueprints.removeAll();

                    for (var b in blueprints) {
                        var blueprint = new models.Blueprint().create(blueprints[b]);

                        // Inject the record into the store
                        stores.Blueprints.push(stack);
                    }

                    console.log('blueprints', stores.Blueprints());

                    // Resolve the promise and pass back the loaded blueprints
                    deferred.resolve(stores.Blueprints());

                }
            });

            return deferred.promise;
        },
        save: function (blueprint) {
            var deferred = Q.defer();
            var blueprint = JSON.stringify(blueprint);

            $.ajax({
                url: '/api/blueprints/',
                type: 'POST',
                data: blueprint,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    stores.Blueprints.push(response);
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        delete: function (record) {

        }
    }
});