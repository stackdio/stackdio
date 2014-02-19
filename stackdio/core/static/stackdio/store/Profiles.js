define(['store/store', 'api/Profiles'], function (store, API) {
    var Profiles = function () {
        this.proxy = API;
    }

    Profiles.prototype = new store();
    Profiles.prototype.constructor = Profiles;

    return new Profiles();
});
