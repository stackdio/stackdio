$(document).ready(function () {
    stackdio.api.Accounts = (function () {
        var self = this;

        return {
            load : function () {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/providers/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var account;

                        // Clear the store and the grid
                        stackdio.stores.Accounts.removeAll();

                        for (i in items) {
                            account = new stackdio.models.Account().create(items[i]);

                            // Inject the record into the store
                            stackdio.stores.Accounts.push(account);
                        }

                        console.log('accounts', stackdio.stores.Accounts());

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.Accounts());
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