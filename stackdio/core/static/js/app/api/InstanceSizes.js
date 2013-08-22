define(["lib/q", "app/stores", "app/models"], function (Q, stores, models) {
    return {
        load : function () {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/instance_sizes/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var size;

                    deferred.resolve();

                    // Clear the store and the grid
                    stores.InstanceSizes.removeAll();


                    for (i in items) {
                        size = new models.InstanceSize().create(items[i]);
                        stores.InstanceSizes.push(size);
                    }

                    // Resolve the promise and pass back the loaded items
                    deferred.resolve(stores.InstanceSizes());
                }
            });

            return deferred.promise
        }
    }
});