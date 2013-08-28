define(["lib/q", "app/stores", "app/models"], function (Q, stores, models) {
    return {
        load : function (stack) {
            var deferred = Q.defer();

            $.ajax({
                url: stack.hosts,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var stackHost;

                    // Clear the store and the grid
                    stores.StackHosts.removeAll();

                    for (i in items) {
                        stackHost = new models.StackHost().create(items[i]);

                        // Inject the record into the store
                        stores.StackHosts.push(stackHost);
                    }

                    console.log('stack hosts', stores.StackHosts());

                    // Resolve the promise and pass back the loaded items
                    deferred.resolve(stores.StackHosts());
                }
            });

            return deferred.promise;
        },
        save: function (record, stack) {
            var deferred = Q.defer();

            $.ajax({
                url: stack.hosts,
                type: 'PUT',
                data: record,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                }
            });

            return deferred.promise;
        },
        delete: function (record, stack) {
            var deferred = Q.defer();

            $.ajax({
                url: stack.hosts,
                type: 'DELETE',
                data: {
                    id: record.id
                },
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response);
                }
            });

            return deferred.promise;
        }
    }
});