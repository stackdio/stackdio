define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    var self = this;

    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.cloud.providers,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var accounts = response.results.map(function (account) {
                        return new models.Account().create(account);
                    });
                    deferred.resolve(accounts);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        save: function (account) {
            var deferred = Q.defer();
            var files, formData = new FormData(), xhr = new XMLHttpRequest();

            // Append required fields to the form data
            for (var key in account) {
                formData.append(key, account[key]);
            }

            // Open the connection to the provider URI and set authorization header
            xhr.open('POST', '/api/providers/');
            xhr.setRequestHeader('X-CSRFToken', stackdio.settings.csrftoken);
            xhr.setRequestHeader('Accept', 'application/json');

            // Define any actions to take once the upload is complete
            xhr.onloadend = function (evt) {
                var item;

                // Check if the upload succeeded
                if (evt.target.status === 200 || evt.target.status === 201 || evt.target.status === 302) {
                    // Parse the response to get the created item
                    item = JSON.parse(evt.target.response);

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
        update: function (account) {
            var deferred = Q.defer();
            var patchAccount = {
                title: account.title,
                description: account.description,
                default_availability_zone: account.default_availability_zone
            };

            $.ajax({
                url: account.url,
                type: 'PATCH',
                data: JSON.stringify(patchAccount),
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        delete: function (account) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/providers/' + account.id,
                type: 'DELETE',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });
            
            return deferred.promise;
        }
    }
});