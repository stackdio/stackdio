define(['store/store', 'api/InstanceSizes'], function (store, API) {
    var InstanceSizes = function () {
        this.proxy = API;
    }

    InstanceSizes.prototype = new store();
    InstanceSizes.prototype.constructor = InstanceSizes;

    return new InstanceSizes();
});
