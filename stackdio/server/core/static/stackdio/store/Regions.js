define(['store/store', 'api/Regions'], function (store, API) {
    var Regions = function () {
        this.proxy = API;
    }

    Regions.prototype = new store();
    Regions.prototype.constructor = Regions;

    return new Regions();
});
