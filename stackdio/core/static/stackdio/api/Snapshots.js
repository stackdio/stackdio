define(['q', 'store/stores', 'model/models', 'settings'], function (Q, stores, models, settings) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.stacks.snapshots,
                type: 'GET',
                headers: {
                    "Accept": "application/json"
                },
                success: function (response) {
                    var snapshots = response.results.map(function (s) {
                        var snapshot = new models.Snapshot().create(s);

                        // Inject the name of the account used to create the snapshot
                        // snapshot.account = _.find(stores.Accounts(), function (account) {
                        //     return account.id === snapshot.cloud_provider;
                        // });

                        return snapshot;
                    });

                    // Resolve the promise and pass back the loaded items
                    deferred.resolve(snapshots);
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
                    filesystem_type: record.filesystem_type.value,
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