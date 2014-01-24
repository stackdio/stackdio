define(["q", "store/stores", "model/models"], function (Q, stores, models) {
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
                var matches = response.results;

                // stores.Stacks.removeAll();

                // stacks.forEach(function (stack) {
                //     api.getHistory(stack).then(function (stackWithHistory) {
                //         stores.Stacks.push(new models.Stack().create(stackWithHistory));
                //     }).done();
                // });

                deferred.resolve(matches);
            }
        });

        return deferred.promise;
    };


    return api;
});