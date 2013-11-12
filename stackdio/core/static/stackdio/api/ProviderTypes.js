define(["q", "store/stores", "model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/provider_types/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response;
                    var type;

                    // Clear the store and the grid
                    stores.ProviderTypes.removeAll();

                    for (i in items) {
                        type = new models.ProviderType().create(items[i]);

                        // Inject the record into the store
                        stores.ProviderTypes.push(type);
                    }

                    console.log('types', stores.ProviderTypes);

                    // Resolve the promise and pass back the loaded items
                    deferred.resolve(stores.ProviderTypes());
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