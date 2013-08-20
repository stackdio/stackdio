$(document).ready(function () {
    stackdio.api.ProviderTypes = (function () {
        var self = this;

        return {
            load : function () {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/provider_types/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var type;

                        // Clear the store and the grid
                        stackdio.stores.ProviderTypes.removeAll();

                        for (i in items) {
                            type = new stackdio.models.ProviderType().create(items[i]);

                            // Inject the record into the store
                            stackdio.stores.ProviderTypes.push(type);
                        }

                        console.log('types', stackdio.stores.ProviderTypes());

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.ProviderTypes());
                    }
                });

                return deferred.promise;
            },
            save: function (record) {

            },
            delete: function (record) {

            }
        }
    })();
});