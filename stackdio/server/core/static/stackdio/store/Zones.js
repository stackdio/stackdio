define(['store/store', 'api/Zones'], function (store, API) {
    var Zones = function () {
        this.proxy = API;
    }

    Zones.prototype = new store();
    Zones.prototype.constructor = Zones;

    return new Zones();
});
