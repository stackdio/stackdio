define(["q", "store/stores", "model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/stacks/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var stack;

                    // Clear the store and the grid
                    stores.Stacks.removeAll();

                    for (i in items) {
                        stack = new models.Stack().create(items[i]);

                        // Inject the record into the store
                        stores.Stacks.push(stack);
                    }

                    console.log('stacks', stores.Stacks());

                    // Resolve the promise and pass back the loaded stacks
                    deferred.resolve(stores.Stacks());

                }
            });

            return deferred.promise;
        },
        save: function (stack) {
            var deferred = Q.defer();

            stack = JSON.stringify(stack);

            $.ajax({
                url: '/api/stacks/',
                type: 'POST',
                data: stack,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (stack) {
                    stores.Stacks.push(stack);
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        getHosts: function (stack) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/stacks/' + stack.id + '/hosts/',
                type: 'GET',
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var hosts = response.results;
                    
                    // stores.Stacks.push(stack);
                    // deferred.resolve();
                }
            });

            return deferred.promise;
        },
        delete: function (record) {

        }
    }
});