$(document).ready(function () {
    stackdio.api.Snapshots = (function () {
        var self = this;

        return {
            load : function () {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/snapshots/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var snapshot;

                        // Clear the store and the grid
                        stackdio.stores.Snapshots.removeAll();

                        for (i in items) {
                            snapshot = new stackdio.models.Snapshot().create(items[i]);

                            // Inject the name of the account used to create the snapshot
                            snapshot.account = _.find(stackdio.stores.Accounts(), function (account) {
                                return account.id === snapshot.cloud_provider;
                            });

                            // Inject the record into the store
                            stackdio.stores.Snapshots.push(snapshot);
                        }

                        console.log('snapshots', stackdio.stores.Snapshots());

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.Snapshots());
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