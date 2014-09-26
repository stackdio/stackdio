define(['store/store', 'api/Blueprints'], function (store, API) {
    var Blueprints = function () {
        this.proxy = API;
    }

    Blueprints.prototype = new store();
    Blueprints.prototype.constructor = Blueprints;

    return new Blueprints();
});
