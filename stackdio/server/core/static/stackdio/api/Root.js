define(['q', 'settings'], function (Q, settings) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api',
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    settings.api = response;
                    deferred.resolve(response);
                }
            });

            return deferred.promise;
        },
        save: function (record) {

        },
        delete: function (record) {

        }
    }
});