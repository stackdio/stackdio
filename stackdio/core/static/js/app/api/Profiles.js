$(document).ready(function () {
    stackdio.api.Profiles = (function () {
        var self = this;

        return {
            load : function (callback) {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/profiles/',
                    type: 'GET',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item, items = response.results;
                        var profile;

                        // Clear the store and the grid
                        stackdio.stores.Stacks.removeAll();

                        for (i in items) {
                            profile = new stackdio.models.Profile().create(items[i]);

                            // Inject the name of the provider account used to create the snapshot
                            profile.account = _.find(stackdio.stores.Accounts(), function (account) {
                                return account.id === profile.cloud_provider;
                            }).title;

                            // Inject the record into the store
                            stackdio.stores.Profiles.push(profile);
                        }

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.Profiles());

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