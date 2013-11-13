define(["q", "store/stores", "model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/snapshots/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var snapshot;

                    // Clear the store and the grid
                    stores.Snapshots.removeAll();

                    for (i in items) {
                        snapshot = new models.Snapshot().create(items[i]);

                        // Inject the name of the account used to create the snapshot
                        snapshot.account = _.find(stores.Accounts(), function (account) {
                            return account.id === snapshot.cloud_provider;
                        });

                        // Inject the record into the store
                        stores.Snapshots.push(snapshot);
                    }

                    console.log('snapshots', stores.Snapshots());

                    // Resolve the promise and pass back the loaded items
                    deferred.resolve(stores.Snapshots());
                }
            });

            return deferred.promise;
        },
        save: function (record) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/snapshots/',
                type: 'POST',
                data: {
                    title: record.snapshot_title.value,
                    description: record.snapshot_description.value,
                    cloud_provider: record.account.id,
                    size_in_gb: record.snapshot_size.value,
                    snapshot_id: record.snapshot_id.value
                },
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    // Create new snapshot
                    var snapshot = new models.Snapshot().create(response);

                    // Inject account name
                    snapshot.account = _.find(stores.Accounts(), function (account) {
                        return account.id === response.cloud_provider;
                    });

                    // Add to observable collection
                    stores.Snapshots.push(snapshot);

                    deferred.resolve(snapshot);
                }
            });

            return deferred.promise;
        },
        delete: function (snapshot) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/snapshots/' + snapshot.id,
                type: 'DELETE',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    // Clear the store and the grid
                    stores.Snapshots.remove(snapshot);

                    // Resolve the promise and pass back the deleted item in case its
                    // info is needed for a UI message
                    deferred.resolve(snapshot);
                }
            });

            return deferred.promise;
        },
        options: function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/snapshots/',
                type: 'OPTIONS',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, textStatus, qwerty) {
                    deferred.resolve({verbs: qwerty.getResponseHeader('Allow').split(',') });
                }
            });
            
            return deferred.promise;
        }
    }
});