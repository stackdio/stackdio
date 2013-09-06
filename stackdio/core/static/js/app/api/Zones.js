define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var self = this;
            var deferred = Q.defer();

            $.ajax({
                url: '/api/zones/',
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
                    stores.Zones.removeAll();


                    for (i in items) {
                        size = new models.Zone().create(items[i]);
                        stores.Zones.push(size);
                    }

                    // Resolve the promise and pass back the loaded items
                    console.log('Zones', stores.Zones());
                    deferred.resolve(stores.Zones());
                }
            });

            return deferred.promise
        }
    }
});