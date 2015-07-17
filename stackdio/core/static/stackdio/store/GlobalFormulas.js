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
