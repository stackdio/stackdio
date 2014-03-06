define(['q', 'settings', 'model/models'], function (Q, settings, models) {
    var self = this;

    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.formulas.formulas,
                type: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function (response) {
                    var formulas = response.results.map(function (formula) {
                        return new models.Formula().create(formula);
                    });
                    deferred.resolve(formulas);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        },
        import: function (uri) {
            var deferred = Q.defer();

            $.ajax({
                url: settings.api.formulas.formulas,
                type: 'POST',
                data: JSON.stringify({uri: uri}),
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    deferred.resolve(new models.Formula().create(data));
                }
            });

            return deferred.promise;
        },
        delete: function (formula) {
            var deferred = Q.defer();

            $.ajax({
                url: formula.url,
                type: 'DELETE',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        getProperties: function (formula) {
            var deferred = Q.defer();
            var self = this;

            $.ajax({
                url: formula.properties,
                type: 'GET',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    deferred.resolve(data.properties);
                }
            });

            return deferred.promise;
        },
        update: function (formula) {
            var deferred = Q.defer();
            var self = this;

            $.ajax({
                url: formula.url,
                type: 'PUT',
                data: JSON.stringify({public: !formula.public}),
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    deferred.resolve();
                }
            });

            return deferred.promise;
        }
    }
});