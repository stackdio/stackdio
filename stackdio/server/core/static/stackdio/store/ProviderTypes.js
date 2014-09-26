define(['store/store', 'api/ProviderTypes'], function (store, API) {
    var ProviderTypes = function () {
        this.proxy = API;
    }

    ProviderTypes.prototype = new store();
    ProviderTypes.prototype.constructor = ProviderTypes;

    return new ProviderTypes();

});
