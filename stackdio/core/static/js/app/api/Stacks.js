$(document).ready(function () {
    stackdio.api.Stacks = (function () {
        var self = this;

        return {
            load : function (callback) {
                var deferred = Q.defer();
                var stack;

                $.ajax({
                    url: '/api/stacks/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var stack;


                        // Clear the store and the grid
                        stackdio.stores.Stacks.removeAll();

                        for (i in items) {
                            stack = new stackdio.models.Stack().create(items[i]);

                            // Inject the record into the store
                            stackdio.stores.Stacks.push(stack);
                        }

                        // Resolve the promise and pass back the loaded stacks
                        deferred.resolve(stackdio.stores.Stacks());

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