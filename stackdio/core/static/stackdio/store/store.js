define(['q', 'knockout'], function (Q, ko) {

    var Store = function () {
        this.collection = ko.observableArray();
        this.proxy = null;
        this._dirty = false;
    };

    Store.prototype.populate = function (force) {
        var deferred = Q.defer();
        var self = this;

        if (!self._dirty && self.collection().length && !force) {  // Already populated and not dirty
            deferred.resolve();
        } else if (!self._dirty || force) {              // Not dirty, but client forces population
            self.proxy.load().then(function (models) {
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

    Store.prototype.isDirty = function () {
        return this._dirty;
    };

    Store.prototype.sync = function () {
        var self = this;

        self.collection.forEach(function (type) {
            if (type.hasOwnProperty("_local") && type._local) {
                self.proxy.save(type).then(function () {
                    type._local = false;
                }).fail(function (err) {
                    console.error(err);
                }).done();
            }
        });
    };

    Store.prototype.add = function (type) {
        this.collection.push(type);
    };

    Store.prototype.empty = function () {
        this.collection.removeAll();
    };

    Store.prototype.remove = function (item) {
        var filtered = this.collection().filter(function (type) {
            return JSON.stringify(type) !== JSON.stringify(item);
        });

        this.collection(filtered);
    };

    Store.prototype.removeById = function (id) {
        var filtered = this.collection().filter(function (type) {
            return type.id !== id;
        });

        this.collection(filtered);
    };

    return Store;

});
