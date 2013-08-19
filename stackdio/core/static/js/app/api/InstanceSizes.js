$(document).ready(function () {
    stackdio.api.InstanceSizes = (function () {

        return {
            load : function () {
                var self = this;
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/instance_sizes/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var size;

                        deferred.resolve();

                        // Clear the store and the grid
                        stackdio.stores.InstanceSizes.removeAll();


                        for (i in items) {
                            size = new stackdio.models.InstanceSize().create(items[i]);
                            stackdio.stores.InstanceSizes.push(size);
                        }

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.InstanceSizes());
                    }
                });

                return deferred.promise
            }
        }
    })();
});