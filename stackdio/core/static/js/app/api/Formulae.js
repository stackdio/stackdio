define(["lib/q", "app/store/stores", "app/model/models"], function (Q, stores, models) {
    var self = this;

    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/formulas/',
                type: 'GET',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    var i, item, items = data.results;
                    var formula;

                    // Clear the store and the grid
                    stores.Formulae.removeAll();

                    for (i in items) {
                        formula = new models.Formula().create(items[i]);

                        // Inject the record into the store
                        stores.Formulae.push(formula);
                    }

                    console.log('formulae', stores.Formulae());

                    // Resolve the promise
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        import: function (uri) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/formulas/',
                type: 'POST',
                data: JSON.stringify({uri: uri}),
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    var formula = new models.Formula().create(data);
                    stores.Formulae.push(formula);

                    // Resolve the promise
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        delete: function (formula) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/formulas/' + formula.id,
                type: 'DELETE',
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    stores.Formulae.remove(formula);

                    // Resolve the promise
                    deferred.resolve();
                }
            });

            return deferred.promise;
        }
    }
});