define(["lib/q", "app/stores", "app/models"], function (Q, stores, models) {
        return {
            load : function () {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/roles/',
                    type: 'GET',
                    headers: {
                        "X-CSRFToken": stackdio.csrftoken,
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var role;

                        // Clear the store and the grid
                        stores.Roles.removeAll();

                        for (i in items) {
                            role = new models.Role().create(items[i]);

                            // Inject the record into the store
                            stores.Roles.push(role);
                        }

                        console.log('roles', stores.Roles());

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stores.Roles());
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