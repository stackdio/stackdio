define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/users/' + stackdio_user.id,
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    console.log('user', response);
                    deferred.resolve();

                }
            });

            return deferred.promise;
        },
        save: function (user) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/users/' + user.id,
                type: 'POST',
                data: user,
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