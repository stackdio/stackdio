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
                var deferred = Q.defer();
                var files, formData = new FormData(), xhr = new XMLHttpRequest();

                // Append private key file to the FormData() object
                formData.append('private_key_file', record.private_key_file.files[0]);

                // Add the provider type that the user chose from the account split button
                formData.append('provider_type', record.providerType.id);

                // Append all other required fields to the form data
                for (r in record) {
                    rec = record[r];
                    formData.append(r, rec.value);
                }

                // Open the connection to the provider URI and set authorization header
                xhr.open('POST', '/api/providers1/');
                xhr.setRequestHeader('X-CSRFToken', stackdio.csrftoken);
                xhr.setRequestHeader('Accept', 'application/json');

                // Define any actions to take once the upload is complete
                xhr.onloadend = function (evt) {
                    var item;

                    // Check if the upload succeeded
                    if (evt.target.status === 200 || evt.target.status === 201 || evt.target.status === 302) {
                        // Parse the response to get the created item
                        item = JSON.parse(evt.target.response);

                        // Add it to the Accounts store
                        stackdio.stores.Accounts.push(item);

                        // Resolve the promise
                        deferred.resolve(item);
                    } else {
                        var html=[];

                        try {
                            var response = JSON.parse(evt.target.response);


                            for (key in response) {
                                failure = response[key];
                                html.push('<p>' + key + ': ' + failure + '</p>');
                            }
                            deferred.reject(new Error(html));
                        } catch (e) {
                            deferred.reject('error');
                        }
                    }
                };

                // Start the upload process
                xhr.send(formData);

                return deferred.promise;
            },
            delete: function (account) {
                var deferred = Q.defer();

                $.ajax({
                    url: '/api/providers/' + account.id,
                    type: 'DELETE',
                    headers: {
                        "X-CSRFToken": stackdio.csrftoken,
                        "Accept": "application/json"
                    },
                    success: function (response) {
                        stackdio.stores.Accounts.remove(account);
                        deferred.resolve(account);
                    }
                });
                
                return deferred.promise;
            }
        }
    })();
});