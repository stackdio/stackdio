define(['q', 'model/models'], function (Q, models) {
    var api = {};

    api.search = function (terms) {
        var deferred = Q.defer();
        var self = this;

        $.ajax({
            url: '/api/search/?q=' + terms,
            type: 'GET',
            headers: {
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (response) {
                deferred.resolve(response.results);
            }
        });

        return deferred.promise;
    };

    return api;
});