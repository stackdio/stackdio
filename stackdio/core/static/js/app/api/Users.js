define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/settings/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve(response.public_key);
                }
            });

            return deferred.promise;
        },
        saveKey: function (public_key) {
            var deferred = Q.defer();

            var data = JSON.stringify({'public_key': public_key});

            $.ajax({
                url: '/api/settings/',
                type: 'PUT',
                data: data,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        savePassword: function (oldpw, newpw, confirmpw) {
            var deferred = Q.defer();

            var data = JSON.stringify({
                'current_password': oldpw,
                'new_password': newpw,
                'confirm_password': confirmpw
            });

            $.ajax({
                url: '/api/settings/change_password/',
                type: 'PUT',
                data: data,
                dataType: 'json',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    deferred.resolve();
                },
                error: function (request, status, error) {
                    var response;

                    try {
                        response = JSON.parse(request.responseText);
                        deferred.resolve(response.detail.errors[0]);
                    }
                    catch (e) {
                        deferred.resolve('Request failed for unknown reasons.');
                    }
                }
            });

            return deferred.promise;
        }
    }
});