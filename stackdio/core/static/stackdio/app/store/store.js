/*!
  * Copyright 2014,  Digital Reasoning
  * 
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  * 
  *     http://www.apache.org/licenses/LICENSE-2.0
  * 
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  * 
*/

define(['../../bower_components/q/q', 'knockout'], function (Q, ko) {

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
        var self = this;

        if (type instanceof Array) {
            type.forEach(function (item) {
                self.collection.push(item);
            });
        } else {
            self.collection.push(type);
        }
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
