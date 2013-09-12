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
                    console.log('user', response);
                    stackdio_user.public_key = response.public_key;
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        save: function (public_key) {
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
        }
    }
});