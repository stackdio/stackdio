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
        
        // var deferred = Q.defer();
        // var self = this;

        // $.ajax({
        //     url: '/api/stacks/',
        //     type: 'GET',
        //     headers: {
        //         "X-CSRFToken": stackdio.settings.csrftoken,
        //         "Accept": "application/json"
        //     },
        //     success: function (response) {
        //         var stacks = response.results;
        //         var historyPromises = [];

        //         stores.Stacks.removeAll();

        //     }
        // });

        // return deferred.promise;
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
            }
        });

        return deferred.promise;
    };

    api.update = function (stack) {
        var deferred = Q.defer();

        stack = JSON.stringify(stack);

        $.ajax({
            url: stack.url,
            type: 'PUT',
            data: stack,
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (newStack) {
                api.getHistory(newStack).then(function (stackWithHistory) {
                    stores.Stacks.push(new models.Stack().create(stackWithHistory));
                    deferred.resolve(stackWithHistory);
                });
            }
        });

        return deferred.promise;
    };


    api.save = function (stack) {
        var deferred = Q.defer();

        stack = JSON.stringify(stack);

        $.ajax({
            url: '/api/stacks/',
            type: 'POST',
            data: stack,
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (newStack) {
                api.getHistory(newStack).then(function (stackWithHistory) {
                    stores.Stacks.push(new models.Stack().create(stackWithHistory));
                    deferred.resolve(stackWithHistory);
                });
            }
        });

        return deferred.promise;
    };

    api.getHosts = function (stack) {
        var deferred = Q.defer();

        $.ajax({
            url: '/api/stacks/' + stack.id + '/hosts/',
            type: 'GET',
            dataType: 'json',
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": stackdio.settings.csrftoken,
                "Accept": "application/json"
            },
            success: function (response) {
                var hosts = response.results;
                
                // stores.Stacks.push(stack);
                // deferred.resolve();
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
            }
        });

        return deferred.promise;
    };

    return api;
});