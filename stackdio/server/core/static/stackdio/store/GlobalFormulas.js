define(['q', 'store/store', 'api/Formulas'], function (Q, store, API) {
    var GlobalFormulas = function () {
        this.proxy = API;
    }

    GlobalFormulas.prototype = new store();
    GlobalFormulas.prototype.constructor = GlobalFormulas;

    // Override the populate function to use the global load
    GlobalFormulas.prototype.populate = function (force) {
        var deferred = Q.defer();
        var self = this;

        if (!self._dirty && self.collection().length && !force) {  // Already populated and not dirty
            deferred.resolve();
        } else if (!self._dirty || force) {              // Not dirty, but client forces population
            self.proxy.load_global().then(function (models) {
                self.collection(models);
                deferred.resolve();
            }).fail(function (err) {
                console.log('Failed to load from remote proxy. ' + err.toString());
                deferred.reject();
            }).done();
        } else {
            deferred.reject();
        }

        return deferred.promise;
    };

    return new GlobalFormulas();
});
