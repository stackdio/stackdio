$(document).ready(function () {
    stackdio.api.Roles = (function () {
        var self = this;

        return {
            load : function () {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/roles/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var role;

                        // Clear the store and the grid
                        stackdio.stores.Roles.removeAll();

                        for (i in items) {
                            role = new stackdio.models.Role().create(items[i]);

                            // Inject the record into the store
                            stackdio.stores.Roles.push(role);
                        }

                        console.log('roles', stackdio.stores.Roles());

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.Roles());
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