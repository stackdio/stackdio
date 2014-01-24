define(["q", "store/stores", "model/models"], function (Q, stores, models) {
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
                    var formulae = data.results;

                    // Clear the stores
                    stores.Formulae.removeAll();
                    stores.FormulaComponents.removeAll();

                    for (var i in formulae) {
                        var formula = new models.Formula().create(formulae[i]);

                        // Inject the record into the store
                        stores.Formulae.push(formula);

                        for (var j in formula.components) {
                            var component = new models.FormulaComponent().create(formula.components[j]);
                            stores.FormulaComponents.push(component);
                        }
                    }

                    // console.log('formulae', stores.Formulae());
                    // console.log('components', stores.FormulaComponents());

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
                url: '/api/formulas/' + formula.id,
                type: 'PUT',
                data: JSON.stringify({public: !formula.public}),
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    self.load();
                    deferred.resolve();
                }
            });

            return deferred.promise;
        }
    }
});