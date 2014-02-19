define(['store/store', 'api/Snapshots'], function (store, API) {
    var Snapshots = function () {
        this.proxy = API;
    }

    Snapshots.prototype = new store();
    Snapshots.prototype.constructor = Snapshots;

    return new Snapshots();
});
