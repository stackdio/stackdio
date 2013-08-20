$(document).ready(function () {
    stackdio.api.Profiles = (function () {
        var self = this;

        return {
            load : function () {
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
                            });

                            // Inject the record into the store
                            stackdio.stores.Profiles.push(profile);
                        }

                        console.log('profiles', stackdio.stores.Profiles());

                        // Resolve the promise and pass back the loaded items
                        deferred.resolve(stackdio.stores.Profiles());

                    }
                });

                return deferred.promise;
            },
            save: function (record) {
                $.ajax({
                    url: '/api/profiles/',
                    type: 'POST',
                    data: {
                        title: record.profile_title.value,
                        description: record.profile_description.value,
                        cloud_provider: self.selectedAccount.id,
                        image_id: record.image_id.value,
                        default_instance_size: record.default_instance_size.value,
                        ssh_user: record.ssh_user.value
                    },
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        var i, item = response;

                        if (item.hasOwnProperty('id')) {
                            self.profiles.push(item);
                            $( "#profile-form-container" ).dialog("close");
                        }
                    }
                });
            },
            delete: function (profile) {
                console.log(profile);
                return;

                $.ajax({
                    url: '/api/profiles/' + profile.id,
                    type: 'DELETE',
                    headers: {
                        "Authorization": "Basic " + Base64.encode('testuser:password'),
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        self.profiles.remove(profile);
                    }
                });
            }
        }
    })();
});