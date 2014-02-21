define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    var api = {};

    api.load = function () {
        var deferred = Q.defer();

        $.ajax({
            url: settings.api.stacks.stacks,
            type: 'GET',
            headers: {
                'Accept': 'application/json'
            },
            success: function (response) {
                var historyPromises = [],
                    stacks = [];

                response.results.forEach(function (stack) {
                    historyPromises[historyPromises.length] = api.getHistory(stack).then(function (stackWithHistory) {
                        stacks[stacks.length] = new models.Stack().create(stackWithHistory);
                    });
                });

                Q.all(historyPromises).then(function () {
                    deferred.resolve(stacks);
                }).done();
            },
            error: function (request, status, error) {
                deferred.reject(new Error(error));
            }
        });

        return deferred.promise;
    };

    api.getHistory = function (stack) {
        var deferred = Q.defer();

        $.ajax({
            url: stack.history,
            type: 'GET',
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (response) {
                var history = response.results;
                stack.fullHistory = history;
                deferred.resolve(stack);
            },
            error: function (request, status, error) {
                deferred.reject(new Error(error));
            }
        });

        return deferred.promise;
    };

    api.update = function (stack) {
        var deferred = Q.defer();

        $.ajax({
            url: stack.url,
            type: 'PUT',
            data: JSON.stringify(stack),
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (newStack) {
                api.getHistory(newStack).then(function (stackWithHistory) {
                    deferred.resolve(stackWithHistory);
                });
            },
            error: function (request, status, error) {
                deferred.reject(new Error(error));
            }
        });

        return deferred.promise;
    };


    api.save = function (stack) {
        var deferred = Q.defer();

        $.ajax({
            url: settings.api.stacks.stacks,
            type: 'POST',
            data: JSON.stringify(stack),
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (newStack) {
                api.getHistory(newStack).then(function (stackWithHistory) {
                    deferred.resolve(stackWithHistory);
                });
            },
            error: function (request, status, error) {
                deferred.reject(new Error(error));
            }
        });

        return deferred.promise;
    };

    api.getHosts = function (stack) {
        var deferred = Q.defer();

        $.ajax({
            url: stack.hosts,
            type: 'GET',
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (response) {
                var hosts = response.results;                
                deferred.resolve(hosts);
            },
            error: function (request, status, error) {
                deferred.reject(new Error(error));
            }
        });

        return deferred.promise;
    };

    api.getProperties = function (stack) {
        var deferred = Q.defer();

        $.ajax({
            url: stack.properties,
            type: 'GET',
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (properties) {
                deferred.resolve(properties);
            },
            error: function (request, status, error) {
                deferred.reject(new Error(error));
            }
        });

        return deferred.promise;
    };

    return api;
});